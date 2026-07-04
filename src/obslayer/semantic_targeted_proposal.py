from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .graphify_embedding_handoff import _is_relative_to, _require_not_live
from .guardrails import GuardrailError, write_json


@dataclass(frozen=True)
class TargetedSemanticProposal:
    mode: str
    status: str
    proposal_id: str
    source_decision_packet: str
    group: str
    live_mutation_authorized: bool
    approval_manifest_created: bool
    targets: list[dict[str, Any]]
    candidate_paths: list[str]
    proposed_changes: list[str]
    safety: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _safe_decision_packet(path: str | Path) -> Path:
    packet = _require_not_live(path)
    allowed = _repo_root() / "out" / "proposals" / "semantic-candidate-decisions"
    if packet.name != "decision-packet.json" or not packet.is_file():
        raise GuardrailError(f"Expected decision-packet.json: {packet}")
    if not _is_relative_to(packet, allowed.resolve()):
        raise GuardrailError(f"decision packet must live under {allowed}: {packet}")
    return packet


def _safe_out_dir(path: str | Path) -> Path:
    out_dir = _require_not_live(path)
    allowed = _repo_root() / "out" / "proposals" / "semantic-targeted-proposals"
    if not _is_relative_to(out_dir, allowed.resolve()):
        raise GuardrailError(f"targeted semantic proposals must live under {allowed}: {out_dir}")
    return out_dir


def build_targeted_semantic_proposal(
    *, decision_packet_json: str | Path, group: str = "link_hygiene_reports", proposal_id: str | None = None
) -> TargetedSemanticProposal:
    packet_path = _safe_decision_packet(decision_packet_json)
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    if payload.get("mode") != "semantic-candidate-decision-packet":
        raise GuardrailError("source packet mode must be semantic-candidate-decision-packet")
    if payload.get("live_mutation_authorized") is not False:
        raise GuardrailError("source packet must not authorize live mutation")
    groups = {item.get("name"): item for item in payload.get("groups") or [] if isinstance(item, dict)}
    selected = groups.get(group)
    if not selected:
        raise GuardrailError(f"decision group not found: {group}")
    if selected.get("decision") != "promote-to-targeted-proposal":
        raise GuardrailError(f"decision group is not promotable to targeted proposal: {group}")

    paths = [str(path) for path in selected.get("paths") or [] if str(path).strip()]
    pid = proposal_id or f"semantic-targeted-{group}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    return TargetedSemanticProposal(
        mode="semantic-targeted-proposal",
        status="ready-for-operator-review",
        proposal_id=pid,
        source_decision_packet=str(packet_path),
        group=group,
        live_mutation_authorized=False,
        approval_manifest_created=False,
        targets=[],
        candidate_paths=paths,
        proposed_changes=[
            "Draft a dedicated link-hygiene review/index artifact from the listed historical reports.",
            "Keep the artifact proposal-only; do not edit live vault notes or create an approval manifest yet.",
            "Use this packet to choose exact documentation targets before any future target-diff proposal.",
        ],
        safety={
            "proposal_only": True,
            "targets_empty": True,
            "live_mutation_authorized": False,
            "approval_manifest_created": False,
            "source_group_promotable": True,
        },
    )


def targeted_semantic_proposal_to_markdown(proposal: TargetedSemanticProposal) -> str:
    lines = [
        "# Targeted semantic proposal",
        "",
        f"Proposal id: `{proposal.proposal_id}`",
        f"Status: `{proposal.status}`",
        f"Group: `{proposal.group}`",
        f"Source decision packet: `{proposal.source_decision_packet}`",
        "",
        "## Boundary",
        "",
        "- Proposal-only promotion from semantic decision packet.",
        "- No live vault mutation, edit targets, approval manifest, or backups are created.",
        "- Hermes/operator must choose exact targets before any future apply-capable proposal.",
        "",
        "## Proposed changes",
        "",
    ]
    lines.extend(f"- {item}" for item in proposal.proposed_changes)
    lines.extend(["", "## Candidate evidence paths", ""])
    lines.extend(f"- `{path}`" for path in proposal.candidate_paths)
    lines.extend(["", "## Safety", ""])
    lines.extend(f"- {key}: `{value}`" for key, value in proposal.safety.items())
    lines.append("")
    return "\n".join(lines)


def write_targeted_semantic_proposal(
    *, decision_packet_json: str | Path, out_dir: str | Path, group: str = "link_hygiene_reports", proposal_id: str | None = None
) -> dict[str, str]:
    proposal_dir = _safe_out_dir(out_dir)
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal = build_targeted_semantic_proposal(
        decision_packet_json=decision_packet_json, group=group, proposal_id=proposal_id
    )
    json_path = proposal_dir / "proposal.json"
    md_path = proposal_dir / "REPORT.md"
    write_json(json_path, {"created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **proposal.to_dict()})
    md_path.write_text(targeted_semantic_proposal_to_markdown(proposal), encoding="utf-8")
    return {
        "status": "ok",
        "proposal": str(json_path),
        "report": str(md_path),
        "candidate_paths": str(len(proposal.candidate_paths)),
        "targets": str(len(proposal.targets)),
    }
