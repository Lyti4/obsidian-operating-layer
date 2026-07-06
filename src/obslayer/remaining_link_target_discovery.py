from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Mapping

MODE = "obslayer.remaining-link-target-discovery.v1"
DISCOVERY_CLASSES = {
    "real_broken_needs_target_discovery",
    "ambiguous_needs_operator_disambiguation",
}
SUPPRESSED_CLASSES = {
    "generated_report_auto_keep",
    "protected_cross_vault_manual",
    "graphify_exact_path_preferred_no_apply",
}
PROTECTED_PATH_PARTS = {".obsidian", "_Backups", "_Archive", ".trash"}


@dataclass(frozen=True)
class TargetDiscoveryCandidate:
    path: str
    title: str
    score: float
    reason_codes: list[str]
    safety_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TargetDiscoveryItem:
    source: str
    raw: str
    target: str
    status: str
    classification: str
    decision: str
    reason: str
    candidates: list[TargetDiscoveryCandidate]
    proposed_new_link: str | None
    live_mutation_authorized: bool = False
    approval_manifest_created: bool = False
    apply_authority: str = "none"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidates"] = [candidate.to_dict() for candidate in self.candidates]
        return payload


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_remaining_link_triage(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("triage packet must be a JSON object")
    return payload


def build_target_discovery_packet(
    *,
    triage_packet: Mapping[str, Any],
    notes_index: Iterable[Mapping[str, Any]],
    source_triage: str | Path | None = None,
    source_notes_index: str | Path | None = None,
    min_confidence: float = 0.92,
    max_candidates: int = 5,
) -> dict[str, Any]:
    if not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be between 0 and 1")

    notes = list(notes_index)
    raw_items = triage_packet.get("items", [])
    if not isinstance(raw_items, list):
        raise ValueError("triage packet items must be a list")

    items = [
        discover_target_for_item(
            item,
            notes=notes,
            min_confidence=min_confidence,
            max_candidates=max_candidates,
        )
        for item in raw_items
        if isinstance(item, Mapping)
    ]
    counts = Counter(item.decision for item in items)
    class_counts = Counter(item.classification for item in items)
    confident = [item for item in items if item.decision == "proposal_candidate"]
    findings: list[str] = []
    if confident:
        findings.append("proposal candidates require separate approval manifest before any live apply")

    return {
        "schema": MODE,
        "mode": "repo-only/evidence-only",
        "status": "proposal_candidates_found" if confident else "no_live_candidates",
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_triage": str(source_triage) if source_triage is not None else None,
        "source_notes_index": str(source_notes_index) if source_notes_index is not None else None,
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "apply_authority": "none",
        "findings": findings,
        "summary": {
            "items": len(items),
            "by_decision": dict(counts),
            "by_classification": dict(class_counts),
            "proposal_candidates": len(confident),
            "manual_or_suppressed": len(items) - len(confident),
            "min_confidence": min_confidence,
        },
        "items": [item.to_dict() for item in items],
    }


def discover_target_for_item(
    item: Mapping[str, Any],
    *,
    notes: Iterable[Mapping[str, Any]],
    min_confidence: float = 0.92,
    max_candidates: int = 5,
) -> TargetDiscoveryItem:
    source = str(item.get("source") or "")
    raw = str(item.get("raw") or item.get("target") or "")
    target = str(item.get("target") or _target_part(raw))
    status = str(item.get("status") or "")
    classification = str(item.get("classification") or "")

    if classification in SUPPRESSED_CLASSES:
        return TargetDiscoveryItem(
            source=source,
            raw=raw,
            target=target,
            status=status,
            classification=classification,
            decision="suppressed_by_policy",
            reason="triage class is policy-suppressed and must not become a proposal candidate",
            candidates=[],
            proposed_new_link=None,
        )

    if classification not in DISCOVERY_CLASSES:
        return TargetDiscoveryItem(
            source=source,
            raw=raw,
            target=target,
            status=status,
            classification=classification,
            decision="unsupported_classification",
            reason="target discovery only handles explicit discovery/disambiguation classes",
            candidates=[],
            proposed_new_link=None,
        )

    candidates = _rank_candidates(target, source=source, notes=notes)[:max_candidates]
    if not candidates:
        return TargetDiscoveryItem(
            source=source,
            raw=raw,
            target=target,
            status=status,
            classification=classification,
            decision="no_candidate",
            reason="no repo-indexed note matched target hint",
            candidates=[],
            proposed_new_link=None,
        )

    best = candidates[0]
    second = candidates[1].score if len(candidates) > 1 else 0.0
    same_source_exact = _is_same_source_vault_exact_target(source=source, target=target, candidate_path=best.path)
    if (
        (best.score >= min_confidence and best.score - second >= 0.08)
        or (same_source_exact and best.score >= 0.82)
    ) and not best.safety_flags:
        reason = "high-confidence target discovery; separate manifest required before live apply"
        if same_source_exact:
            reason = "same-source-vault exact target beats cross-vault mirror ambiguity; separate manifest required before live apply"
        return TargetDiscoveryItem(
            source=source,
            raw=raw,
            target=target,
            status=status,
            classification=classification,
            decision="proposal_candidate",
            reason=reason,
            candidates=candidates,
            proposed_new_link=_replace_target(raw, _without_md(best.path)),
        )

    return TargetDiscoveryItem(
        source=source,
        raw=raw,
        target=target,
        status=status,
        classification=classification,
        decision="manual_review_required",
        reason="candidate confidence missing, low, tied, or safety-flagged",
        candidates=candidates,
        proposed_new_link=None,
    )


def write_target_discovery_packet(
    *,
    triage_json: str | Path,
    notes_index_jsonl: str | Path,
    out_dir: str | Path,
    min_confidence: float = 0.92,
) -> dict[str, str]:
    triage = load_remaining_link_triage(triage_json)
    notes = read_jsonl(notes_index_jsonl)
    packet = build_target_discovery_packet(
        triage_packet=triage,
        notes_index=notes,
        source_triage=triage_json,
        source_notes_index=notes_index_jsonl,
        min_confidence=min_confidence,
    )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet_path = out / "remaining-link-target-discovery-v1.json"
    items_path = out / "remaining-link-target-discovery-items.jsonl"
    report_path = out / "REPORT.md"
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    items_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in packet["items"]),
        encoding="utf-8",
    )
    report_path.write_text(target_discovery_to_markdown(packet), encoding="utf-8")
    return {
        "status": str(packet["status"]),
        "packet": str(packet_path),
        "items": str(items_path),
        "report": str(report_path),
    }


