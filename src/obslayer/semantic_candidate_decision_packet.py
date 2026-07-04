from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .graphify_embedding_handoff import _is_relative_to, _require_not_live
from .guardrails import GuardrailError, write_json


@dataclass(frozen=True)
class CandidateDecisionGroup:
    name: str
    decision: str
    rationale: str
    candidate_count: int
    paths: list[str]
    queries: list[str]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateDecisionPacket:
    mode: str
    status: str
    source_proposal: str
    packet_id: str
    live_mutation_authorized: bool
    targets: list[dict[str, Any]]
    groups: list[CandidateDecisionGroup]
    summary: dict[str, Any]
    safety: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["groups"] = [group.to_dict() for group in self.groups]
        return data


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _safe_semantic_proposal_json(path: str | Path) -> Path:
    proposal = _require_not_live(path)
    allowed = _repo_root() / "out" / "proposals" / "semantic-query-reports"
    if proposal.name != "proposal.json" or not proposal.is_file():
        raise GuardrailError(f"Expected semantic proposal.json: {proposal}")
    if not _is_relative_to(proposal, allowed.resolve()):
        raise GuardrailError(f"semantic proposal must live under {allowed}: {proposal}")
    return proposal


def _safe_decision_packet_out_dir(path: str | Path) -> Path:
    out_dir = _require_not_live(path)
    allowed = _repo_root() / "out" / "proposals" / "semantic-candidate-decisions"
    if not _is_relative_to(out_dir, allowed.resolve()):
        raise GuardrailError(f"Semantic candidate decision packets must live under {allowed}: {out_dir}")
    return out_dir


def _group_name(candidate: dict[str, Any]) -> str:
    queries = " ".join(str(item).lower() for item in candidate.get("queries") or [])
    path = str(candidate.get("path") or "").lower()
    if "link hygiene" in queries or "broken link" in queries or "hygiene" in path:
        return "link_hygiene_reports"
    if "nanobot" in queries or "codex" in queries or "workspace registry" in path:
        return "nanobot_orchestration_context"
    if "graphify" in queries or "graphify" in path or "cross repo" in path:
        return "graphify_context"
    if "approval manifest" in queries or "safety boundary" in queries or "acceptance" in path:
        return "approval_safety_context"
    return "needs_manual_triage"


def _decision_for_group(name: str) -> tuple[str, str, str]:
    if name == "link_hygiene_reports":
        return (
            "promote-to-targeted-proposal",
            "Multiple historical hygiene reports are clustered around broken-link cleanup; this is the best candidate "
            "for a narrow operator-reviewed promotion.",
            "Create a small target-diff proposal that updates only the review/dashboard documentation or "
            "a dedicated hygiene index; do not mutate vault notes automatically.",
        )
    if name == "graphify_context":
        return (
            "keep-as-context",
            "Graphify hits are useful orientation material, but the current packet does not identify a specific edit target.",
            "Use these paths as evidence for future Graphify/semantic roadmap packets, not as direct apply targets.",
        )
    if name == "approval_safety_context":
        return (
            "keep-as-guardrail-evidence",
            "Approval/safety hits validate the existing apply boundary and should remain evidence unless "
            "a concrete stale statement is found.",
            "Reference these notes when building approval-manifest tooling; no immediate target-diff promotion.",
        )
    if name == "nanobot_orchestration_context":
        return (
            "promote-to-spec-kit-followup",
            "Nanobot/Headroom/Codex orchestration is an active workstream, but changes must stay in "
            "repo spec-kit and read-only scout policy first.",
            "Open a repo-only follow-up for route/enforcement checks; no live vault, service, auth, or cron mutation.",
        )
    return (
        "manual-review-only",
        "The candidate cluster is not specific enough for safe automated promotion.",
        "Leave as review input until an operator selects an exact target and desired diff.",
    )


