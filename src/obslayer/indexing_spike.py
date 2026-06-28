from __future__ import annotations

import hashlib
import json
import os
import resource
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .guardrails import GuardrailError, is_protected_relative, load_json, write_json
from .mcp_adapter import normalize_mcp_tool_request

REQUIRED_FORBIDDEN_CAPABILITIES = {
    "write-direct",
    "delete-direct",
    "move-direct",
    "patch-direct",
    "execute-live-mutation",
    "secret-read",
}
REQUIRED_PROTECTED_PATHS = {".obsidian", "_Backups", ".trash"}
READONLY_INDEX_TOOL_ALLOWLIST = {"search_notes", "read_note", "index_vault", "index_status"}
SAFE_INDEX_TOOL_TOKENS = ("read", "search", "index", "status", "metadata", "list", "graph")
DANGEROUS_INDEX_TOOL_TOKENS = (
    "write",
    "edit",
    "delete",
    "remove",
    "move",
    "rename",
    "patch",
    "apply",
    "create",
    "append",
    "replace",
    "upload",
    "fetch",
    "sync",
    "git",
    "secret",
    "env",
    "token",
)
LOCAL_OLLAMA_URLS = {"http://localhost:11434", "http://127.0.0.1:11434"}
REPO_ROOT = Path(__file__).resolve().parents[2]
INDEXING_SANDBOX_ROOT = REPO_ROOT / "out" / "sandbox-vaults"
INDEXING_REPORT_ROOT = REPO_ROOT / "out" / "reports" / "indexing-spike"
DEFAULT_LIVE_VAULT_ROOT = Path("/home/hermesadmin/Obsidian")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _refuse_live_vault_path(path: Path) -> None:
    live_root = DEFAULT_LIVE_VAULT_ROOT.expanduser().resolve()
    if live_root.exists() and _is_relative_to(path, live_root):
        raise GuardrailError(f"Indexing spike refuses paths inside live vault: {path}")

def _require_under(path: Path, root: Path, label: str) -> None:
    resolved_root = root.expanduser().resolve()
    if not _is_relative_to(path, resolved_root):
        raise GuardrailError(f"{label} must live under {resolved_root}: {path}")


def _normalize_loopback_ollama_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "http":
        raise GuardrailError(f"Embedding endpoint must use local http Ollama: {url}")
    if parsed.username or parsed.password:
        raise GuardrailError(f"Embedding endpoint must not include credentials: {url}")
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise GuardrailError(f"Embedding endpoint must be localhost/loopback only: {url}")
    port = parsed.port or 11434
    if port != 11434:
        raise GuardrailError(f"Embedding endpoint must use Ollama port 11434: {url}")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise GuardrailError(f"Embedding endpoint must be a bare base URL: {url}")
    return f"http://{parsed.hostname}:11434"


def _safe_embedding_base_urls(policy: dict[str, Any]) -> set[str]:
    configured = policy.get("allowed_base_urls") or sorted(LOCAL_OLLAMA_URLS)
    if not isinstance(configured, list) or not configured:
        raise GuardrailError("Embedding policy must declare localhost allowed_base_urls")
    return {_normalize_loopback_ollama_url(str(url)) for url in configured}


@dataclass(frozen=True)
class IndexingSpikeEvaluation:
    candidate: str
    source_id: str
    sandbox_vault: str
    exposed_tools: list[str]
    fixed_queries: list[str]
    findings: list[dict[str, Any]]
    acceptance: dict[str, bool]
    artifacts: dict[str, str]
    verification: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_indexing_candidate_record(path: str | Path) -> dict[str, Any]:
    record = load_json(path)
    if record.get("kind") != "knowledge-indexer":
        raise GuardrailError(f"Candidate record is not a knowledge indexer: {record.get('kind')}")
    if record.get("direct_write_enabled") is not False:
        raise GuardrailError("Knowledge indexer must set direct_write_enabled=false")
    if record.get("sandbox_required") is not True:
        raise GuardrailError("Knowledge indexer must require sandbox evaluation")

    forbidden = set(record.get("forbidden_capabilities", []))
    missing_forbidden = REQUIRED_FORBIDDEN_CAPABILITIES - forbidden
    if missing_forbidden:
        raise GuardrailError(f"Candidate missing forbidden capabilities: {sorted(missing_forbidden)}")

    tools = record.get("exposed_tools", [])
    if not isinstance(tools, list) or not tools:
        raise GuardrailError("Candidate record must list exposed_tools")
    dangerous_tools = [tool for tool in tools if classify_index_tool(str(tool)) == "refuse"]
    if dangerous_tools:
        raise GuardrailError(f"Candidate exposes dangerous index tools: {dangerous_tools}")

    embedding_policy = record.get("embedding_policy", {})
    if embedding_policy.get("local_only") is not True:
        raise GuardrailError("Candidate embedding policy must set local_only=true")
    if embedding_policy.get("provider") not in {"ollama", "fastembed", "local"}:
        raise GuardrailError("Candidate embedding provider must be local-first")
    if embedding_policy.get("remote_endpoint_requires_explicit_approval") is not True:
        raise GuardrailError("Candidate must require explicit approval for remote embedding endpoints")
    _safe_embedding_base_urls(embedding_policy)

    protected_paths = set(record.get("protected_paths", []))
    missing_protected = REQUIRED_PROTECTED_PATHS - protected_paths
    if missing_protected:
        raise GuardrailError(f"Candidate protected path policy missing: {sorted(missing_protected)}")
    return record


