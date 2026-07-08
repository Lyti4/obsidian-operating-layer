from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError, write_json

MODE = "obslayer.operator-review-packet.v1"


@dataclass(frozen=True)
class OperatorReviewItem:
    source_id: str
    route: str
    confidence: float | None
    reason_codes: list[str]
    old_link: str
    proposed_link: str
    policy_tag: str
    rollback_key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorReviewPacket:
    mode: str
    status: str
    created_at: str
    source_proposal_packet: str
    source_readiness_packet: str | None
    review_items: list[OperatorReviewItem]
    held_count: int
    findings: list[str]
    next_safe_step: str
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["review_items"] = [item.to_dict() for item in self.review_items]
        return payload


def _repo_root(repo: str | Path | None = None) -> Path:
    return Path(repo).expanduser().resolve() if repo is not None else Path.cwd().resolve()


def _require_under_repo_out(path: str | Path, repo: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    out_root = (repo / "out").resolve()
    try:
        resolved.relative_to(out_root)
    except ValueError as exc:
        raise GuardrailError(f"operator review inputs/outputs must live under repo out/: {resolved}") from exc
    return resolved


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardrailError(f"expected JSON object: {path}")
    return payload


def _as_reason_codes(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def _proposal_text(raw: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _operator_review_item(raw: dict[str, Any], index: int) -> OperatorReviewItem:
    confidence_raw = raw.get("confidence") or raw.get("score")
    confidence = float(confidence_raw) if isinstance(confidence_raw, (int, float)) else None
    return OperatorReviewItem(
        source_id=str(raw.get("id") or raw.get("source_id") or f"proposal-{index}"),
        route=str(raw.get("route") or raw.get("allowed_next_action") or "auto-propose"),
        confidence=confidence,
        reason_codes=_as_reason_codes(raw.get("reason_codes") or raw.get("reasons")),
        old_link=_proposal_text(raw, "old_link", "source", "old_text"),
        proposed_link=_proposal_text(raw, "proposed_link", "target", "new_text"),
        policy_tag=_proposal_text(raw, "policy_tag", "policy") or "operator-review-required",
        rollback_key=_proposal_text(raw, "rollback_key") or f"operator-review-{index}",
    )


def _is_grouped_proposal_packet(proposal: dict[str, Any]) -> bool:
    targets = proposal.get("targets")
    if not isinstance(targets, list) or not targets:
        return False
    return any(
        isinstance(target, dict)
        and isinstance(target.get("evidence"), dict)
        and isinstance(target["evidence"].get("grouped_replacements"), list)
        for target in targets
    )


def _is_manual_review_selector_packet(proposal: dict[str, Any]) -> bool:
    return (
        proposal.get("schema") == "obslayer.manual-review-selector.v1"
        or proposal.get("mode") == "obslayer.manual-review-selector.v1"
        or proposal.get("packet_type") == "manual_review_evidence_only"
    )


def _wiki_link(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped.startswith("[[") and stripped.endswith("]]"):
        return stripped
    if stripped.endswith(".md"):
        stripped = stripped[:-3]
    return f"[[{stripped}]]"


def _manual_selector_review_items(proposal: dict[str, Any], findings: list[str]) -> list[dict[str, Any]]:
    raw_items = proposal.get("review_items")
    if not isinstance(raw_items, list):
        findings.append("manual selector review_items must be a list")
        return []

    status = proposal.get("status")
    if status not in ("ready_for_manual_review", "no_candidate"):
        findings.append("manual selector status must be ready_for_manual_review or no_candidate")

    converted: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            findings.append(f"review_items[{index - 1}] must be an object")
            continue
        _check_no_apply_authority(raw, findings, prefix=f"review_items[{index - 1}]")
        queue = raw.get("review_queue")
        source_id = ""
        if isinstance(queue, dict):
            source_id = str(queue.get("item_id") or "")
        old_link = _wiki_link(str(raw.get("old_link") or ""))
        proposed_link = _wiki_link(str(raw.get("proposed_path") or raw.get("top_candidate_path") or ""))
        converted.append(
            {
                "id": source_id or str(raw.get("source") or f"manual-selector-{index}"),
                "route": str(raw.get("selection_mode") or raw.get("route_hint") or "manual-review-selector"),
                "confidence": raw.get("confidence"),
                "reason_codes": raw.get("reason_codes"),
                "old_link": old_link,
                "proposed_link": proposed_link,
                "policy_tag": str(raw.get("policy_tag") or "manual-review-only"),
                "rollback_key": source_id or f"manual-selector-review-{index}",
            }
        )
    return converted


def _check_no_apply_authority(value: Any, findings: list[str], *, prefix: str = "source proposal packet") -> None:
    if not isinstance(value, dict):
        return
    if value.get("live_mutation_authorized") not in (None, False):
        findings.append(f"{prefix} must not authorize live mutation")
    if value.get("approval_manifest_created") not in (None, False):
        findings.append(f"{prefix} must not create approval manifests")
    if value.get("approval_manifest_authority") not in (None, False):
        findings.append(f"{prefix} must not have approval manifest authority")
    if value.get("apply_authority") not in (None, "none", False):
        findings.append(f"{prefix} must not have apply authority")


def _grouped_review_items(proposal: dict[str, Any], findings: list[str]) -> list[dict[str, Any]]:
    raw_items: list[dict[str, Any]] = []
    targets = proposal.get("targets")
    if not isinstance(targets, list):
        findings.append("grouped proposal targets must be a list")
        return raw_items

    for target_index, target in enumerate(targets, start=1):
        if not isinstance(target, dict):
            findings.append(f"targets[{target_index - 1}] must be an object")
            continue
        _check_no_apply_authority(target, findings, prefix=f"targets[{target_index - 1}]")
        target_path = str(target.get("path") or f"target-{target_index}")
        evidence = target.get("evidence")
        if not isinstance(evidence, dict):
            findings.append(f"targets[{target_index - 1}].evidence must be an object")
            continue
        _check_no_apply_authority(evidence, findings, prefix=f"targets[{target_index - 1}].evidence")
        replacements = evidence.get("grouped_replacements")
        if not isinstance(replacements, list):
            findings.append(f"targets[{target_index - 1}].evidence.grouped_replacements must be a list")
            continue
        for replacement_index, replacement in enumerate(replacements, start=1):
            if not isinstance(replacement, dict):
                findings.append(
                    f"targets[{target_index - 1}].evidence.grouped_replacements[{replacement_index - 1}] must be an object"
                )
                continue
            _check_no_apply_authority(
                replacement,
                findings,
                prefix=f"targets[{target_index - 1}].evidence.grouped_replacements[{replacement_index - 1}]",
            )
            replacement_evidence = replacement.get("evidence")
            if isinstance(replacement_evidence, dict):
                _check_no_apply_authority(
                    replacement_evidence,
                    findings,
                    prefix=(
                        f"targets[{target_index - 1}].evidence.grouped_replacements"
                        f"[{replacement_index - 1}].evidence"
                    ),
                )
            source_reason = ""
            source_decision = ""
            if isinstance(replacement_evidence, dict):
                source_reason = str(replacement_evidence.get("source_reason") or "")
                source_decision = str(replacement_evidence.get("source_decision") or "")
            raw_items.append(
                {
                    "id": f"{target_path}#{replacement_index}",
                    "route": source_decision or "grouped-proposal",
                    "reason_codes": [source_reason] if source_reason else [],
                    "old_link": replacement.get("old_text"),
                    "proposed_link": replacement.get("new_text"),
                    "policy_tag": "operator-review-required",
                    "rollback_key": f"grouped-review-{target_index}-{replacement_index}",
                }
            )
    return raw_items


def build_operator_review_packet(
    *,
    repo: str | Path | None = None,
    proposal_packet: str | Path,
    readiness_packet: str | Path | None = None,
    max_review_items: int = 5,
) -> OperatorReviewPacket:
    """Build a human review packet from dry-run proposal evidence only.

    The packet is deliberately not an approval manifest and never grants apply
    authority. Empty dry-run proposals produce a no-candidate checkpoint instead
    of asking a human to approve nothing.
    """

    repo_path = _repo_root(repo)
    proposal_path = _require_under_repo_out(proposal_packet, repo_path)
    proposal = _load_object(proposal_path)
    is_grouped_proposal = _is_grouped_proposal_packet(proposal)
    is_manual_selector = _is_manual_review_selector_packet(proposal)

    findings: list[str] = []
    if is_grouped_proposal or is_manual_selector:
        _check_no_apply_authority(proposal, findings, prefix="source proposal packet")
    else:
        if proposal.get("live_mutation_authorized") is not False:
            findings.append("source proposal packet must set live_mutation_authorized=false")
        if proposal.get("approval_manifest_created") is not False:
            findings.append("source proposal packet must set approval_manifest_created=false")
        if proposal.get("approval_manifest_authority") not in (None, False):
            findings.append("source proposal packet must not have approval manifest authority")
        if proposal.get("apply_authority") not in (None, "none", False):
            findings.append("source proposal packet must not have apply authority")
    if proposal.get("targets") not in (None, []) and not (is_grouped_proposal or is_manual_selector):
        findings.append("source proposal packet must not expose live targets")
    _check_no_apply_authority(proposal.get("summary"), findings, prefix="source proposal packet summary")

    readiness_path_text: str | None = None
    if readiness_packet is not None:
        readiness_path = _require_under_repo_out(readiness_packet, repo_path)
        readiness = _load_object(readiness_path)
        readiness_path_text = str(readiness_path)
        if readiness.get("behavior") not in (None, "readiness-only/evidence-only"):
            findings.append("readiness packet behavior must be readiness-only/evidence-only")
        if readiness.get("safety") and isinstance(readiness["safety"], dict):
            safety = readiness["safety"]
            if safety.get("live_mutation_authorized") not in (None, False):
                findings.append("readiness packet safety must not authorize live mutation")
            if safety.get("apply_authority") not in (None, "none", False):
                findings.append("readiness packet safety must not grant apply authority")

    if is_grouped_proposal:
        raw_proposals = _grouped_review_items(proposal, findings)
    elif is_manual_selector:
        raw_proposals = _manual_selector_review_items(proposal, findings)
    else:
        raw_proposals = proposal.get("dry_run_proposals")
        if not isinstance(raw_proposals, list):
            findings.append("dry_run_proposals must be a list")
            raw_proposals = []

    raw_held = proposal.get("held_for_review")
    held_count = len(raw_held) if isinstance(raw_held, list) else 0

    if max_review_items < 1:
        findings.append("max_review_items must be positive")
        max_review_items = 1

    review_items: list[OperatorReviewItem] = []
    for index, raw in enumerate(raw_proposals[:max_review_items], start=1):
        if not isinstance(raw, dict):
            findings.append(f"dry_run_proposals[{index - 1}] must be an object")
            continue
        item = _operator_review_item(raw, index)
        if not item.old_link or not item.proposed_link:
            findings.append(f"dry_run_proposals[{index - 1}] must include old/proposed link text")
        review_items.append(item)

    if findings:
        status = "blocked"
        next_safe_step = "fix evidence packet before human review"
    elif not review_items:
        status = "no_candidate"
        next_safe_step = "return to scoring or manual candidate selection; do not request live approval"
    else:
        status = "ready_for_human_review"
        next_safe_step = "ask operator to review this packet; create approval manifest only after explicit approval"

    return OperatorReviewPacket(
        mode=MODE,
        status=status,
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        source_proposal_packet=str(proposal_path),
        source_readiness_packet=readiness_path_text,
        review_items=review_items,
        held_count=held_count,
        findings=findings,
        next_safe_step=next_safe_step,
        safety={
            "live_mutation_authorized": False,
            "approval_manifest_created": False,
            "approval_manifest_authority": False,
            "target_paths": [],
            "apply_authority": "none",
        },
    )


def operator_review_packet_to_markdown(packet: OperatorReviewPacket) -> str:
    lines = [
        "# Operator Review Packet",
        "",
        f"Status: `{packet.status}`",
        f"Mode: `{packet.mode}`",
        f"Source proposal packet: `{packet.source_proposal_packet}`",
        f"Source readiness packet: `{packet.source_readiness_packet or ''}`",
        "",
        "## Safety",
        "",
        "- live mutation authorized: `false`",
        "- approval manifest created: `false`",
        "- apply authority: `none`",
        "- target paths: `[]`",
        "",
        "## Review items",
        "",
    ]
    if packet.review_items:
        for item in packet.review_items:
            lines.extend(
                [
                    f"- `{item.source_id}`: `{item.old_link}` -> `{item.proposed_link}`",
                    f"  - route: `{item.route}`",
                    f"  - confidence: `{item.confidence}`",
                    f"  - reasons: `{', '.join(item.reason_codes)}`",
                    f"  - policy: `{item.policy_tag}`",
                    f"  - rollback key: `{item.rollback_key}`",
                ]
            )
    else:
        lines.append("No operator-review candidates were emitted by the source proposal packet.")
    lines.extend(["", "## Findings", ""])
    if packet.findings:
        lines.extend(f"- {finding}" for finding in packet.findings)
    else:
        lines.append("- none")
    lines.extend(["", "## Next safe step", "", packet.next_safe_step, ""])
    return "\n".join(lines)


def write_operator_review_packet(packet: OperatorReviewPacket, out_dir: str | Path) -> tuple[Path, Path]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    json_path = out_path / "operator-review-packet.json"
    report_path = out_path / "REPORT.md"
    write_json(json_path, packet.to_dict())
    report_path.write_text(operator_review_packet_to_markdown(packet), encoding="utf-8")
    return json_path, report_path
