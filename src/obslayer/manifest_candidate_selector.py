from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError

MODE = "obslayer.manifest-candidate-selector.v1"
ALLOWED_PREFIXES = ("out", "docs")
MAX_CANDIDATES = 5
SAFETY: dict[str, Any] = {
    "live_mutation_authorized": False,
    "approval_manifest_created": False,
    "approval_manifest_authority": False,
    "apply_authority": "none",
    "target_paths": [],
}
AUTHORITY_KEYS = {
    "live_mutation_authorized",
    "approval_manifest_created",
    "approval_manifest_authority",
    "apply_authority",
    "target_paths",
}
TRUE_STRINGS = {"1", "true", "yes", "y", "enabled", "enable", "approved", "authorize", "authorized"}
SAFE_APPLY_VALUES = {None, False, "", "false", "none"}
SELECTABLE_ROUTES = {"proposal_candidate", "suggest", "proposal_only_ready"}
DENYLIST_TERMS = (
    ".obsidian",
    "_Backups",
    "_Archive",
    ".trash",
    "Soul",
    "secure",
    "credentials",
    "auth",
    "browser profile",
)


@dataclass(frozen=True)
class ManifestCandidateSelector:
    mode: str
    generated_at: str
    repo_root: str
    status: str
    source_candidate_packet: str
    source_unified_index: str
    source_operator_review_packet: str
    max_candidates: int
    selected_count: int
    selected_candidates: list[dict[str, Any]]
    manual_review_exclusions: list[dict[str, Any]]
    findings: list[str]
    next_safe_step: str
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(self.safety)
        return payload


def _repo_root(repo: str | Path | None = None) -> Path:
    return Path(repo).expanduser().resolve() if repo is not None else Path.cwd().resolve()


def _repo_local_path(path: str | Path, repo: Path, *, purpose: str) -> tuple[Path, str]:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    try:
        rel = resolved.relative_to(repo)
    except ValueError as exc:
        raise GuardrailError(f"{purpose} escapes repo: {resolved}") from exc
    rel_posix = rel.as_posix()
    if not any(rel_posix == prefix or rel_posix.startswith(f"{prefix}/") for prefix in ALLOWED_PREFIXES):
        raise GuardrailError(f"{purpose} must stay under repo out/ or docs/: {rel_posix}")
    return resolved, rel_posix


def _load_object(path: str | Path, repo: Path, *, purpose: str) -> tuple[dict[str, Any], str]:
    resolved, rel_path = _repo_local_path(path, repo, purpose=purpose)
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardrailError(f"{purpose} must be a JSON object: {resolved}")
    return payload, rel_path