def build_candidate_decision_packet(*, semantic_proposal_json: str | Path, packet_id: str | None = None) -> CandidateDecisionPacket:
    proposal_path = _safe_semantic_proposal_json(semantic_proposal_json)
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    if payload.get("mode") != "semantic-query-proposal-only-report":
        raise GuardrailError("source proposal mode must be semantic-query-proposal-only-report")
    if payload.get("live_mutation_authorized") is not False:
        raise GuardrailError("source proposal must not authorize live mutation")
    if payload.get("targets") not in ([], None):
        raise GuardrailError("source semantic proposal must not contain edit targets")

    grouped: dict[str, list[dict[str, Any]]] = {}
    for candidate in payload.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        grouped.setdefault(_group_name(candidate), []).append(candidate)

    groups: list[CandidateDecisionGroup] = []
    for name in sorted(grouped):
        candidates = sorted(
            grouped[name],
            key=lambda item: (int(item.get("hit_count") or 0), float(item.get("best_score") or 0.0), str(item.get("path") or "")),
            reverse=True,
        )
        decision, rationale, next_action = _decision_for_group(name)
        paths = [str(item.get("path") or "") for item in candidates if item.get("path")]
        query_set = sorted({str(query) for item in candidates for query in (item.get("queries") or []) if str(query).strip()})
        groups.append(
            CandidateDecisionGroup(
                name=name,
                decision=decision,
                rationale=rationale,
                candidate_count=len(candidates),
                paths=paths[:10],
                queries=query_set,
                next_action=next_action,
            )
        )

    pid = packet_id or f"semantic-candidate-decision-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    promote_count = sum(1 for group in groups if group.decision.startswith("promote"))
    return CandidateDecisionPacket(
        mode="semantic-candidate-decision-packet",
        status="ready-for-operator-review",
        source_proposal=str(proposal_path),
        packet_id=pid,
        live_mutation_authorized=False,
        targets=[],
        groups=groups,
        summary={
            "source_candidates": len(payload.get("candidates") or []),
            "decision_groups": len(groups),
            "promote_groups": promote_count,
            "recommended_first_step": "link_hygiene_reports"
            if any(group.name == "link_hygiene_reports" for group in groups)
            else "manual_review",
        },
        safety={
            "proposal_only": True,
            "targets_empty": True,
            "live_mutation_authorized": False,
            "no_approval_manifest": True,
            "repo_only_decision_packet": True,
        },
    )


def candidate_decision_packet_to_markdown(packet: CandidateDecisionPacket) -> str:
    lines = [
        "# Semantic candidate decision packet",
        "",
        f"Packet id: `{packet.packet_id}`",
        f"Status: `{packet.status}`",
        f"Source proposal: `{packet.source_proposal}`",
        "",
        "## Boundary",
        "",
        "- This packet classifies semantic candidates into operator decisions.",
        "- It does not create edit targets, approval manifests, backups, or live-vault mutations.",
        "- Promotion means a later, separate targeted proposal may be drafted and reviewed.",
        "",
        "## Summary",
        "",
    ]
    for key, value in packet.summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Decision groups",
            "",
            "| group | decision | candidates | next action |",
            "|---|---|---:|---|",
        ]
    )
    for group in packet.groups:
        lines.append(f"| `{group.name}` | `{group.decision}` | {group.candidate_count} | {group.next_action} |")
    for group in packet.groups:
        lines.extend(["", f"### {group.name}", "", f"Decision: `{group.decision}`", "", group.rationale, "", "Top paths:"])
        for path in group.paths:
            lines.append(f"- `{path}`")
        lines.append("")
        lines.append("Queries:")
        for query in group.queries:
            lines.append(f"- {query}")
    lines.extend(["", "## Safety", ""])
    for key, value in packet.safety.items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_candidate_decision_packet(
    *, semantic_proposal_json: str | Path, out_dir: str | Path, packet_id: str | None = None
) -> dict[str, str]:
    packet_dir = _safe_decision_packet_out_dir(out_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet = build_candidate_decision_packet(semantic_proposal_json=semantic_proposal_json, packet_id=packet_id)
    json_path = packet_dir / "decision-packet.json"
    md_path = packet_dir / "REPORT.md"
    write_json(json_path, {"created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **packet.to_dict()})
    md_path.write_text(candidate_decision_packet_to_markdown(packet), encoding="utf-8")
    return {
        "status": "ok",
        "decision_packet": str(json_path),
        "report": str(md_path),
        "groups": str(len(packet.groups)),
        "targets": str(len(packet.targets)),
    }
