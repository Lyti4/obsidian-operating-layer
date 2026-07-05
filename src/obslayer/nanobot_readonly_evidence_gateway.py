"""Read-only HTTP evidence gateway for Nanobot.

The gateway exposes allowlisted project/server evidence directories over
loopback HTTP. It deliberately implements no mutating methods and rejects path
traversal, symlink escapes, hidden files, oversized files, unsafe extensions,
and secret-like filenames.
"""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar
from urllib.parse import unquote, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18791
MAX_FILE_BYTES = 2_000_000

SECRET_NAME_MARKERS = (
    ".env",
    "auth",
    "cookie",
    "credential",
    "id_rsa",
    "private",
    "secret",
    "token",
)

SENSITIVE_PATH_PARTS = {
    "secure",
    "secrets",
    "credentials",
    "credential",
    "private",
    "auth",
    "token",
    "tokens",
    "cookies",
    "cookie",
    "keyring",
    "gnupg",
    "ssh",
    "ssl",
    "codex",
    "openai",
    "browser",
    "chrome",
    "chromium",
    "mozilla",
    "obsidian",
}

SAFE_TEXT_EXTENSIONS = {
    ".css",
    ".csv",
    ".html",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".service",
    ".socket",
    ".svg",
    ".timer",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class EvidenceRoot:
    alias: str
    path: Path

    def resolved(self) -> Path:
        return self.path.resolve(strict=True)


DEFAULT_ROOTS = (
    # Project evidence roots.
    EvidenceRoot("reports", PROJECT_ROOT / "out" / "reports"),
    EvidenceRoot("proposals", PROJECT_ROOT / "out" / "proposals"),
    EvidenceRoot("queue", PROJECT_ROOT / "out" / "queue"),
    EvidenceRoot("spec-kit", PROJECT_ROOT / "docs" / "spec-kit"),
    EvidenceRoot("project-docs", PROJECT_ROOT / "docs"),
    EvidenceRoot("project-policy", PROJECT_ROOT),
    # Broader server-safe read-only roots for Nanobot communicator/reviewer use.
    # These are intentionally selected roots, not raw / or /home exposure.
    EvidenceRoot("server-work", Path.home() / "work"),
    EvidenceRoot("server-user-systemd", Path.home() / ".config" / "systemd" / "user"),
    EvidenceRoot("server-local-bin", Path.home() / ".local" / "bin"),
    EvidenceRoot("hermes-skills", Path.home() / ".hermes" / "skills"),
    EvidenceRoot("hermes-cron", Path.home() / ".hermes" / "cron"),
    EvidenceRoot("nanobot-workspace", Path.home() / ".nanobot-hermes" / "workspace"),
    EvidenceRoot("nanobot-docs", Path.home() / ".nanobot-hermes" / "docs"),
)


class AccessDenied(ValueError):
    """Raised when a requested path is outside the gateway policy."""


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _has_secret_like_name(path: Path) -> bool:
    return any(marker in part.lower() for part in path.parts for marker in SECRET_NAME_MARKERS)


def _has_hidden_part(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts if part not in (".", ".."))


def _has_sensitive_path_part(path: Path) -> bool:
    return any(part.lower().lstrip(".") in SENSITIVE_PATH_PARTS for part in path.parts)


def _is_text_like_no_extension_file(path: Path) -> bool:
    if path.suffix:
        return False
    sample = path.read_bytes()[:4096]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _is_exposed_file(path: Path) -> bool:
    if path.stat().st_size > MAX_FILE_BYTES:
        return False
    return path.suffix.lower() in SAFE_TEXT_EXTENSIONS or _is_text_like_no_extension_file(path)


def _is_exposed_directory_entry(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if _has_hidden_part(rel) or _has_secret_like_name(rel) or _has_sensitive_path_part(rel):
        return False
    if path.is_file() and not _is_exposed_file(path):
        return False
    return True


def allowed_roots(existing_only: bool = True) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for item in DEFAULT_ROOTS:
        if existing_only and not item.path.exists():
            continue
        roots[item.alias] = item.path.resolve(strict=True)
    return roots


PROJECT_POLICY_ALLOWED_RELS = {"AGENTS.md", "README.md", "Makefile"}


def _alias_allows_rel(alias: str, rel: Path) -> bool:
    if alias != "project-policy":
        return True
    if rel.as_posix() == ".":
        return True
    return rel.as_posix() in PROJECT_POLICY_ALLOWED_RELS


def resolve_evidence_path(url_path: str, roots: dict[str, Path] | None = None) -> tuple[str, Path]:
    """Resolve /<alias>/<relative-path> under an allowlisted root.

    Returns (alias, resolved_path). Raises AccessDenied for traversal, secret-like
    names, hidden paths, missing aliases, and symlink escapes.
    """

    roots = allowed_roots() if roots is None else roots
    clean = unquote(url_path.split("?", 1)[0]).lstrip("/")
    if not clean:
        raise AccessDenied("missing evidence alias")
    parts = [p for p in clean.split("/") if p]
    alias = parts[0]
    if alias not in roots:
        raise AccessDenied(f"unknown evidence alias: {alias}")
    rel = Path(*parts[1:]) if len(parts) > 1 else Path(".")
    if rel.is_absolute() or ".." in rel.parts:
        raise AccessDenied("path traversal is not allowed")
    if not _alias_allows_rel(alias, rel):
        raise AccessDenied("path is not exposed for this alias")
    if _has_hidden_part(rel):
        raise AccessDenied("hidden paths are not exposed")
    if _has_secret_like_name(rel):
        raise AccessDenied("secret-like filenames are not exposed")
    if _has_sensitive_path_part(rel):
        raise AccessDenied("sensitive path names are not exposed")
    root = roots[alias]
    candidate = (root / rel).resolve(strict=True)
    if not _is_relative_to(candidate, root):
        raise AccessDenied("symlink escape is not allowed")
    if candidate.is_file() and candidate.stat().st_size > MAX_FILE_BYTES:
        raise AccessDenied(f"file is too large to expose: {candidate.stat().st_size} bytes")
    if candidate.is_file() and not _is_exposed_file(candidate):
        raise AccessDenied(f"file extension/content is not exposed: {candidate.suffix}")
    return alias, candidate


def list_index(roots: dict[str, Path] | None = None) -> bytes:
    roots = allowed_roots() if roots is None else roots
    payload = {
        "status": "ok",
        "mode": "server-safe-read-only",
        "mutating_methods": "disabled",
        "policy": {
            "max_file_bytes": MAX_FILE_BYTES,
            "hidden_paths": "blocked",
            "secret_like_names": "blocked",
            "sensitive_path_parts": "blocked",
            "unsafe_extensions": "blocked",
        },
        "roots": {alias: f"/{alias}/" for alias in sorted(roots)},
        "snapshot": "/snapshot.json",
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def audit_roots(roots: dict[str, Path] | None = None, *, max_entries_per_root: int = 2000) -> bytes:
    """Return a content-free exposure audit for allowlisted roots.

    The audit reports counts and sample relative paths only; it does not read or
    return file contents. It is intended for Hermes/Nanobot review of the gateway
    safety envelope without leaking evidence payloads.
    """

    roots = allowed_roots() if roots is None else roots
    payload: dict[str, object] = {
        "status": "ok",
        "mode": "server-safe-read-only",
        "max_entries_per_root": max_entries_per_root,
        "roots": {},
    }
    root_payload: dict[str, object] = {}
    for alias, root in sorted(roots.items()):
        stats: dict[str, object] = {
            "path": str(root),
            "entries_seen": 0,
            "directories_exposed": 0,
            "files_exposed": 0,
            "entries_blocked": 0,
            "blocked_samples": [],
            "truncated": False,
        }
        blocked_samples: list[str] = []
        for index, child in enumerate(root.rglob("*"), start=1):
            if index > max_entries_per_root:
                stats["truncated"] = True
                break
            stats["entries_seen"] = int(stats["entries_seen"]) + 1
            rel = child.relative_to(root).as_posix()
            try:
                exposed = _is_exposed_directory_entry(child, root)
            except OSError:
                exposed = False
            if exposed:
                if child.is_dir():
                    stats["directories_exposed"] = int(stats["directories_exposed"]) + 1
                elif child.is_file():
                    stats["files_exposed"] = int(stats["files_exposed"]) + 1
            else:
                stats["entries_blocked"] = int(stats["entries_blocked"]) + 1
                if len(blocked_samples) < 20:
                    blocked_samples.append(rel)
        stats["blocked_samples"] = blocked_samples
        root_payload[alias] = stats
    payload["roots"] = root_payload
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def markdown_root_index(alias: str, roots: dict[str, Path] | None = None, *, limit: int = 80) -> bytes:
    """Return a small generated Markdown index for an exposed evidence root."""

    roots = allowed_roots() if roots is None else roots
    if alias not in roots:
        raise AccessDenied(f"unknown evidence alias: {alias}")
    root = roots[alias]
    entries: list[str] = []
    for child in sorted(root.rglob("*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
        if len(entries) >= limit:
            break
        try:
            if not child.is_file() or not _is_exposed_directory_entry(child, root):
                continue
            rel = child.relative_to(root).as_posix()
        except OSError:
            continue
        entries.append(f"- `/{alias}/{rel}`")
    body = [
        f"# Nanobot read-only {alias} index",
        "",
        "Generated by the read-only evidence gateway; GET/HEAD only.",
        "",
        f"Root: `/{alias}/`",
        "",
        "## Latest exposed files",
        "",
        *(entries or ["- No exposed files found."]),
        "",
    ]
    return ("\n".join(body)).encode()


def snapshot_index(roots: dict[str, Path] | None = None) -> bytes:
    roots = allowed_roots() if roots is None else roots
    urls = {
        "policy": ["/project-policy/AGENTS.md", "/project-policy/README.md", "/project-policy/Makefile"],
        "specs": [
            "/spec-kit/24-orchestration-backlog.md",
            "/spec-kit/26-nanobot-standing-worker.md",
            "/spec-kit/28-global-headroom-only-llm-channel.md",
            "/spec-kit/29-semantic-proposal-workflow.md",
            "/spec-kit/29-channel-registry.md",
            "/spec-kit/channel-registry.json",
        ],
        "acceptance": ["/project-docs/acceptance/index.md"],
        "reports": ["/reports/index.md", "/reports/project-docs-lag-audit/", "/reports/nanobot-cron-scout/"],
        "proposals": ["/proposals/index.md", "/proposals/semantic-review-indexes/", "/proposals/semantic-targeted-proposals/"],
    }
    available_urls = {
        group: [url for url in items if url.lstrip("/").split("/", 1)[0] in roots]
        for group, items in urls.items()
    }
    payload = {
        "status": "ok",
        "mode": "server-safe-read-only-snapshot",
        "description": "Canonical safe URLs for scheduled Nanobot docs/project lag audits.",
        "mutating_methods": "disabled",
        "urls": available_urls,
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


class EvidenceRequestHandler(BaseHTTPRequestHandler):
    server_version = "NanobotReadonlyEvidenceGateway/1.0"
    roots: ClassVar[dict[str, Path]] = {}

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        # Keep stdout quiet; systemd/terminal callers still see explicit startup.
        return

    def _send_bytes(self, body: bytes, *, status: HTTPStatus = HTTPStatus.OK, content_type: str = "application/octet-stream") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Nanobot-Evidence-Mode", "read-only")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_error_json(self, status: HTTPStatus, message: str) -> None:
        body = (json.dumps({"status": "error", "error": message}, sort_keys=True) + "\n").encode()
        self._send_bytes(body, status=status, content_type="application/json; charset=utf-8")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Allow", "GET, HEAD, OPTIONS")
        self.send_header("X-Nanobot-Evidence-Mode", "read-only")
        self.end_headers()

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.json"):
            self._send_bytes(list_index(self.roots), content_type="application/json; charset=utf-8")
            return
        if parsed.path == "/audit.json":
            self._send_bytes(audit_roots(self.roots), content_type="application/json; charset=utf-8")
            return
        if parsed.path == "/snapshot.json":
            self._send_bytes(snapshot_index(self.roots), content_type="application/json; charset=utf-8")
            return
        if parsed.path in ("/reports/index.md", "/proposals/index.md"):
            alias = parsed.path.strip("/").split("/", 1)[0]
            try:
                self._send_bytes(markdown_root_index(alias, self.roots), content_type="text/markdown; charset=utf-8")
            except AccessDenied as exc:
                self._send_error_json(HTTPStatus.FORBIDDEN, str(exc))
            return
        if parsed.path == "/health":
            self._send_bytes(
                b'{"status":"ok","mode":"server-safe-read-only"}\n',
                content_type="application/json; charset=utf-8",
            )
            return
        try:
            alias, target = resolve_evidence_path(parsed.path, self.roots)
        except FileNotFoundError:
            self._send_error_json(HTTPStatus.NOT_FOUND, "not found")
            return
        except AccessDenied as exc:
            self._send_error_json(HTTPStatus.FORBIDDEN, str(exc))
            return
        if target.is_dir():
            items = []
            for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                rel = child.relative_to(self.roots[alias])
                if not _alias_allows_rel(alias, rel):
                    continue
                if not _is_exposed_directory_entry(child, self.roots[alias]):
                    continue
                suffix = "/" if child.is_dir() else ""
                href = f"/{alias}/{rel.as_posix()}{suffix}"
                items.append(f'<li><a href="{html.escape(href)}">{html.escape(child.name + suffix)}</a></li>')
            rel_label = "" if target == self.roots[alias] else str(target.relative_to(self.roots[alias]))
            body = (
                "<!doctype html><meta charset=utf-8><title>Nanobot read-only evidence</title>"
                f"<h1>/{html.escape(alias)}/{html.escape(rel_label)}</h1>"
                "<p>server-safe read-only gateway; GET/HEAD only</p><ul>"
                + "".join(items)
                + "</ul>"
            ).encode()
            self._send_bytes(body, content_type="text/html; charset=utf-8")
            return
        content_type = mimetypes.guess_type(target.name)[0] or "text/plain"
        if content_type.startswith("text/") or target.suffix.lower() in {".json", ".jsonl"}:
            content_type += "; charset=utf-8"
        self._send_bytes(target.read_bytes(), content_type=content_type)

    def do_POST(self) -> None:  # noqa: N802
        self._send_error_json(HTTPStatus.METHOD_NOT_ALLOWED, "read-only gateway: mutating methods are disabled")

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST


def make_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    roots = allowed_roots(existing_only=True)
    handler = type("ConfiguredEvidenceRequestHandler", (EvidenceRequestHandler,), {"roots": roots})
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nanobot read-only evidence gateway")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--print-index", action="store_true", help="Print root index JSON and exit")
    parser.add_argument("--print-audit", action="store_true", help="Print content-free root exposure audit JSON and exit")
    parser.add_argument("--print-snapshot", action="store_true", help="Print canonical safe audit URLs JSON and exit")
    args = parser.parse_args(argv)
    if args.print_index:
        print(list_index().decode(), end="")
        return 0
    if args.print_audit:
        print(audit_roots().decode(), end="")
        return 0
    if args.print_snapshot:
        print(snapshot_index().decode(), end="")
        return 0
    server = make_server(args.host, args.port)
    print(f"nanobot evidence gateway: http://{args.host}:{args.port}/ (read-only)", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
