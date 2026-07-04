from pathlib import Path

from obslayer.llm_channel_smoke import run_llm_channel_smoke


def _registry(path: Path, nanobot_shape: str = "Headroom backend Codex bridge, not generic /v1/responses") -> Path:
    payload = {
        "schema_version": 1,
        "global_rule": "External LLM-provider traffic routes through Headroom by default.",
        "channels": [
            {
                "component": "Codex CLI",
                "role": "worker",
                "external_llm_allowed": True,
                "required_route": "OPENAI_BASE_URL=http://127.0.0.1:8787/v1 through Headroom",
                "may_mutate": "repository/task scope only",
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["direct upstream base_url"],
            },
            {
                "component": "Headroom",
                "role": "proxy",
                "external_llm_allowed": True,
                "required_route": "loopback service 127.0.0.1:8787",
                "may_mutate": False,
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["public exposure"],
            },
            {
                "component": "Nanobot Hermes communicator",
                "role": "proposal worker",
                "external_llm_allowed": True,
                "required_route": (
                    "/home/hermesadmin/.nanobot-hermes/bin/nanobot-headroom-agent -> "
                    "http://127.0.0.1:8787/backend-api/codex/responses"
                ),
                "accepted_endpoint_shape": nanobot_shape,
                "may_mutate": False,
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["direct provider"],
            },
            {
                "component": "Nanobot read-only evidence gateway",
                "role": "evidence",
                "external_llm_allowed": False,
                "required_route": "http://127.0.0.1:18791/ allowlisted prefixes only",
                "may_mutate": False,
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["CIDR-wide localhost"],
            },
            {
                "component": "Graphify",
                "role": "graph adapter",
                "external_llm_allowed": True,
                "required_route": (
                    "graphify-headroom + codex-cli through Headroom for external semantic extraction; "
                    "Ollama local for embeddings"
                ),
                "may_mutate": False,
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["direct provider"],
            },
        ],
    }
    import json

    p = path / "channel-registry.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_llm_channel_smoke_offline_ok(tmp_path: Path) -> None:
    report = run_llm_channel_smoke(_registry(tmp_path), generated_utc="2026-07-04T00:00:00Z")

    assert report.status == "ok"
    assert report.assertions["nanobot_uses_backend_codex_bridge"] is True
    assert report.assertions["nanobot_rejects_generic_v1_responses"] is True
    assert {probe.status for probe in report.probes} == {"skipped"}


def test_llm_channel_smoke_flags_generic_nanobot_route(tmp_path: Path) -> None:
    report = run_llm_channel_smoke(_registry(tmp_path, "generic /v1/responses"))

    assert report.status == "failed"
    assert report.assertions["nanobot_rejects_generic_v1_responses"] is False
    assert "assertion failed: nanobot_rejects_generic_v1_responses" in report.findings