def classify_index_tool(tool_name: str) -> str:
    normalized = tool_name.lower().replace("-", "_")
    if normalized in READONLY_INDEX_TOOL_ALLOWLIST:
        return "allow-readonly-index"
    if any(token in normalized for token in DANGEROUS_INDEX_TOOL_TOKENS):
        return "refuse"
    if any(token in normalized for token in SAFE_INDEX_TOOL_TOKENS):
        return "allow-readonly-index"
    return "manual-review-required"


def normalize_index_tool(tool_name: str) -> dict[str, Any]:
    decision = classify_index_tool(tool_name)
    if decision == "allow-readonly-index":
        return {
            "tool": tool_name,
            "decision": decision,
            "status": "allowed-for-sandbox-readonly-index",
            "executed": False,
            "proposal_required": False,
            "reason": "Tool is limited to read/search/status or derived-index mutation in sandbox.",
        }
    if decision == "refuse":
        base = normalize_mcp_tool_request(tool_name)
        return {**base, "reason": "Write/delete/move/fetch/git-like index tools are blocked."}
    return {
        "tool": tool_name,
        "decision": decision,
        "status": "manual-review-required",
        "executed": False,
        "proposal_required": True,
        "reason": "Unknown index tool requires explicit mapping before Hermes access.",
    }


def _safe_sandbox_vault(path: str | Path) -> Path:
    vault = Path(path).expanduser().resolve()
    if not vault.exists() or not vault.is_dir():
        raise GuardrailError(f"Sandbox vault does not exist or is not a directory: {vault}")
    _refuse_live_vault_path(vault)
    _require_under(vault, INDEXING_SANDBOX_ROOT, "Indexing spike sandbox")
    if vault == INDEXING_SANDBOX_ROOT.resolve():
        raise GuardrailError(f"Indexing spike sandbox must be a named vault below {INDEXING_SANDBOX_ROOT}: {vault}")
    if vault.name in {"sandbox-vaults", "out"} or is_protected_relative(vault.name):
        raise GuardrailError(f"Sandbox vault name is not allowed: {vault.name}")
    return vault


def safe_indexing_report_dir(path: str | Path) -> Path:
    reports = Path(path).expanduser().resolve()
    _refuse_live_vault_path(reports)
    _require_under(reports, INDEXING_REPORT_ROOT, "Indexing spike reports")
    return reports


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_vault_tree(root: str | Path) -> dict[str, Any]:
    vault = Path(root).expanduser().resolve()
    files: list[dict[str, str]] = []
    for path in sorted(p for p in vault.rglob("*") if p.is_file()):
        rel = path.relative_to(vault).as_posix()
        files.append({"path": rel, "sha256": _hash_file(path)})
    tree_digest = hashlib.sha256()
    for item in files:
        tree_digest.update(item["path"].encode("utf-8"))
        tree_digest.update(b"\0")
        tree_digest.update(item["sha256"].encode("ascii"))
        tree_digest.update(b"\0")
    return {"file_count": len(files), "tree_sha256": tree_digest.hexdigest(), "files": files}


def _embedding_env_ok(record: dict[str, Any]) -> bool:
    policy = record.get("embedding_policy", {})
    expected = _safe_embedding_base_urls(policy)
    current = os.environ.get("OLLAMA_BASE_URL")
    if current is None:
        return True
    try:
        normalized = _normalize_loopback_ollama_url(current)
    except GuardrailError:
        return False
    return normalized in expected


