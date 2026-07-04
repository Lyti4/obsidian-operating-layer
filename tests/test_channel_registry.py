from __future__ import annotations

import json
from pathlib import Path

import pytest

from obslayer import GuardrailError
from obslayer.channel_registry import validate_channel_registry


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_project_channel_registry_validates() -> None:
    report = validate_channel_registry(repo_root() / "docs" / "spec-kit" / "channel-registry.json")

    assert report.status == "ok"
    assert "Codex CLI" in report.headroom_routed_components
    assert "Nanobot Hermes communicator" in report.headroom_routed_components
    assert "Nanobot read-only evidence gateway" in report.local_only_components


def test_registry_rejects_nanobot_mutation(tmp_path: Path) -> None:
    registry = {
        "schema_version": 1,
        "global_rule": "External traffic routes through Headroom.",
        "channels": [
            {
                "component": "Codex CLI",
                "role": "worker",
                "external_llm_allowed": True,
                "required_route": "Headroom",
                "may_mutate": "repo only",
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["direct provider forbidden"],
            },
            {
                "component": "Headroom",
                "role": "router",
                "external_llm_allowed": True,
                "required_route": "Headroom loopback",
                "may_mutate": False,
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["public exposure"],
            },
            {
                "component": "Nanobot Hermes communicator",
                "role": "proposal worker",
                "external_llm_allowed": True,
                "required_route": "Headroom backend bridge",
                "may_mutate": True,
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["direct provider forbidden"],
            },
            {
                "component": "Graphify",
                "role": "adapter",
                "external_llm_allowed": True,
                "required_route": "Headroom",
                "may_mutate": False,
                "acceptance_owner": "Hermes",
                "forbidden_fallbacks": ["live writes"],
            },
        ],
    }
    path = tmp_path / "channel-registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(GuardrailError, match="Nanobot Hermes communicator: may_mutate must be false"):
        validate_channel_registry(path)
