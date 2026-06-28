from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

from .guardrails import GuardrailError, is_protected_relative

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIVE_VAULT_ROOT = Path("/home/hermesadmin/Obsidian")
DEFAULT_SANDBOX_ROOT = REPO_ROOT / "out" / "sandbox-vaults"
DEFAULT_DERIVED_ROOT = REPO_ROOT / "out" / "external-indexing-spike"
INDEXING_WRAPPER_TOOL_ALLOWLIST = ("index_status", "index_vault", "search_notes", "read_note")
REDACTED_LIVE_VAULT = "<LIVE_VAULT>"


@dataclass(frozen=True)
class IndexingWrapperPolicy:
    vault_root: str
    derived_root: str
    ollama_base_url: str
    allowed_tools: tuple[str, ...] = INDEXING_WRAPPER_TOOL_ALLOWLIST
    live_vault_root: str = str(DEFAULT_LIVE_VAULT_ROOT)
    require_sandbox_vault: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedMcpResult:
    tool: str
    payload: Any
    provenance: list[dict[str, Any]]
    redactions: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_existing_or_parent(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.exists():
        return candidate.resolve()
    return candidate.parent.resolve() / candidate.name


def require_not_live_vault_path(path: str | Path, *, live_vault_root: str | Path = DEFAULT_LIVE_VAULT_ROOT) -> Path:
    resolved = _resolve_existing_or_parent(path)
    live = Path(live_vault_root).expanduser().resolve()
    if _is_relative_to(resolved, live):
        raise GuardrailError(f"Indexing wrapper refuses live vault path: {resolved}")
    return resolved


def require_under(path: str | Path, root: str | Path, label: str) -> Path:
    resolved = _resolve_existing_or_parent(path)
    resolved_root = Path(root).expanduser().resolve()
    if not _is_relative_to(resolved, resolved_root):
        raise GuardrailError(f"{label} must live under {resolved_root}: {resolved}")
    return resolved


def normalize_loopback_ollama_base_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "http":
        raise GuardrailError(f"Ollama endpoint must use local http: {url}")
    if parsed.username or parsed.password:
        raise GuardrailError(f"Ollama endpoint must not include credentials: {url}")
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise GuardrailError(f"Ollama endpoint must be localhost/loopback only: {url}")
    port = parsed.port or 11434
    if port != 11434:
        raise GuardrailError(f"Ollama endpoint must use port 11434: {url}")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise GuardrailError(f"Ollama endpoint must be a bare base URL: {url}")
    return f"http://{parsed.hostname}:11434"


def assert_indexing_tool_allowed(tool: str, allowed_tools: tuple[str, ...] = INDEXING_WRAPPER_TOOL_ALLOWLIST) -> str:
    if tool not in allowed_tools:
        raise GuardrailError(f"Indexing MCP tool is not allowlisted: {tool}")
    return tool


def build_indexing_wrapper_policy(
    *,
    vault_root: str | Path,
    derived_root: str | Path,
    ollama_base_url: str = "http://localhost:11434",
    allowed_tools: tuple[str, ...] = INDEXING_WRAPPER_TOOL_ALLOWLIST,
    sandbox_root: str | Path = DEFAULT_SANDBOX_ROOT,
    derived_boundary: str | Path = DEFAULT_DERIVED_ROOT,
    live_vault_root: str | Path = DEFAULT_LIVE_VAULT_ROOT,
    require_sandbox_vault: bool = True,
) -> IndexingWrapperPolicy:
    vault = require_not_live_vault_path(vault_root, live_vault_root=live_vault_root)
    if require_sandbox_vault:
        require_under(vault, sandbox_root, "Indexing wrapper vault root")
        if vault == Path(sandbox_root).expanduser().resolve():
            raise GuardrailError("Indexing wrapper vault root must be a named sandbox vault")
    derived = require_not_live_vault_path(derived_root, live_vault_root=live_vault_root)
    require_under(derived, derived_boundary, "Indexing wrapper derived storage")
    normalized_url = normalize_loopback_ollama_base_url(ollama_base_url)
    for tool in allowed_tools:
        assert_indexing_tool_allowed(tool)
    return IndexingWrapperPolicy(
        vault_root=str(vault),
        derived_root=str(derived),
        ollama_base_url=normalized_url,
        allowed_tools=allowed_tools,
        live_vault_root=str(Path(live_vault_root).expanduser().resolve()),
        require_sandbox_vault=require_sandbox_vault,
    )


def parse_mcp_text_result(message: dict[str, Any]) -> Any:
    if "error" in message:
        return {"error": message["error"]}
    content = message.get("result", {}).get("content")
    if not isinstance(content, list) or not content:
        return message.get("result", message)
    text_items = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
    if not text_items:
        return content
    text = text_items[0]
    if not isinstance(text, str):
        return text
    text = text.lstrip("\ufeff").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def redact_live_vault_paths(value: Any, *, live_vault_root: str | Path = DEFAULT_LIVE_VAULT_ROOT) -> tuple[Any, list[dict[str, str]]]:
    live = str(Path(live_vault_root).expanduser().resolve())
    redactions: list[dict[str, str]] = []

    def visit(obj: Any) -> Any:
        if isinstance(obj, str):
            redacted = obj
            for needle in {
                live,
                live.replace("/", "\\/"),  # Covers JSON-escaped snippets after dumps/loads.
            }:
                if needle in redacted:
                    redacted = redacted.replace(needle, REDACTED_LIVE_VAULT)
            for needle in {quote(live, safe=""), quote(live, safe="/")}:
                redacted = re.sub(re.escape(needle), REDACTED_LIVE_VAULT, redacted, flags=re.IGNORECASE)
            if redacted != obj:
                redactions.append({"kind": "live-vault-path", "replacement": REDACTED_LIVE_VAULT})
            return redacted
        if isinstance(obj, list):
            return [visit(item) for item in obj]
        if isinstance(obj, dict):
            return {str(key): visit(val) for key, val in obj.items()}
        return obj

    return visit(value), redactions


def _decoded_path_forms(raw: str, *, max_rounds: int = 3) -> list[str]:
    forms = [str(raw)]
    current = str(raw)
    for _ in range(max_rounds):
        decoded = unquote(current)
        if decoded == current:
            break
        forms.append(decoded)
        current = decoded
    return forms


def _safe_rel_path(raw: str) -> str:
    clean: str | None = None
    for candidate in _decoded_path_forms(str(raw).replace("\\", "/")):
        normalized = candidate.replace("\\", "/")
        rel = Path(normalized)
        if rel.is_absolute() or ".." in rel.parts:
            raise GuardrailError(f"Result path must be vault-relative: {raw}")
        candidate_clean = rel.as_posix()
        if candidate_clean.startswith("./"):
            candidate_clean = candidate_clean[2:]
        if is_protected_relative(candidate_clean):
            raise GuardrailError(f"Result path points to protected content: {candidate_clean}")
        clean = candidate_clean
    return clean if clean is not None else str(raw)


PATH_FIELD_NAMES = frozenset(
    {"path", "paths", "file", "files", "filepath", "filepaths", "file_path", "file_paths", "note", "note_path", "source", "source_path"}
)


def _validate_payload_paths(value: Any, *, context: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text in PATH_FIELD_NAMES or key_text.endswith("_path") or key_text.endswith("Path"):
                if isinstance(item, str):
                    _safe_rel_path(item)
                elif isinstance(item, list):
                    for entry in item:
                        if not isinstance(entry, str):
                            raise GuardrailError(f"Unexpected non-string path list entry in {context}: {key_text}")
                        _safe_rel_path(entry)
                elif item is not None:
                    raise GuardrailError(f"Unexpected non-string path field in {context}: {key_text}")
            _validate_payload_paths(item, context=f"{context}.{key_text}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_paths(item, context=f"{context}[{index}]")


def _file_hash_or_missing(vault_root: Path, rel_path: str) -> str:
    target = (vault_root / rel_path).resolve()
    root = vault_root.resolve()
    if not _is_relative_to(target, root) or not target.is_file():
        return "missing"
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _normalize_lines(section: dict[str, Any]) -> list[int] | None:
    lines = section.get("lines")
    if isinstance(lines, list) and len(lines) == 2:
        return [int(lines[0]), int(lines[1])]
    line = section.get("line")
    if line is not None:
        n = int(line)
        return [n, n]
    return None


def normalize_indexing_mcp_result(
    *,
    tool: str,
    message: dict[str, Any],
    vault_root: str | Path,
    live_vault_root: str | Path = DEFAULT_LIVE_VAULT_ROOT,
) -> NormalizedMcpResult:
    assert_indexing_tool_allowed(tool)
    vault = require_not_live_vault_path(vault_root, live_vault_root=live_vault_root)
    payload = parse_mcp_text_result(message)
    _validate_payload_paths(payload, context=tool)
    payload, redactions = redact_live_vault_paths(payload, live_vault_root=live_vault_root)
    provenance: list[dict[str, Any]] = []

    if tool == "search_notes" and isinstance(payload, dict):
        for result in payload.get("results", []):
            if not isinstance(result, dict) or "path" not in result:
                continue
            rel = _safe_rel_path(str(result["path"]))
            hash_or_version = _file_hash_or_missing(vault, rel)
            sections = result.get("matched_sections") or []
            if not sections:
                provenance.append({"path": rel, "span": None, "snippet": "", "hash_or_version": hash_or_version})
            for section in sections:
                if not isinstance(section, dict):
                    continue
                provenance.append(
                    {
                        "path": rel,
                        "span": _normalize_lines(section),
                        "snippet": str(section.get("snippet", "")),
                        "hash_or_version": hash_or_version,
                    }
                )
    elif tool == "read_note" and isinstance(payload, dict) and "path" in payload:
        rel = _safe_rel_path(str(payload["path"]))
        provenance.append(
            {
                "path": rel,
                "span": [int(payload.get("start_line", 1)), int(payload.get("end_line", payload.get("start_line", 1)))],
                "snippet": str(payload.get("content", ""))[:500],
                "hash_or_version": _file_hash_or_missing(vault, rel),
            }
        )
    elif tool in {"index_status", "index_vault"}:
        provenance.append({"path": None, "span": None, "snippet": "derived-index-operation", "hash_or_version": "derived"})

    return NormalizedMcpResult(tool=tool, payload=payload, provenance=provenance, redactions=redactions)
