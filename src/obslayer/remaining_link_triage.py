from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from obslayer.external_autograph_policy import external_policy_source, load_external_autograph_policy

MODE = "obslayer.remaining-link-triage.v1"
POLICY = load_external_autograph_policy()
REPORT_PATH_PARTS = tuple(str(part).lower() for part in POLICY["generated_report_noise"]["path_parts"])
NOISE_WORDS = tuple(str(word).lower() for word in POLICY["generated_report_noise"]["noise_words"])
PROTECTED_LINK_PARTS = tuple(str(part).lower() for part in POLICY["protected_link_parts"])


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def build_remaining_link_triage_packet(
    *,
    wikilinks: Iterable[Mapping[str, Any]],
    source_wikilinks: str | Path | None = None,
) -> dict[str, Any]:
    items = [
        classify_remaining_link(row)
        for row in wikilinks
        if str(row.get("status") or "") in {"broken", "ambiguous"}
    ]
    counts: Counter[str] = Counter(str(item["classification"]) for item in items)
    status_counts: Counter[str] = Counter(str(item["status"]) for item in items)
    apply_counts: Counter[str] = Counter(str(item["apply_authority"]) for item in items)
    bucket_counts: Counter[str] = Counter(str(item["operator_bucket"]) for item in items)
    return {
        "schema": MODE,
        "mode": "repo-only/evidence-only",
        "status": "ok",
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_wikilinks": str(source_wikilinks) if source_wikilinks is not None else None,
        "source_policy": external_policy_source("remaining-link-triage-contract"),
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "apply_authority": "none",
        "summary": {
            "items": len(items),
            "by_status": dict(status_counts),
            "by_classification": dict(counts),
            "by_apply_authority": dict(apply_counts),
            "by_operator_bucket": dict(bucket_counts),
            "accepted_no_apply_items": bucket_counts.get("accepted_no_apply", 0),
            "manual_protected_items": bucket_counts.get("manual_protected", 0),
            "target_discovery_items": bucket_counts.get("target_discovery", 0),
            "actionable_apply_items": sum(1 for item in items if item["apply_authority"] != "none"),
        },
        "items": items,
    }


def write_remaining_link_triage_packet(*, wikilinks_jsonl: str | Path, out_dir: str | Path) -> dict[str, str]:
    rows = read_jsonl(wikilinks_jsonl)
    packet = build_remaining_link_triage_packet(wikilinks=rows, source_wikilinks=wikilinks_jsonl)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet_path = out / "remaining-link-triage-v1.json"
    items_path = out / "remaining-link-triage-items.jsonl"
    report_path = out / "REPORT.md"
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    items_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in packet["items"]),
        encoding="utf-8",
    )
    report_path.write_text(remaining_link_triage_to_markdown(packet), encoding="utf-8")
    return {"status": "ok", "packet": str(packet_path), "items": str(items_path), "report": str(report_path)}


def classify_remaining_link(row: Mapping[str, Any]) -> dict[str, Any]:
    source = str(row.get("source") or "")
    raw = str(row.get("raw") or row.get("target") or "")
    target = str(row.get("target") or _target_part(raw))
    status = str(row.get("status") or "")
    candidates = [str(candidate) for candidate in row.get("candidates") or []]

    if _is_protected_source(source) or _is_protected_link(target) or _is_protected_link(raw):
        classification = "protected_cross_vault_manual"
        risk = "high"
        reason = "protected/cross-vault/Soul source or link; no automatic retarget/create"
        rule_id = "remaining-protected-cross-vault-manual"
        preferred_candidate = None
    elif (
        status == "ambiguous"
        and (preferred := _exact_candidate_for_target(target, candidates))
        and _is_graphify_report_link(target, source)
    ):
        classification = "graphify_exact_path_preferred_no_apply"
        risk = "low"
        reason = "Graphify report link already names an exact report path; ambiguity is resolver/title fallback noise"
        rule_id = "remaining-graphify-exact-path-preferred"
        preferred_candidate = preferred
    elif _is_generated_or_report_context(source, target, raw):
        classification = "generated_report_auto_keep"
        risk = "low"
        reason = "generated/report/audit/evidence context; keep as historical evidence"
        rule_id = "remaining-generated-report-auto-keep"
        preferred_candidate = None
    else:
        classification = "real_broken_needs_target_discovery" if status == "broken" else "ambiguous_needs_operator_disambiguation"
        risk = "medium"
        reason = "non-generated unresolved link requires target discovery/operator decision"
        rule_id = "remaining-target-discovery-required"
        preferred_candidate = None

    operator_bucket = _operator_bucket(classification)

    return {
        "source": source,
        "raw": raw,
        "target": target,
        "status": status,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "classification": classification,
        "operator_bucket": operator_bucket,
        "risk": risk,
        "reason": reason,
        "preferred_candidate": preferred_candidate,
        "source_policy": external_policy_source(rule_id),
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "apply_authority": "none",
    }