def build_indexing_spike_evaluation(
    *,
    candidate_record: str | Path,
    sandbox_vault: str | Path,
    fixed_queries: list[str] | None = None,
    artifact_root: str | Path | None = None,
) -> IndexingSpikeEvaluation:
    started = time.perf_counter()
    record = load_indexing_candidate_record(candidate_record)
    sandbox = _safe_sandbox_vault(sandbox_vault)
    queries = fixed_queries or [
        "Obsidian Operating Layer safety boundary",
        "notes with wikilinks and tags",
        "approval manifest backup apply verify",
    ]

    before = hash_vault_tree(sandbox)
    tools = [str(tool) for tool in record["exposed_tools"]]
    tool_findings = [normalize_index_tool(tool) for tool in tools]
    after = hash_vault_tree(sandbox)

    protected_paths = set(record.get("protected_paths", []))
    provenance_fields = set(record.get("provenance_fields", []))
    wrapper_fields = set(record.get("wrapper_required_provenance_fields", []))
    required_source_fields = {"path", "lines", "snippet"}

    acceptance = {
        "sandbox_only": True,
        "vault_tree_unchanged": before["tree_sha256"] == after["tree_sha256"],
        "no_write_delete_move_tools": all(item["decision"] != "refuse" for item in tool_findings),
        "unknown_tools_reviewed": all(item["decision"] != "manual-review-required" for item in tool_findings),
        "protected_paths_declared": REQUIRED_PROTECTED_PATHS.issubset(protected_paths),
        "provenance_policy_ready": required_source_fields.issubset(provenance_fields)
        and "hash_or_version" in wrapper_fields,
        "local_embedding_policy": record.get("embedding_policy", {}).get("local_only") is True and _embedding_env_ok(record),
        "derived_storage_declared": bool(record.get("derived_storage")),
    }
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    artifacts: dict[str, str] = {}
    if artifact_root is not None:
        root = safe_indexing_report_dir(artifact_root)
        root.mkdir(parents=True, exist_ok=True)
        stem = record["name"].replace("/", "-").replace(" ", "-")
        artifacts = {"json_report": str(root / f"indexing-spike-evaluation-{stem}.json")}

    findings: list[dict[str, Any]] = [
        {
            "kind": "tool-policy",
            "items": tool_findings,
        },
        {
            "kind": "protected-path-policy",
            "required": sorted(REQUIRED_PROTECTED_PATHS),
            "declared": sorted(protected_paths),
            "missing": sorted(REQUIRED_PROTECTED_PATHS - protected_paths),
        },
        {
            "kind": "provenance-policy",
            "candidate_fields": sorted(provenance_fields),
            "wrapper_required_fields": sorted(wrapper_fields),
        },
        {
            "kind": "embedding-policy",
            "provider": record.get("embedding_policy", {}).get("provider"),
            "local_only": record.get("embedding_policy", {}).get("local_only"),
            "ollama_base_url_env": os.environ.get("OLLAMA_BASE_URL", "<unset>"),
            "env_ok": _embedding_env_ok(record),
        },
    ]

    return IndexingSpikeEvaluation(
        candidate=record["name"],
        source_id=record["source"]["id"],
        sandbox_vault=str(sandbox),
        exposed_tools=tools,
        fixed_queries=queries,
        findings=findings,
        acceptance=acceptance,
        artifacts=artifacts,
        verification={
            "status": "passed" if all(acceptance.values()) else "needs-review",
            "sandboxed": True,
            "external_candidate_executed": False,
            "no_write_harness": True,
            "vault_hash_before": {k: v for k, v in before.items() if k != "files"},
            "vault_hash_after": {k: v for k, v in after.items() if k != "files"},
            "benchmark_metrics": {
                "wall_time_ms": elapsed_ms,
                "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "cost_model": "local-wrapper-no-llm-call",
            },
        },
    )


def write_indexing_spike_evaluation(evaluation: IndexingSpikeEvaluation, out: str | Path) -> None:
    write_json(out, {"status": "ok", **evaluation.to_dict()})


def indexing_spike_to_markdown(evaluation: IndexingSpikeEvaluation) -> str:
    lines = [
        f"# Indexing spike evaluation: {evaluation.candidate}",
        "",
        f"- source: `{evaluation.source_id}`",
        f"- sandbox_vault: `{evaluation.sandbox_vault}`",
        f"- verification_status: `{evaluation.verification['status']}`",
        f"- external_candidate_executed: `{evaluation.verification['external_candidate_executed']}`",
        "",
        "## Acceptance",
    ]
    for key, value in evaluation.acceptance.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Exposed tools"])
    for tool in evaluation.exposed_tools:
        lines.append(f"- `{tool}` → `{classify_index_tool(tool)}`")
    lines.extend(["", "## Fixed query set"])
    for query in evaluation.fixed_queries:
        lines.append(f"- {query}")
    lines.extend(
        [
            "",
            "## Verification",
            "```json",
            json.dumps(evaluation.verification, indent=2, sort_keys=True),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"
