from pathlib import Path

import pytest

from obslayer.nanobot_readonly_evidence_gateway import AccessDenied, resolve_evidence_path


def test_resolve_allowed_file(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    report = root / "REPORT.md"
    report.write_text("ok", encoding="utf-8")

    alias, resolved = resolve_evidence_path("/reports/REPORT.md", {"reports": root.resolve()})

    assert alias == "reports"
    assert resolved == report.resolve()


@pytest.mark.parametrize(
    "url_path",
    [
        "/reports/../secret.md",
        "/reports/.hidden/file.md",
        "/reports/token.json",
        "/reports/secure/REPORT.md",
        "/reports/Obsidian/NOTE.md",
        "/unknown/REPORT.md",
    ],
)
def test_rejects_unsafe_paths(tmp_path: Path, url_path: str) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    (root / "token.json").write_text("{}", encoding="utf-8")
    with pytest.raises(AccessDenied):
        resolve_evidence_path(url_path, {"reports": root.resolve()})


def test_rejects_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("no", encoding="utf-8")
    (root / "escape.md").symlink_to(outside)

    with pytest.raises(AccessDenied):
        resolve_evidence_path("/reports/escape.md", {"reports": root.resolve()})


def test_rejects_binary_extension(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    binary = root / "blob.sqlite"
    binary.write_bytes(b"sqlite")

    with pytest.raises(AccessDenied):
        resolve_evidence_path("/reports/blob.sqlite", {"reports": root.resolve()})


def test_rejects_oversized_text_file(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    huge = root / "huge.md"
    huge.write_text("x" * 2_000_001, encoding="utf-8")

    with pytest.raises(AccessDenied):
        resolve_evidence_path("/reports/huge.md", {"reports": root.resolve()})


def test_allows_server_safe_root_file(tmp_path: Path) -> None:
    root = tmp_path / "work"
    root.mkdir()
    readme = root / "README.md"
    readme.write_text("server context", encoding="utf-8")

    alias, resolved = resolve_evidence_path("/server-work/README.md", {"server-work": root.resolve()})

    assert alias == "server-work"
    assert resolved == readme.resolve()


def test_allows_systemd_unit_extension(tmp_path: Path) -> None:
    root = tmp_path / "systemd"
    root.mkdir()
    unit = root / "demo.service"
    unit.write_text("[Service]\nExecStart=/bin/true\n", encoding="utf-8")

    alias, resolved = resolve_evidence_path("/server-user-systemd/demo.service", {"server-user-systemd": root.resolve()})

    assert alias == "server-user-systemd"
    assert resolved == unit.resolve()


def test_allows_text_script_without_extension(tmp_path: Path) -> None:
    root = tmp_path / "bin"
    root.mkdir()
    script = root / "tool"
    script.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")

    alias, resolved = resolve_evidence_path("/server-local-bin/tool", {"server-local-bin": root.resolve()})

    assert alias == "server-local-bin"
    assert resolved == script.resolve()


def test_rejects_binary_without_extension(tmp_path: Path) -> None:
    root = tmp_path / "bin"
    root.mkdir()
    binary = root / "binary"
    binary.write_bytes(b"\x00\x01not text")

    with pytest.raises(AccessDenied):
        resolve_evidence_path("/server-local-bin/binary", {"server-local-bin": root.resolve()})


class _ServerContext:
    def __init__(self, roots: dict[str, Path]):
        from http.server import ThreadingHTTPServer

        from obslayer.nanobot_readonly_evidence_gateway import EvidenceRequestHandler

        handler = type("TestEvidenceRequestHandler", (EvidenceRequestHandler,), {"roots": roots})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = None

    def __enter__(self):
        import threading

        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        if self.thread:
            self.thread.join(timeout=2)


def _request(url: str, method: str = "GET"):
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def test_http_handler_allows_get_head_options_and_blocks_post(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    (root / "REPORT.md").write_text("ok", encoding="utf-8")

    with _ServerContext({"reports": root.resolve()}) as base_url:
        assert _request(f"{base_url}/reports/REPORT.md")[0] == 200
        assert _request(f"{base_url}/reports/REPORT.md", "HEAD") == (200, "")
        assert _request(f"{base_url}/reports/REPORT.md", "OPTIONS")[0] == 204
        status, body = _request(f"{base_url}/reports/REPORT.md", "POST")

    assert status == 405
    assert "read-only" in body


def test_http_handler_blocks_traversal_hidden_secret_and_binary(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    (root / "safe.md").write_text("ok", encoding="utf-8")
    (root / ".hidden.md").write_text("hidden", encoding="utf-8")
    (root / "token.json").write_text("{}", encoding="utf-8")
    (root / "blob.sqlite").write_bytes(b"sqlite")

    with _ServerContext({"reports": root.resolve()}) as base_url:
        assert _request(f"{base_url}/reports/safe.md")[0] == 200
        assert _request(f"{base_url}/reports/../safe.md")[0] == 403
        assert _request(f"{base_url}/reports/.hidden.md")[0] == 403
        assert _request(f"{base_url}/reports/token.json")[0] == 403
        assert _request(f"{base_url}/reports/blob.sqlite")[0] == 403


def test_http_directory_listing_filters_unexposed_entries(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    (root / "safe.md").write_text("ok", encoding="utf-8")
    (root / "token.json").write_text("{}", encoding="utf-8")
    (root / ".hidden.md").write_text("hidden", encoding="utf-8")

    with _ServerContext({"reports": root.resolve()}) as base_url:
        status, body = _request(f"{base_url}/reports/")

    assert status == 200
    assert "safe.md" in body
    assert "token.json" not in body
    assert ".hidden.md" not in body



def test_http_audit_reports_counts_without_file_contents(tmp_path: Path) -> None:
    root = tmp_path / "reports"
    root.mkdir()
    (root / "safe.md").write_text("VISIBLE_SECRET_SHOULD_NOT_APPEAR", encoding="utf-8")
    (root / "token.json").write_text("SECRET_VALUE_SHOULD_NOT_APPEAR", encoding="utf-8")

    with _ServerContext({"reports": root.resolve()}) as base_url:
        status, body = _request(f"{base_url}/audit.json")

    assert status == 200
    assert "files_exposed" in body
    assert "entries_blocked" in body
    assert "token.json" in body
    assert "VISIBLE_SECRET_SHOULD_NOT_APPEAR" not in body
    assert "SECRET_VALUE_SHOULD_NOT_APPEAR" not in body