def _true_like(value: Any, *, key: str) -> bool:
    if key == "apply_authority":
        if isinstance(value, str):
            return value.strip().lower() not in SAFE_APPLY_VALUES
        return value not in SAFE_APPLY_VALUES
    if key == "target_paths":
        return bool(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in TRUE_STRINGS
    if isinstance(value, (int, float)):
        return value != 0
    return value is not None


def _authority_findings(value: Any, *, prefix: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            if key in AUTHORITY_KEYS and _true_like(nested, key=key):
                findings.append(f"{dotted} claims apply/approval authority")
            findings.extend(_authority_findings(nested, prefix=dotted))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(_authority_findings(nested, prefix=f"{prefix}[{index}]"))
    return findings


def _summary_count(payload: dict[str, Any], *keys: str) -> int:
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return 0
    for key in keys:
        value = summary.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return 0


def _candidate_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    return value if isinstance(value, str) else ""


def _has_candidate_fields(item: dict[str, Any]) -> bool:
    return bool(
        _candidate_text(item, "source_id")
        and (
            _candidate_text(item, "proposed_link")
            or _candidate_text(item, "target")
            or _candidate_text(item, "new_text")
        )
    )


def _selectable(item: dict[str, Any]) -> bool:
    route = item.get("route")
    if isinstance(route, str) and route:
        return route in SELECTABLE_ROUTES
    return _has_candidate_fields(item)


def _denylist_reasons(item: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    values = [
        _candidate_text(item, "source_id"),
        _candidate_text(item, "old_link"),
        _candidate_text(item, "proposed_link"),
        _candidate_text(item, "target"),
        _candidate_text(item, "new_text"),
    ]
    lowered_values = [value.lower() for value in values]
    for term in DENYLIST_TERMS:
        needle = term.lower()
        if any(needle in value for value in lowered_values):
            reasons.append(f"mentions denylisted area: {term}")
    return reasons


def _reason_codes(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def _selected_candidate(item: dict[str, Any]) -> dict[str, Any]:
    confidence = item.get("confidence")
    return {
        "source_id": _candidate_text(item, "source_id"),
        "proposed_link": _candidate_text(item, "proposed_link") or _candidate_text(item, "target") or _candidate_text(item, "new_text"),
        "old_link": _candidate_text(item, "old_link"),
        "rollback_key": _candidate_text(item, "rollback_key"),
        "policy_tag": _candidate_text(item, "policy_tag"),
        "reason_codes": _reason_codes(item.get("reason_codes")),
        "route": _candidate_text(item, "route"),
        "confidence": confidence if isinstance(confidence, (int, float)) else None,
        "approval_required": True,
        "apply_authority": "none",
    }


def build_manifest_candidate_selector(
    *,
    repo: str | Path | None = None,
    candidate_packet: str | Path,
    unified_index: str | Path,
    operator_review_packet: str | Path,
    max_candidates: int = MAX_CANDIDATES,
) -> ManifestCandidateSelector:
    repo_path = _repo_root(repo)
    candidate_payload, candidate_rel = _load_object(candidate_packet, repo_path, purpose="candidate packet input")
    unified_payload, unified_rel = _load_object(unified_index, repo_path, purpose="unified index input")
    operator_payload, operator_rel = _load_object(operator_review_packet, repo_path, purpose="operator review packet input")

    findings: list[str] = []
    for name, payload in (
        ("candidate_packet", candidate_payload),
        ("unified_index", unified_payload),
        ("operator_review_packet", operator_payload),
    ):
        findings.extend(f"{name}.{finding}" for finding in _authority_findings(payload))

    blocked_count = _summary_count(unified_payload, "blocked_count")
    missing_artifacts = _summary_count(unified_payload, "missing_artifacts", "missing_count")
    if blocked_count:
        findings.append(f"unified index reports {blocked_count} blocked artifact(s)")
    if missing_artifacts:
        findings.append(f"unified index reports {missing_artifacts} missing artifact(s)")

    raw_items = operator_payload.get("review_items")
    if not isinstance(raw_items, list):
        raw_items = []
        findings.append("operator review packet review_items must be a list")

    selected: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    if not findings:
        for index, raw in enumerate(raw_items):
            if not isinstance(raw, dict) or not _selectable(raw):
                continue
            reasons = _denylist_reasons(raw)
            if reasons:
                exclusions.append(
                    {
                        "source_id": _candidate_text(raw, "source_id") or f"review_items[{index}]",
                        "route": _candidate_text(raw, "route"),
                        "reasons": reasons,
                    }
                )
                continue
            if len(selected) < max_candidates:
                selected.append(_selected_candidate(raw))

    status = "blocked" if findings else ("ready_for_operator_review" if selected else "no_candidate")
    return ManifestCandidateSelector(
        mode=MODE,
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo_root=str(repo_path),
        status=status,
        source_candidate_packet=candidate_rel,
        source_unified_index=unified_rel,
        source_operator_review_packet=operator_rel,
        max_candidates=max_candidates,
        selected_count=len(selected),
        selected_candidates=selected,
        manual_review_exclusions=exclusions,
        findings=findings,
        next_safe_step=(
            "A separate explicit approval manifest is required before any live pilot; "
            "this selector is evidence-only and proposal-only."
        ),
        safety={**SAFETY},
    )


def manifest_candidate_selector_to_markdown(selector: ManifestCandidateSelector) -> str:
    lines = [
        "# Manifest Candidate Selector",
        "",
        f"- mode: `{selector.mode}`",
        f"- status: `{selector.status}`",
        f"- generated_at: `{selector.generated_at}`",
        f"- selected_count: `{selector.selected_count}`",
        f"- max_candidates: `{selector.max_candidates}`",
        "",
        "## Safety",
        "- live_mutation_authorized: `false`",
        "- approval_manifest_created: `false`",
        "- approval_manifest_authority: `false`",
        "- apply_authority: `none`",
        "- target_paths: `[]`",
        "",
        "## Sources",
        f"- candidate packet: `{selector.source_candidate_packet}`",
        f"- unified index: `{selector.source_unified_index}`",
        f"- operator review packet: `{selector.source_operator_review_packet}`",
        "",
        "## Selected Candidates",
    ]
    if selector.selected_candidates:
        for candidate in selector.selected_candidates:
            lines.append(
                f"- `{candidate['source_id']}`: `{candidate['old_link']}` -> `{candidate['proposed_link']}` "
                f"route=`{candidate['route']}` apply_authority=`none`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Manual Review Exclusions"])
    if selector.manual_review_exclusions:
        for exclusion in selector.manual_review_exclusions:
            lines.append(f"- `{exclusion['source_id']}`: `{'; '.join(exclusion['reasons'])}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Findings"])
    if selector.findings:
        lines.extend(f"- {finding}" for finding in selector.findings)
    else:
        lines.append("- none")
    lines.extend(["", "## Next Safe Step", "", selector.next_safe_step])
    return "\n".join(lines) + "\n"


def write_manifest_candidate_selector(selector: ManifestCandidateSelector, out_dir: str | Path) -> tuple[Path, Path]:
    repo = _repo_root(selector.repo_root)
    out, _ = _repo_local_path(out_dir, repo, purpose="manifest candidate selector output")
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "manifest-candidate-selector.json"
    report_path = out / "REPORT.md"
    json_path.write_text(json.dumps(selector.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(manifest_candidate_selector_to_markdown(selector), encoding="utf-8")
    return json_path, report_path
