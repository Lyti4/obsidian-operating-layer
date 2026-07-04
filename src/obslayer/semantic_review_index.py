from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError


@dataclass(frozen=True)
class ReviewIndexItem:
    rank: int
    path: str
    review_reason: str
    proposed_disposition: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticReviewIndex:
    status: str
    mode: str
    created_at: str
    source_proposal: str
    group: str
    item_count: int
    live_mutation_authorized: bool
    approval_manifest_created: bool
    items: list[ReviewIndexItem]
    next_safe_step: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["items"] = [item.to_dict() for item in self.items]
        return payload


def _load_targeted_proposal(path: str | Path) -> tuple[Path, dict[str, Any]]:
    proposal_path = Path(path).expanduser().resolve()
    try:
        payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GuardrailError(f"Invalid targeted proposal JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GuardrailError("Targeted proposal must be a JSON object")
    if payload.get("mode") != "semantic-targeted-proposal":
        raise GuardrailError("Expected mode=semantic-targeted-proposal")
    if payload.get("live_mutation_authorized") is not False:
        raise GuardrailError("Refusing review index: live mutation must be false")
    if payload.get("approval_manifest_created") is not False:
        raise GuardrailError("Refusing review index: approval manifest must not already be created")
    targets = payload.get("targets", [])
    if targets != []:
        raise GuardrailError("Refusing review index: targeted proposal must have no edit targets")
    candidate_paths = payload.get("candidate_paths", [])
    if not isinstance(candidate_paths, list) or not candidate_paths:
        raise GuardrailError("Targeted proposal must include candidate_paths")
    if not all(isinstance(item, str) and item.strip() for item in candidate_paths):
        raise GuardrailError("candidate_paths must be non-empty strings")
    return proposal_path, payload


def build_semantic_review_index(
    targeted_proposal: str | Path,
    *,
    created_at: str | None = None,
) -> SemanticReviewIndex:
    proposal_path, proposal = _load_targeted_proposal(targeted_proposal)
    candidate_paths = [str(path) for path in proposal["candidate_paths"]]
    group = str(proposal.get("group") or "unknown")

    items = [
        ReviewIndexItem(
            rank=index,
            path=path,
            review_reason=f"Candidate promoted from semantic decision group `{group}`.",
            proposed_disposition="review-source-evidence-before-any-target-diff",
        )
        for index, path in enumerate(candidate_paths, 1)
    ]
    return SemanticReviewIndex(
        status="ready-for-operator-review",
        mode="semantic-review-index",
        created_at=created_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        source_proposal=str(proposal_path),
        group=group,
        item_count=len(items),
        live_mutation_authorized=False,
        approval_manifest_created=False,
        items=items,
        next_safe_step="Read candidate source evidence and choose exact repo documentation target before any target-diff proposal.",
    )


def semantic_review_index_to_markdown(index: SemanticReviewIndex) -> str:
    lines = [
        "# Semantic Review Index",
        "",
        f"Status: `{index.status}`",
        f"Mode: `{index.mode}`",
        f"Group: `{index.group}`",
        f"Created UTC: `{index.created_at}`",
        f"Source proposal: `{index.source_proposal}`",
        f"Items: `{index.item_count}`",
        f"Live mutation authorized: `{index.live_mutation_authorized}`",
        f"Approval manifest created: `{index.approval_manifest_created}`",
        "",
        "## Review items",
        "",
        "| rank | proposed disposition | candidate source path |",
        "|---:|---|---|",
    ]
    for item in index.items:
        path = item.path.replace("|", "\\|")
        lines.append(f"| {item.rank} | `{item.proposed_disposition}` | `{path}` |")
    lines.extend(
        [
            "",
            "## Safety boundary",
            "",
            "- Candidate source paths are evidence inputs only.",
            "- This artifact does not authorize live vault edits.",
            "- No approval manifest was created.",
            "- Any future target-diff proposal must be separate and explicitly approved before apply.",
            "",
            "## Next safe step",
            "",
            index.next_safe_step,
            "",
        ]
    )
    return "\n".join(lines)
