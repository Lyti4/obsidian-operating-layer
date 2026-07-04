from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError

REQUIRED_CHANNEL_FIELDS = {
    "component",
    "role",
    "external_llm_allowed",
    "required_route",
    "may_mutate",
    "acceptance_owner",
    "forbidden_fallbacks",
}

EXTERNAL_DIRECT_PROVIDER_MARKERS = (
    "api.openai.com",
    "chatgpt.com/backend-api",
    "direct provider",
    "raw API key",
)

HEADROOM_REQUIRED_COMPONENTS = {
    "Codex CLI",
    "Nanobot Hermes communicator",
    "Graphify",
}


@dataclass(frozen=True)
class ChannelRegistryValidation:
    status: str
    registry: str
    channel_count: int
    components: list[str]
    external_llm_components: list[str]
    headroom_routed_components: list[str]
    local_only_components: list[str]
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_channel_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path).resolve()
    if registry_path.name != "channel-registry.json":
        raise GuardrailError(f"Expected channel-registry.json, got: {registry_path}")
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GuardrailError(f"Invalid channel registry JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GuardrailError("Channel registry root must be an object")
    return payload


def validate_channel_registry(path: str | Path) -> ChannelRegistryValidation:
    registry_path = Path(path).resolve()
    payload = load_channel_registry(registry_path)
    findings: list[str] = []

    if payload.get("schema_version") != 1:
        findings.append("schema_version must be 1")
    global_rule = payload.get("global_rule")
    if not isinstance(global_rule, str) or "Headroom" not in global_rule:
        findings.append("global_rule must explicitly mention Headroom")

    channels = payload.get("channels")
    if not isinstance(channels, list) or not channels:
        raise GuardrailError("Channel registry must contain a non-empty channels list")

    components: list[str] = []
    external_llm_components: list[str] = []
    headroom_routed_components: list[str] = []
    local_only_components: list[str] = []

    for idx, channel in enumerate(channels):
        if not isinstance(channel, dict):
            findings.append(f"channels[{idx}] must be an object")
            continue
        missing = sorted(REQUIRED_CHANNEL_FIELDS - set(channel))
        if missing:
            findings.append(f"channels[{idx}] missing fields: {', '.join(missing)}")
        component = str(channel.get("component", f"channels[{idx}]"))
        components.append(component)
        route = str(channel.get("required_route", ""))
        forbidden = channel.get("forbidden_fallbacks")
        if not isinstance(forbidden, list) or not all(isinstance(item, str) and item for item in forbidden):
            findings.append(f"{component}: forbidden_fallbacks must be a non-empty list of strings")
        may_mutate = channel.get("may_mutate")
        if component in {"Nanobot Hermes communicator", "Nanobot read-only evidence gateway", "Graphify", "Headroom"}:
            if may_mutate is not False:
                findings.append(f"{component}: may_mutate must be false")
        if channel.get("external_llm_allowed") is True:
            external_llm_components.append(component)
            if "Headroom" in route or "headroom" in route:
                headroom_routed_components.append(component)
            elif component in HEADROOM_REQUIRED_COMPONENTS:
                findings.append(f"{component}: external LLM route must mention Headroom")
            lower_route = route.lower()
            if any(marker.lower() in lower_route for marker in EXTERNAL_DIRECT_PROVIDER_MARKERS):
                if "forbidden" not in " ".join(str(x).lower() for x in (forbidden or [])):
                    findings.append(f"{component}: route appears to include direct provider without forbidden fallback labeling")
        elif channel.get("external_llm_allowed") is False:
            local_only_components.append(component)
        else:
            findings.append(f"{component}: external_llm_allowed must be boolean")

    missing_components = sorted((HEADROOM_REQUIRED_COMPONENTS | {"Headroom"}) - set(components))
    if missing_components:
        findings.append("missing required components: " + ", ".join(missing_components))

    if findings:
        raise GuardrailError("Channel registry validation failed: " + "; ".join(findings))

    return ChannelRegistryValidation(
        status="ok",
        registry=str(registry_path),
        channel_count=len(channels),
        components=components,
        external_llm_components=external_llm_components,
        headroom_routed_components=headroom_routed_components,
        local_only_components=local_only_components,
        findings=[],
    )


def channel_registry_validation_to_markdown(report: ChannelRegistryValidation) -> str:
    lines = [
        "# Channel Registry Validation",
        "",
        f"Status: `{report.status}`",
        f"Registry: `{report.registry}`",
        f"Channels: `{report.channel_count}`",
        "",
        "## External LLM components",
        "",
    ]
    lines.extend(f"- {item}" for item in report.external_llm_components)
    lines.extend(["", "## Headroom-routed components", ""])
    lines.extend(f"- {item}" for item in report.headroom_routed_components)
    lines.extend(["", "## Local-only components", ""])
    lines.extend(f"- {item}" for item in report.local_only_components)
    lines.append("")
    return "\n".join(lines)
