from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from obslayer import GuardrailError
from obslayer.indexing_wrapper import (
    INDEXING_WRAPPER_TOOL_ALLOWLIST,
    REDACTED_DERIVED_ROOT,
    REDACTED_LIVE_VAULT,
    REDACTED_SANDBOX_VAULT,
    IndexingWrapperPolicy,
    assert_indexing_tool_allowed,
    build_indexing_mcp_process_spec,
    build_indexing_wrapper_policy,
    discover_indexing_exclude_prefixes,
    normalize_indexing_exclude_prefixes,
    normalize_indexing_mcp_result,
    normalize_loopback_ollama_base_url,
    parse_mcp_text_result,
    redact_live_vault_paths,
    require_not_live_vault_path,
    sanitize_indexing_mcp_transcript,
    verify_indexing_runtime_tools,
    write_indexing_mcp_report_bundle,
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


def test_discover_indexing_excludes_nested_archives_for_candidate_prefix_semantics(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    for rel in [
        "_Archive/root.md",
        "Memory-Vault/_Archive/old.md",
        "Soul-Vault/_Archive/Duplicates/old.md",
        "Soul-Vault/Soul/private.md",
        "Notes/keep.md",
    ]:
        target = vault / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# note\n", encoding="utf-8")

    prefixes = discover_indexing_exclude_prefixes(vault)

    assert "_Archive/" in prefixes
    assert "Memory-Vault/_Archive/" in prefixes
    assert "Soul-Vault/_Archive/" in prefixes
    assert "Soul-Vault/Soul/" in prefixes
    assert "Notes/" not in prefixes


def test_indexing_exclude_prefixes_are_normalized_and_injected_into_process_env(tmp_path: Path) -> None:
    assert normalize_indexing_exclude_prefixes(["Soul-Vault/_Archive", "Soul-Vault/_Archive/", "Memory-Vault\\_Archive"]) == (
        "Soul-Vault/_Archive/",
        "Memory-Vault/_Archive/",
    )
    for bad in ["/Soul-Vault/_Archive", "../escape", "C:/Users/Alice/Secrets", "\\\\server\\share"]:
        with pytest.raises(GuardrailError, match="vault-relative"):
            normalize_indexing_exclude_prefixes([bad])

    sandbox = make_sandbox(tmp_path)
    (sandbox / "Nested" / "_Archive").mkdir(parents=True)
    derived = repo_root() / "out" / "external-indexing-spike" / f"exclude-{tmp_path.name}"
    policy = build_indexing_wrapper_policy(vault_root=sandbox, derived_root=derived, discover_nested_excludes=True)
    spec = build_indexing_mcp_process_spec(command=["node", "server.js"], policy=policy)

    assert "Nested/_Archive/" in policy.exclude_paths
    assert "Nested/_Archive/" in spec.env["OBSIDIAN_SEMANTIC_EXCLUDE"]


def test_process_spec_revalidates_direct_policy_exclude_paths(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    derived = repo_root() / "out" / "external-indexing-spike" / f"direct-policy-{tmp_path.name}"
    policy = IndexingWrapperPolicy(
        vault_root=str(sandbox.resolve()),
        derived_root=str(derived.resolve()),
        ollama_base_url="http://localhost:11434",
        exclude_paths=("/tmp/evil",),
    )

    with pytest.raises(GuardrailError, match="vault-relative"):
        build_indexing_mcp_process_spec(command=["node", "server.js"], policy=policy)


def test_tool_allowlist_rejects_mutation_tools() -> None:
    assert assert_indexing_tool_allowed("search_notes") == "search_notes"
    with pytest.raises(GuardrailError, match="allowlisted"):
        assert_indexing_tool_allowed("write_note")


def test_parse_mcp_text_result_decodes_json_text_payload() -> None:
    assert parse_mcp_text_result(mcp_text({"results": [{"path": "a.md"}]})) == {"results": [{"path": "a.md"}]}
    assert parse_mcp_text_result({"result": {"content": [{"type": "text", "text": "plain"}]}}) == "plain"


def test_parse_mcp_text_result_handles_bom_whitespace_and_invalid_json() -> None:
    assert parse_mcp_text_result({"result": {"content": [{"type": "text", "text": '\ufeff  {"ok": true}  '}]}}) == {"ok": True}
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


def test_normalize_search_result_converts_absolute_sandbox_path_before_provenance(tmp_path: Path) -> None:
    sandbox = make_sandbox(tmp_path)
    message = mcp_text({"results": [{"path": str((sandbox / "Notes" / "alpha.md").resolve()), "matched_sections": []}]})

    normalized = normalize_indexing_mcp_result(tool="search_notes", message=message, vault_root=sandbox)

    assert normalized.payload["results"][0]["path"] == "Notes/alpha.md"
    assert normalized.provenance[0]["path"] == "Notes/alpha.md"
    assert normalized.provenance[0]["hash_or_version"] != "missing"


@pytest.mark.parametrize("protected_rel", [".obsidian/app.json", "_Archive/old.md"])
def test_normalize_search_result_rejects_absolute_sandbox_protected_paths(tmp_path: Path, protected_rel: str) -> None:
    sandbox = make_sandbox(tmp_path)
    target = sandbox / protected_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("protected", encoding="utf-8")

    with pytest.raises(GuardrailError, match="protected"):
        normalize_indexing_mcp_result(
            tool="search_notes",
            message=mcp_text({"results": [{"path": str(target.resolve()), "matched_sections": []}]}),
            vault_root=sandbox,
        )


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


def runtime_policy(tmp_path: Path):
    sandbox = make_sandbox(tmp_path)
    derived = repo_root() / "out" / "external-indexing-spike" / f"runtime-{tmp_path.name}"
    return build_indexing_wrapper_policy(vault_root=sandbox, derived_root=derived)


def test_verify_indexing_runtime_tools_rejects_extra_or_missing_tools(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    ok_message = mcp_text({"tools": [{"name": name} for name in INDEXING_WRAPPER_TOOL_ALLOWLIST]})
    assert verify_indexing_runtime_tools(ok_message, policy) == list(INDEXING_WRAPPER_TOOL_ALLOWLIST)

    with pytest.raises(GuardrailError, match="non-allowlisted"):
        verify_indexing_runtime_tools(mcp_text({"tools": [*INDEXING_WRAPPER_TOOL_ALLOWLIST, "write_note"]}), policy)
    with pytest.raises(GuardrailError, match="missing"):
        verify_indexing_runtime_tools(mcp_text({"tools": ["index_status"]}), policy)
    with pytest.raises(GuardrailError, match="string name"):
        verify_indexing_runtime_tools(mcp_text({"tools": [{"name": 123}]}), policy)
    with pytest.raises(GuardrailError, match="duplicate"):
        verify_indexing_runtime_tools(mcp_text({"tools": [*INDEXING_WRAPPER_TOOL_ALLOWLIST, "search_notes"]}), policy)


def test_build_indexing_mcp_process_spec_injects_safe_env_and_refuses_live_cwd(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    spec = build_indexing_mcp_process_spec(command=["node", "server.js"], policy=policy, extra_env={"PATH": "/usr/bin"})

    assert spec.command == ("node", "server.js")
    assert spec.env["PATH"] == "/usr/bin"
    assert spec.env["OBSIDIAN_VAULT_PATH"] == policy.vault_root
    assert spec.env["OBSIDIAN_VAULT_ROOT"] == policy.vault_root
    assert spec.env["VAULT_ROOT"] == policy.vault_root
    assert spec.env["OBSIDIAN_SEMANTIC_MCP_HOME"] == policy.derived_root
    assert spec.env["INDEXING_DERIVED_ROOT"] == policy.derived_root
    assert spec.env["OLLAMA_BASE_URL"] == "http://localhost:11434"

    with pytest.raises(GuardrailError, match="live vault"):
        build_indexing_mcp_process_spec(command=["node"], policy=policy, cwd=Path("/home/hermesadmin/Obsidian"))
    with pytest.raises(GuardrailError, match="non-empty"):
        build_indexing_mcp_process_spec(command=[], policy=policy)


def test_sanitize_indexing_mcp_transcript_gates_tools_and_returns_only_sanitized_payload(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    transcript = sanitize_indexing_mcp_transcript(
        [
            {"kind": "list_tools", "message": mcp_text({"tools": [{"name": name} for name in INDEXING_WRAPPER_TOOL_ALLOWLIST]})},
            {
                "tool": "search_notes",
                "message": mcp_text(
                    {
                        "results": [
                            {
                                "path": "Notes/alpha.md",
                                "matched_sections": [
                                    {"line": 2, "snippet": "mentions /home/hermesadmin/Obsidian in sandbox output"}
                                ],
                            }
                        ]
                    }
                ),
            },
        ],
        policy=policy,
    )

    assert transcript.calls[0] == {"kind": "list_tools", "tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)}
    result = transcript.calls[1]
    assert result["kind"] == "tool_result"
    assert result["payload"]["results"][0]["matched_sections"][0]["snippet"] == "mentions <LIVE_VAULT> in sandbox output"
    assert result["provenance"][0]["snippet"] == "mentions <LIVE_VAULT> in sandbox output"
    assert transcript.redactions
    assert "/home/hermesadmin/Obsidian" not in json.dumps(transcript.to_dict())


def test_sanitize_indexing_mcp_transcript_redacts_safe_derived_root_paths(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    derived_db = f"{policy.derived_root}/data/semantic.sqlite"
    transcript = sanitize_indexing_mcp_transcript(
        [
            {"kind": "list_tools", "message": mcp_text({"tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)})},
            {
                "tool": "index_status",
                "message": mcp_text({"db_path": derived_db, "read_only": True, "notes": 0}),
            },
        ],
        policy=policy,
    )

    dumped = json.dumps(transcript.to_dict())
    assert policy.derived_root not in dumped
    assert f"{REDACTED_DERIVED_ROOT}/data/semantic.sqlite" in dumped
    assert any(item["kind"] == "derived-root-path" for item in transcript.redactions)


def test_sanitize_indexing_mcp_transcript_redacts_sandbox_vault_root_paths(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    transcript = sanitize_indexing_mcp_transcript(
        [
            {"kind": "list_tools", "message": mcp_text({"tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)})},
            {
                "tool": "index_status",
                "message": mcp_text({"vault_root": policy.vault_root, "read_only": True, "notes": 0}),
            },
        ],
        policy=policy,
    )

    dumped = json.dumps(transcript.to_dict())
    assert policy.vault_root not in dumped
    assert REDACTED_SANDBOX_VAULT in dumped
    assert any(item["kind"] == "sandbox-vault-path" for item in transcript.redactions)


def test_sanitize_indexing_mcp_transcript_rejects_unsafe_runtime_outputs(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    with pytest.raises(GuardrailError, match="non-allowlisted"):
        sanitize_indexing_mcp_transcript(
            [{"kind": "list_tools", "message": mcp_text({"tools": [*INDEXING_WRAPPER_TOOL_ALLOWLIST, "delete_note"]})}],
            policy=policy,
        )
    with pytest.raises(GuardrailError):
        sanitize_indexing_mcp_transcript(
            [{"tool": "search_notes", "message": mcp_text({"results": [{"path": "%2Ftmp%2Fevil.md"}]})}],
            policy=policy,
        )


def test_sanitize_indexing_mcp_transcript_requires_list_tools_gate(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    with pytest.raises(GuardrailError, match="list_tools"):
        sanitize_indexing_mcp_transcript(
            [{"tool": "index_status", "message": mcp_text({"ok": True})}],
            policy=policy,
        )
    with pytest.raises(GuardrailError, match="Unexpected MCP transcript call kind"):
        sanitize_indexing_mcp_transcript(
            [
                {"kind": "list_tools", "message": mcp_text({"tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)})},
                {"kind": "notification", "message": {}},
            ],
            policy=policy,
        )


def test_sanitize_indexing_mcp_transcript_truncates_long_sanitized_text(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    long_snippet = "x" * 2_500
    transcript = sanitize_indexing_mcp_transcript(
        [
            {"kind": "list_tools", "message": mcp_text({"tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)})},
            {
                "tool": "search_notes",
                "message": mcp_text(
                    {"results": [{"path": "Notes/alpha.md", "matched_sections": [{"line": 1, "snippet": long_snippet}]}]}
                ),
            },
        ],
        policy=policy,
    )

    dumped = json.dumps(transcript.to_dict())
    assert len(transcript.calls[1]["payload"]["results"][0]["matched_sections"][0]["snippet"]) == 2_000
    assert "<TRUNCATED>" in dumped
    assert any(item["kind"] == "long-text-truncation" for item in transcript.redactions)


def test_write_indexing_mcp_report_bundle_splits_raw_and_sanitized_reports(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    calls = [
        {"kind": "list_tools", "message": mcp_text({"tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)})},
        {
            "tool": "search_notes",
            "message": mcp_text(
                {
                    "results": [
                        {
                            "path": "Notes/alpha.md",
                            "matched_sections": [{"line": 2, "snippet": "/home/hermesadmin/Obsidian appears"}],
                        }
                    ]
                }
            ),
        },
    ]
    report_root = Path(policy.derived_root).parents[1] / "reports" / "external-indexing-spike" / f"runtime-{tmp_path.name}"
    bundle = write_indexing_mcp_report_bundle(
        calls=calls,
        policy=policy,
        raw_report=report_root / "raw" / "transcript.json",
        sanitized_report=report_root / "sanitized-transcript.json",
        report_root=report_root,
    )

    raw_text = Path(bundle.raw_report).read_text(encoding="utf-8")
    sanitized_text = Path(bundle.sanitized_report).read_text(encoding="utf-8")
    assert "/home/hermesadmin/Obsidian" in raw_text
    assert "/home/hermesadmin/Obsidian" not in sanitized_text
    assert "<LIVE_VAULT>" in sanitized_text

    with pytest.raises(GuardrailError, match="separate files"):
        write_indexing_mcp_report_bundle(
            calls=calls,
            policy=policy,
            raw_report=report_root / "same.json",
            sanitized_report=report_root / "same.json",
            report_root=report_root,
        )
    with pytest.raises(GuardrailError, match="report"):
        write_indexing_mcp_report_bundle(
            calls=calls,
            policy=policy,
            raw_report=tmp_path / "outside.json",
            sanitized_report=report_root / "safe.json",
            report_root=report_root,
        )


def test_parse_mcp_text_result_rejects_ambiguous_multi_text_json_objects() -> None:
    with pytest.raises(GuardrailError, match="multiple text"):
        parse_mcp_text_result(
            {
                "result": {
                    "content": [
                        {"type": "text", "text": '{"a": 1}'},
                        {"type": "text", "text": '{"b": 2}'},
                    ]
                }
            }
        )


def test_sanitize_indexing_mcp_transcript_redacts_deep_url_encoded_live_paths(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    deeply_encoded_live = "%2525252Fhome%2525252Fhermesadmin%2525252FObsidian%2525252FSecret.md"

    transcript = sanitize_indexing_mcp_transcript(
        [
            {"kind": "list_tools", "message": mcp_text({"tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)})},
            {
                "tool": "search_notes",
                "message": mcp_text({"results": [{"path": "Notes/alpha.md", "matched_sections": [{"snippet": deeply_encoded_live}]}]}),
            },
        ],
        policy=policy,
    )

    dumped = json.dumps(transcript.to_dict())
    assert deeply_encoded_live not in dumped
    assert "/home/hermesadmin/Obsidian" not in dumped
    assert REDACTED_LIVE_VAULT in dumped


def test_write_indexing_mcp_report_bundle_rejects_live_or_outside_report_root(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)
    calls = [{"kind": "list_tools", "message": mcp_text({"tools": list(INDEXING_WRAPPER_TOOL_ALLOWLIST)})}]

    for unsafe_root in [Path("/home/hermesadmin/Obsidian") / "Reports", tmp_path / "reports"]:
        with pytest.raises(GuardrailError):
            write_indexing_mcp_report_bundle(
                calls=calls,
                policy=policy,
                raw_report=unsafe_root / "raw.json",
                sanitized_report=unsafe_root / "sanitized.json",
                report_root=unsafe_root,
            )


def test_build_indexing_mcp_process_spec_rejects_secret_or_live_vault_extra_env(tmp_path: Path) -> None:
    policy = runtime_policy(tmp_path)

    for extra_env in [
        {"OPENAI_API_KEY": "secret"},
        {"HOME": "/home/hermesadmin/Obsidian"},
        {"HTTP_PROXY": "http://proxy.local:8080"},
    ]:
        with pytest.raises(GuardrailError):
            build_indexing_mcp_process_spec(command=["node"], policy=policy, extra_env=extra_env)