def remaining_link_triage_to_markdown(packet: Mapping[str, Any]) -> str:
    summary = packet["summary"]
    lines = [
        "# Remaining link triage v1",
        "",
        "Status: repo-only/evidence-only; no live mutation authority.",
        "",
        "## Summary",
        "",
        f"- items: `{summary['items']}`",
        f"- by_status: `{summary['by_status']}`",
        f"- by_classification: `{summary['by_classification']}`",
        f"- by_operator_bucket: `{summary['by_operator_bucket']}`",
        f"- accepted/no-apply noise: `{summary['accepted_no_apply_items']}`",
        f"- manual/protected: `{summary['manual_protected_items']}`",
        f"- target discovery needed: `{summary['target_discovery_items']}`",
        f"- actionable_apply_items: `{summary['actionable_apply_items']}`",
        "",
        "## Policy",
        "",
        "- generated/audit/evidence/report links: auto-keep/no-apply",
        "- Soul/cross-vault/protected links: manual-only/no-apply",
        "- Graphify exact report paths: prefer exact path for interpretation/no-apply",
        "- other unresolved links: target discovery required before proposal",
        "",
    ]
    return "\n".join(lines) + "\n"


def _operator_bucket(classification: str) -> str:
    if classification in {"generated_report_auto_keep", "graphify_exact_path_preferred_no_apply"}:
        return "accepted_no_apply"
    if classification == "protected_cross_vault_manual":
        return "manual_protected"
    return "target_discovery"


def _target_part(raw: str) -> str:
    return raw.split("|", 1)[0].strip()


def _without_md(path: str) -> str:
    return path[:-3] if path.endswith(".md") else path


def _exact_candidate_for_target(target: str, candidates: list[str]) -> str | None:
    target_no_heading = target.split("#", 1)[0]
    exact = target_no_heading if target_no_heading.endswith(".md") else f"{target_no_heading}.md"
    for candidate in candidates:
        if candidate == exact or _without_md(candidate) == target_no_heading:
            return candidate
    return None


def _is_graphify_report_link(target: str, source: str) -> bool:
    lower = f"{source}\n{target}".lower()
    return "graphify" in lower and ("/reports/" in lower or lower.startswith("hermes/reports/"))


def _is_generated_or_report_context(source: str, target: str, raw: str) -> bool:
    lower = f"{source}\n{target}\n{raw}".replace("\\", "/").lower()
    stem = Path(source).stem.lower()
    return (
        any(part in lower for part in REPORT_PATH_PARTS)
        or source.startswith("Hermes/Reports/")
        or any(word in stem for word in ("report", "audit", "evidence"))
        or any(word in lower for word in ("graph_report", "#community", "worker report"))
        or any(word in stem for word in NOISE_WORDS)
    )


def _is_protected_source(text: str) -> bool:
    lower = text.replace("\\", "/").lower()
    return (
        lower.startswith("soul-vault/")
        or lower.startswith("hermes-soul-vault/")
        or lower.startswith("soul-organism-graphify-vault/")
        or "/soul/" in lower
        or lower.startswith("soul/")
        or lower.startswith("hermes/soul/")
    )


def _is_protected_link(text: str) -> bool:
    lower = text.replace("\\", "/").lower()
    return (
        lower.startswith("soul/")
        or lower.startswith("hermes/soul/")
        or any(part in lower for part in PROTECTED_LINK_PARTS)
    )
