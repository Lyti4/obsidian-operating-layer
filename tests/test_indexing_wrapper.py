from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from obslayer import GuardrailError
from obslayer.indexing_wrapper import (
    INDEXING_WRAPPER_TOOL_ALLOWLIST,
    REDACTED_LIVE_VAULT,
    assert_indexing_tool_allowed,
    build_indexing_wrapper_policy,
    normalize_indexing_mcp_result,
    normalize_loopback_ollama_base_url,
    parse_mcp_text_result,
    redact_live_vault_paths,
    require_not_live_vault_path,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def make_sandbox(tmp_path: Path) -> Path:
    sandbox = repo_root() / "out" / "sandbox-vaults" / f"wrapper-pytest-{tmp_path.name}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    (sandbox / "Notes").mkdir(parents=True)
    (sandbox / "Notes" / "alpha.md").write_text(
        "# Alpha\nSnippet mentions /home/hermesadmin/Obsidian but is sandbox content.\n",
        encoding="utf-8",
    )
    return sandbox


def mcp_text(payload: object) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": json.dumps(payload)}]}}


def test_loopback_ollama_url_normalization_accepts_only_bare_local_http() -> None:
    assert normalize_loopback_ollama_base_url("http://localhost:11434") == "http://localhost:11434"
    assert normalize_loopback_ollama_base_url("http://127.0.0.1") == "http://127.0.0.1:11434"

    for bad in [
        "https://localhost:11434",
        "http://example.invalid:11434",
        "http://192.168.1.10:11434",
        "http://user:pass@localhost:11434",
        "http://localhost:11435",
        "http://localhost:11434/api/embed",
        "http://localhost:11434?x=1",
    ]:
        with pytest.raises(GuardrailError):
            normalize_loopback_ollama_base_url(bad)


def test_build_indexing_wrapper_policy_rejects_live_vault_and_remote_derived_paths(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    derived = repo_root() / "out" / "external-indexing-spike" / f"policy-{tmp_path.name}"

    policy = build_indexing_wrapper_policy(vault_root=sandbox, derived_root=derived, ollama_base_url="http://localhost:11434")
    assert policy.vault_root == str(sandbox.resolve())
    assert policy.derived_root == str(derived.resolve())
    assert policy.allowed_tools == INDEXING_WRAPPER_TOOL_ALLOWLIST

    live_vault = Path("/home/hermesadmin/Obsidian")
    with pytest.raises(GuardrailError, match="live vault"):
        build_indexing_wrapper_policy(vault_root=live_vault, derived_root=derived)
    with pytest.raises(GuardrailError, match="live vault"):
        build_indexing_wrapper_policy(vault_root=sandbox, derived_root=live_vault / "cache")

    with pytest.raises(GuardrailError, match="derived storage"):
        build_indexing_wrapper_policy(vault_root=sandbox, derived_root=tmp_path / "mcp-home")


def test_live_vault_refusal_is_independent_of_live_root_existence(tmp_path: Path) -> None:
    missing_live = tmp_path / "missing-live-vault"
    with pytest.raises(GuardrailError, match="live vault"):
        require_not_live_vault_path(missing_live / "Nested" / "note.md", live_vault_root=missing_live)


def test_tool_allowlist_rejects_mutation_tools() -> None:
    assert assert_indexing_tool_allowed("search_notes") == "search_notes"
    with pytest.raises(GuardrailError, match="allowlisted"):
        assert_indexing_tool_allowed("write_note")


def test_parse_mcp_text_result_decodes_json_text_payload() -> None:
    assert parse_mcp_text_result(mcp_text({"results": [{"path": "a.md"}]})) == {"results": [{"path": "a.md"}]}
    assert parse_mcp_text_result({"result": {"content": [{"type": "text", "text": "plain"}]}}) == "plain"


def test_parse_mcp_text_result_handles_bom_whitespace_multiple_content_and_invalid_json() -> None:
    assert parse_mcp_text_result(
        {
            "result": {
                "content": [
                    {"type": "image", "data": "ignored"},
                    {"type": "text", "text": '\ufeff  {"ok": true}  '},
                    {"type": "text", "text": '{"ignored": true}'},
                ]
            }
        }
    ) == {"ok": True}
    assert parse_mcp_text_result({"result": {"content": [{"type": "text", "text": "{bad json"}]}}) == "{bad json"
    assert parse_mcp_text_result({"error": {"message": "/home/hermesadmin/Obsidian leaked"}}) == {
        "error": {"message": "/home/hermesadmin/Obsidian leaked"}
    }


def test_redact_live_vault_paths_recursively() -> None:
    payload = {
        "snippet": "run /home/hermesadmin/Obsidian safely",
        "nested": ["/home/hermesadmin/Obsidian/Note.md"],
        "url_encoded": "%2Fhome%2Fhermesadmin%2FObsidian%2FNote.md",
        "url_encoded_lowercase": "%2fhome%2fhermesadmin%2fObsidian%2fNote.md",
    }
    redacted, redactions = redact_live_vault_paths(payload)

    assert REDACTED_LIVE_VAULT in redacted["snippet"]
    assert REDACTED_LIVE_VAULT in redacted["nested"][0]
    assert REDACTED_LIVE_VAULT in redacted["url_encoded"]
    assert REDACTED_LIVE_VAULT in redacted["url_encoded_lowercase"]
    assert len(redactions) == 4


def test_normalize_search_result_redacts_snippets_and_injects_provenance_hash(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    note = sandbox / "Notes" / "alpha.md"
    expected_hash = "sha256:" + hashlib.sha256(note.read_bytes()).hexdigest()
    message = mcp_text(
        {
            "results": [
                {
                    "path": "Notes/alpha.md",
                    "title": "Alpha",
                    "matched_sections": [
                        {
                            "heading": "Alpha",
                            "line": 2,
                            "lines": [2, 2],
                            "snippet": "Snippet mentions /home/hermesadmin/Obsidian but is sandbox content.",
                        }
                    ],
                }
            ]
        }
    )

    normalized = normalize_indexing_mcp_result(tool="search_notes", message=message, vault_root=sandbox)
    assert normalized.redactions
    assert normalized.payload["results"][0]["matched_sections"][0]["snippet"].startswith("Snippet mentions <LIVE_VAULT>")
    assert normalized.provenance == [
        {
            "path": "Notes/alpha.md",
            "span": [2, 2],
            "snippet": "Snippet mentions <LIVE_VAULT> but is sandbox content.",
            "hash_or_version": expected_hash,
        }
    ]


@pytest.mark.parametrize(
    "bad_path",
    [
        "/tmp/evil.md",
        "../escape.md",
        ".obsidian/app.json",
        "/home/hermesadmin/Obsidian/Secret.md",
        "%2Ftmp%2Fevil.md",
        "%2fhome%2fhermesadmin%2fObsidian%2fSecret.md",
        "..%2Fescape.md",
    ],
)
def test_normalize_search_result_rejects_absolute_traversal_and_protected_paths(tmp_path: Path, bad_path: str) -> None:
    sandbox = make_sandbox(tmp_path)
    message = mcp_text({"results": [{"path": bad_path, "matched_sections": []}]})

    with pytest.raises(GuardrailError):
        normalize_indexing_mcp_result(tool="search_notes", message=message, vault_root=sandbox)


def test_normalize_read_note_result_redacts_content_and_rejects_protected_or_absolute_paths(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    message = mcp_text(
        {
            "path": "Notes/alpha.md",
            "start_line": 1,
            "end_line": 2,
            "content": "# Alpha\n/home/hermesadmin/Obsidian appears in content",
        }
    )
    normalized = normalize_indexing_mcp_result(tool="read_note", message=message, vault_root=sandbox)
    assert normalized.payload["content"].endswith("<LIVE_VAULT> appears in content")
    assert normalized.provenance[0]["path"] == "Notes/alpha.md"
    assert normalized.provenance[0]["span"] == [1, 2]

    for bad_path in [
        "/tmp/x.md",
        "/home/hermesadmin/Obsidian/Secret.md",
        "%2Ftmp%2Fevil.md",
        "%2fhome%2fhermesadmin%2fObsidian%2fSecret.md",
        "..%2Fescape.md",
    ]:
        with pytest.raises(GuardrailError, match="vault-relative"):
            normalize_indexing_mcp_result(tool="read_note", message=mcp_text({"path": bad_path}), vault_root=sandbox)
    with pytest.raises(GuardrailError, match="protected"):
        normalize_indexing_mcp_result(tool="read_note", message=mcp_text({"path": ".obsidian/app.json"}), vault_root=sandbox)


def test_normalize_status_and_index_payloads_have_derived_provenance(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    normalized = normalize_indexing_mcp_result(tool="index_status", message=mcp_text({"read_only": True}), vault_root=sandbox)
    assert normalized.provenance == [
        {"path": None, "span": None, "snippet": "derived-index-operation", "hash_or_version": "derived"}
    ]


@pytest.mark.parametrize("tool", ["index_status", "index_vault"])
@pytest.mark.parametrize(
    "payload",
    [
        {"path": "/tmp/evil.md"},
        {"path": "/home/hermesadmin/Obsidian/Secret.md"},
        {"path": "%2Ftmp%2Fevil.md"},
        {"path": "%2fhome%2fhermesadmin%2fObsidian%2fSecret.md"},
        {"path": "..%2Fescape.md"},
        {"files": ["Notes/alpha.md", ".obsidian/app.json"]},
        {"paths": [{"value": "/home/hermesadmin/Obsidian/Secret.md"}]},
        {"paths": [{"value": "%2Fhome%2Fhermesadmin%2FObsidian%2FSecret.md"}]},
        {"paths": [{"value": "..%2Fescape.md"}]},
        {"paths": [1]},
    ],
)
def test_normalize_status_and_index_payloads_reject_unsafe_path_metadata(
    tmp_path: Path, tool: str, payload: dict[str, object]
) -> None:
    sandbox = make_sandbox(tmp_path)

    with pytest.raises(GuardrailError):
        normalize_indexing_mcp_result(tool=tool, message=mcp_text(payload), vault_root=sandbox)
