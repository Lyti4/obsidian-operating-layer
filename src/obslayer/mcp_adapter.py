from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError, is_protected_relative, load_json, utc_stamp, write_json

ALLOWED_MCP_CAPABILITIES = {"read", "search", "graph", "metadata-read", "propose", "write-request"}
REQUIRED_FORBIDDEN_CAPABILITIES = {
    "write-direct",
    "delete-direct",
    "move-direct",
    "merge-direct",
    "patch-direct",
    "execute-live-mutation",
    "secret-read",
}
DANGEROUS_TOOL_TOKENS = (
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
    "mkdir",
    "rmdir",
    "secret",
    "env",
    "token",
)
SAFE_TOOL_TOKENS = ("read", "search", "find", "list", "graph", "link", "backlink", "tag", "metadata", "frontmatter")


@dataclass(frozen=True)
class McpAdapterEvaluation:
    adapter: str
    source_id: str
    sandbox_vault: str
    allowed_capabilities: list[str]
    forbidden_capabilities: list[str]
    direct_write_disabled: bool
    sandbox_required: bool
    write_policy: str
    findings: list[dict[str, Any]]
    artifacts: dict[str, str]
    verification: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_mcp_adapter_record(path: str | Path) -> dict[str, Any]:
    record = load_json(path)
    if record.get("kind") != "mcp-server":
        raise GuardrailError(f"Adapter record is not an MCP server: {record.get('kind')}")
    if record.get("direct_write_enabled") is not False:
        raise GuardrailError("MCP adapter must set direct_write_enabled=false")
    if record.get("sandbox_required") is not True:
        raise GuardrailError("MCP adapter must require sandbox evaluation")

    capabilities = set(record.get("capabilities", []))
    unknown_allowed = capabilities - ALLOWED_MCP_CAPABILITIES
    if unknown_allowed:
        raise GuardrailError(f"MCP adapter has unsupported allowed capabilities: {sorted(unknown_allowed)}")
    dangerous_as_allowed = capabilities & REQUIRED_FORBIDDEN_CAPABILITIES
    if dangerous_as_allowed:
        raise GuardrailError(f"MCP adapter exposes dangerous capabilities as allowed: {sorted(dangerous_as_allowed)}")

    forbidden = set(record.get("forbidden_capabilities", []))
    missing = REQUIRED_FORBIDDEN_CAPABILITIES - forbidden
    if missing:
        raise GuardrailError(f"MCP adapter missing required forbidden capabilities: {sorted(missing)}")
    return record


def classify_mcp_tool(tool_name: str) -> str:
    normalized = tool_name.lower().replace("-", "_")
    if any(token in normalized for token in DANGEROUS_TOOL_TOKENS):
        return "refuse"
    if any(token in normalized for token in SAFE_TOOL_TOKENS):
        return "allow-readonly"
    return "review-required"


def normalize_mcp_tool_request(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    arguments = arguments or {}
    decision = classify_mcp_tool(tool_name)
    payload: dict[str, Any] = {
        "tool": tool_name,
        "decision": decision,
        "arguments_recorded": bool(arguments),
        "executed": False,
    }
    if decision == "allow-readonly":
        payload.update(
            {
                "status": "allowed-for-sandbox-readonly",
                "proposal_required": False,
                "reason": "Tool name matches read/search/graph/metadata policy; wrapper still does not execute it in this slice.",
            }
        )
    elif decision == "refuse":
        payload.update(
            {
                "status": "refused",
                "proposal_required": True,
                "reason": "Write/delete/move/secret-like MCP tool names are blocked and must become obslayer proposals.",
            }
        )
    else:
        payload.update(
            {
                "status": "manual-review-required",
                "proposal_required": True,
                "reason": "Unknown MCP tool names are denied by default until mapped to an explicit safe capability.",
            }
        )
    return payload


def _safe_sandbox_vault(path: str | Path) -> Path:
    vault = Path(path).expanduser().resolve()
    if not vault.exists() or not vault.is_dir():
        raise GuardrailError(f"Sandbox vault does not exist or is not a directory: {vault}")
    if is_protected_relative(vault.name):
        raise GuardrailError(f"Sandbox vault name is protected: {vault.name}")
    return vault


def build_mcp_adapter_evaluation(
    *,
    adapter_record: str | Path,
    sandbox_vault: str | Path,
    probe_tools: list[str] | None = None,
    artifact_root: str | Path | None = None,
) -> McpAdapterEvaluation:
    record = load_mcp_adapter_record(adapter_record)
    sandbox = _safe_sandbox_vault(sandbox_vault)
    probes = probe_tools or ["read_note", "search_notes", "graph_links", "write_note", "delete_note"]
    normalized = [normalize_mcp_tool_request(tool) for tool in probes]
    direct_write_disabled = all(item["decision"] != "allow-write" and item["executed"] is False for item in normalized)

    artifacts: dict[str, str] = {}
    if artifact_root is not None:
        root = Path(artifact_root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        stem = record["name"].replace("/", "-").replace(" ", "-")
        artifacts = {
            "json_report": str(root / f"mcp-adapter-evaluation-{stem}-{utc_stamp()}.json"),
        }

    return McpAdapterEvaluation(
        adapter=record["name"],
        source_id=record["source"]["id"],
        sandbox_vault=str(sandbox),
        allowed_capabilities=sorted(record.get("capabilities", [])),
        forbidden_capabilities=sorted(record.get("forbidden_capabilities", [])),
        direct_write_disabled=direct_write_disabled,
        sandbox_required=True,
        write_policy="refuse-direct-mutation-and-convert-to-obslayer-proposal",
        findings=normalized,
        artifacts=artifacts,
        verification={
            "sandboxed": True,
            "direct_write_disabled": direct_write_disabled,
            "dangerous_tools_refused": all(item["status"] == "refused" for item in normalized if item["decision"] == "refuse"),
            "unknown_tools_require_review": all(
                item["status"] == "manual-review-required" for item in normalized if item["decision"] == "review-required"
            ),
        },
    )


def write_mcp_adapter_evaluation(evaluation: McpAdapterEvaluation, out: str | Path) -> None:
    write_json(out, {"status": "ok", **evaluation.to_dict()})


def evaluation_to_markdown(evaluation: McpAdapterEvaluation) -> str:
    lines = [
        f"# MCP adapter evaluation: {evaluation.adapter}",
        "",
        f"- source: `{evaluation.source_id}`",
        f"- sandbox_vault: `{evaluation.sandbox_vault}`",
        f"- direct_write_disabled: `{evaluation.direct_write_disabled}`",
        f"- write_policy: `{evaluation.write_policy}`",
        "",
        "## Tool policy probes",
    ]
    for finding in evaluation.findings:
        lines.append(f"- `{finding['tool']}` → `{finding['status']}`; proposal_required={finding['proposal_required']}")
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
