from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .channel_registry import load_channel_registry, validate_channel_registry
from .guardrails import GuardrailError

NANOBOT_BRIDGE = "http://127.0.0.1:8787/backend-api/codex/responses"
CANONICAL_SHAPE_MARKER = "backend codex bridge only"


@dataclass(frozen=True)
class EndpointProbe:
    name: str
    url: str
    expected: str
    status: str
    http_status: int | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LlmChannelSmoke:
    status: str
    generated_utc: str
    registry: str
    assertions: dict[str, bool]
    probes: list[EndpointProbe]
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["probes"] = [probe.to_dict() for probe in self.probes]
        return payload


def _get_channel(payload: dict[str, Any], component: str) -> dict[str, Any]:
    channels = payload.get("channels")
    if not isinstance(channels, list):
        raise GuardrailError("channel registry has no channels list")
    for channel in channels:
        if isinstance(channel, dict) and channel.get("component") == component:
            return channel
    raise GuardrailError(f"channel not found: {component}")


def _probe_url(name: str, url: str, expected: str, timeout: float = 5.0) -> EndpointProbe:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(512).decode("utf-8", "replace")
            return EndpointProbe(
                name=name,
                url=url,
                expected=expected,
                status="ok" if 200 <= response.status < 300 else "unexpected",
                http_status=response.status,
                detail=body[:160],
            )
    except urllib.error.HTTPError as exc:
        return EndpointProbe(name=name, url=url, expected=expected, status="http-error", http_status=exc.code, detail="")
    except OSError as exc:
        return EndpointProbe(name=name, url=url, expected=expected, status="unreachable", detail=str(exc)[:160])


def run_llm_channel_smoke(
    registry_path: str | Path,
    *,
    live_probes: bool = False,
    generated_utc: str | None = None,
) -> LlmChannelSmoke:
    registry_validation = validate_channel_registry(registry_path)
    registry = Path(registry_path).resolve()
    payload = load_channel_registry(registry)
    findings: list[str] = []

    nanobot = _get_channel(payload, "Nanobot Hermes communicator")
    codex = _get_channel(payload, "Codex CLI")
    graphify = _get_channel(payload, "Graphify")
    gateway = _get_channel(payload, "Nanobot read-only evidence gateway")

    nanobot_route = str(nanobot.get("required_route", ""))
    nanobot_shape = str(nanobot.get("accepted_endpoint_shape", ""))
    codex_route = str(codex.get("required_route", ""))
    graphify_route = str(graphify.get("required_route", ""))
    gateway_route = str(gateway.get("required_route", ""))

    assertions = {
        "registry_valid": registry_validation.status == "ok",
        "external_llm_default_headroom": "Headroom" in str(payload.get("global_rule", "")),
        "codex_cli_headroom_route": "127.0.0.1:8787" in codex_route or "headroom" in codex_route.lower(),
        "graphify_headroom_route": "headroom" in graphify_route.lower(),
        "nanobot_uses_backend_codex_bridge": NANOBOT_BRIDGE in nanobot_route,
        "nanobot_uses_canonical_backend_only": CANONICAL_SHAPE_MARKER in nanobot_shape.lower(),
        "evidence_gateway_local_read_only": (
            "127.0.0.1:18791" in gateway_route
            and gateway.get("external_llm_allowed") is False
            and gateway.get("may_mutate") is False
        ),
        "local_ollama_embedding_exception_documented": "Ollama local" in graphify_route,
    }

    for name, ok in assertions.items():
        if not ok:
            findings.append(f"assertion failed: {name}")

    probes: list[EndpointProbe] = []
    if live_probes:
        probes.append(_probe_url("headroom_health", "http://127.0.0.1:8787/health", "2xx healthy local proxy"))
        probes.append(_probe_url("nanobot_evidence_gateway_health", "http://127.0.0.1:18791/health", "2xx read-only gateway"))
    else:
        probes.append(EndpointProbe("headroom_health", "http://127.0.0.1:8787/health", "not probed in offline mode", "skipped"))
        probes.append(
            EndpointProbe(
                "nanobot_evidence_gateway_health",
                "http://127.0.0.1:18791/health",
                "not probed in offline mode",
                "skipped",
            )
        )

    for probe in probes:
        if probe.status not in {"ok", "skipped"}:
            findings.append(f"probe failed: {probe.name} status={probe.status} http={probe.http_status}")

    return LlmChannelSmoke(
        status="ok" if not findings else "failed",
        generated_utc=generated_utc or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        registry=str(registry),
        assertions=assertions,
        probes=probes,
        findings=findings,
    )


def llm_channel_smoke_to_markdown(report: LlmChannelSmoke) -> str:
    lines = [
        "# LLM Channel Smoke",
        "",
        f"Status: `{report.status}`",
        f"Generated UTC: `{report.generated_utc}`",
        f"Registry: `{report.registry}`",
        "",
        "## Assertions",
        "",
    ]
    for name, ok in report.assertions.items():
        lines.append(f"- `{name}`: `{str(ok).lower()}`")
    lines.extend(["", "## Endpoint probes", ""])
    for probe in report.probes:
        http = "" if probe.http_status is None else f" http={probe.http_status}"
        lines.append(f"- `{probe.name}`: `{probe.status}`{http} — `{probe.url}`")
    if report.findings:
        lines.extend(["", "## Findings", ""])
        lines.extend(f"- {finding}" for finding in report.findings)
    lines.append("")
    return "\n".join(lines)