def target_discovery_to_markdown(packet: Mapping[str, Any]) -> str:
    summary = packet.get("summary", {})
    lines = [
        "# Remaining Link Target Discovery",
        "",
        f"- schema: `{packet.get('schema')}`",
        f"- status: `{packet.get('status')}`",
        "- mode: repo-only/evidence-only",
        "- live_mutation_authorized: `false`",
        "- approval_manifest_created: `false`",
        "- apply_authority: `none`",
        f"- items: `{summary.get('items', 0)}`",
        f"- proposal_candidates: `{summary.get('proposal_candidates', 0)}`",
        "",
        "High-confidence discoveries are proposal-only and require a separate approval manifest before any live apply.",
    ]
    return "\n".join(lines) + "\n"


def _rank_candidates(
    target: str,
    *,
    source: str,
    notes: Iterable[Mapping[str, Any]],
) -> list[TargetDiscoveryCandidate]:
    target_base = target.split("#", 1)[0]
    target_norm = _norm(target_base)
    source_top = source.split("/", 1)[0] if "/" in source else ""
    ranked: list[TargetDiscoveryCandidate] = []

    for note in notes:
        path = str(note.get("path") or note.get("relative_path") or "")
        title = str(note.get("title") or Path(path).stem)
        if not path:
            continue

        safety_flags = _safety_flags(note, path)
        variants = {_norm(path), _norm(_without_md(path)), _norm(Path(path).stem), _norm(title)}
        score = max((SequenceMatcher(None, target_norm, variant).ratio() for variant in variants), default=0.0)
        reasons: list[str] = []

        if _without_md(path).lower() == target_base.lower():
            score = 1.0
            reasons.append("exact_path_without_md")
        if title.lower() == target_base.lower() or Path(path).stem.lower() == target_base.lower():
            score = max(score, 0.98)
            reasons.append("exact_title")
        if source_top and path.startswith(f"{source_top}/"):
            score = min(1.0, score + 0.02)
            reasons.append("same_top_level")

        if score > 0:
            ranked.append(
                TargetDiscoveryCandidate(
                    path=path,
                    title=title,
                    score=round(score, 4),
                    reason_codes=reasons or ["fuzzy_match"],
                    safety_flags=safety_flags,
                )
            )

    return sorted(ranked, key=lambda candidate: (candidate.score, -len(candidate.safety_flags)), reverse=True)


def _target_part(raw: str) -> str:
    return raw.split("|", 1)[0].strip()


def _replace_target(raw: str, new_target: str) -> str:
    if "|" in raw:
        _, alias = raw.split("|", 1)
        return f"{new_target}|{alias}"
    return new_target


def _without_md(path: str) -> str:
    return path[:-3] if path.endswith(".md") else path


def _norm(value: str) -> str:
    return " ".join(_without_md(value).replace("/", " ").replace("-", " ").replace("_", " ").lower().split())


def _is_same_source_vault_exact_target(*, source: str, target: str, candidate_path: str) -> bool:
    source_top = source.split("/", 1)[0] if "/" in source else ""
    if not source_top or not source_top.endswith("-Vault") or _is_protected_root(source_top):
        return False
    target_base = target.split("#", 1)[0].lstrip("./")
    expected = target_base if target_base.startswith(f"{source_top}/") else f"{source_top}/{target_base}"
    return _without_md(candidate_path).lower() == _without_md(expected).lower()


def _is_protected_root(root: str) -> bool:
    return root.lower() in {"soul-vault", "hermes-soul-vault", "soul-organism-graphify-vault"}


def _safety_flags(note: Mapping[str, Any], path: str) -> list[str]:
    flags: list[str] = []
    parts = set(Path(path).parts)
    if parts & PROTECTED_PATH_PARTS:
        flags.append("protected_path")
    if path.split("/", 1)[0].lower() in {"soul-vault", "hermes-soul-vault", "soul-organism-graphify-vault"}:
        flags.append("protected_vault_root")
    if bool(note.get("protected")) or bool(note.get("soul_protected")):
        flags.append("protected_note")
    if str(note.get("vault_role") or "").lower() in {"live", "external"}:
        flags.append("non_repo_note_index")
    return flags
