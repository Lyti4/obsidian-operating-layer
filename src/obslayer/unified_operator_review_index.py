from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .guardrails import GuardrailError

MODE = "obslayer.unified-operator-review-index.v1"
ALLOWED_PREFIXES = ("out", "docs")
DEFAULT_ARTIFACTS = (
    "out/reports/operator-review-packet/grouped-next5-smoke/operator-review-packet.json",
    "out/reports/operator-review-packet/grouped-next5-smoke/REPORT.md",
    "out/reports/remaining-link-suppression-gate-20260706T1420Z/HERMES_ACCEPTANCE_REPORT.md",
    "out/reports/remaining-broader-target-discovery-20260706T152315Z-same-vault-rule/REPORT.md",
    "out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z/candidate-volume-operator-packet.json",
    "out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z/REPORT.md",
    "docs/acceptance/index.md",
    "docs/spec-kit/36-current-evidence-index.md",
)
PER_VAULT_INDEX = "out/reports/per-vault-index"
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
}
TRUE_STRINGS = {"1", "true", "yes", "y", "enabled", "enable", "approved", "authorize", "authorized"}
SAFE_APPLY_VALUES = {None, False, "", "false", "none"}


@dataclass(frozen=True)
class UnifiedReviewArtifact:
    path: str
    kind: str
    exists: bool
    status: str | None
    review_items: int | None
    safety: dict[str, Any]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnifiedOperatorReviewIndex:
    mode: str
    generated_at: str
    repo_root: str
    status: str
    artifacts: list[UnifiedReviewArtifact]
    summary: dict[str, int]
    safety: dict[str, Any]
    next_gates: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = [artifact.to_dict() for artifact in self.artifacts]
        return payload


def _repo_root(repo: str | Path | None = None) -> Path:
    return Path(repo).expanduser().resolve() if repo is not None else Path.cwd().resolve()


def _relative_to_repo(path: str | Path, repo: Path) -> tuple[Path, str]:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    try:
        rel = resolved.relative_to(repo)
    except ValueError as exc:
        raise GuardrailError(f"unified operator review artifact escapes repo: {resolved}") from exc
    rel_posix = rel.as_posix()
    if not any(rel_posix == prefix or rel_posix.startswith(f"{prefix}/") for prefix in ALLOWED_PREFIXES):
        raise GuardrailError(f"unified operator review artifacts must stay under repo out/ or docs/: {rel_posix}")
    return resolved, rel_posix


def _output_dir(path: str | Path, repo: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    out_root = (repo / "out").resolve()
    try:
        resolved.relative_to(out_root)
    except ValueError as exc:
        raise GuardrailError(f"unified operator review output must stay under repo out/: {resolved}") from exc
    return resolved


def _default_artifacts(repo: Path) -> list[Path]:
    paths = [repo / artifact for artifact in DEFAULT_ARTIFACTS]
    per_vault_root = repo / PER_VAULT_INDEX
    if per_vault_root.is_dir():
        machine_readable = sorted(
            path
            for path in per_vault_root.rglob("*")
            if path.is_file() and (path.suffix == ".json" or path.name == "REPORT.md")
        )
        paths.extend(machine_readable[:5])
    return paths


def _artifact_kind(path: Path, rel_path: str) -> str:
    if path.suffix == ".json":
        return "json"
    if rel_path.startswith("docs/"):
        return "doc"
    if path.name.endswith(".md"):
        return "report"
    return "artifact"


def _review_item_count(payload: dict[str, Any]) -> int | None:
    for key in ("review_items", "dry_run_proposals", "proposal_candidates", "candidates"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, int):
            return value
    summary = payload.get("summary")
    if isinstance(summary, dict):
        for key in ("review_items", "ready_for_human_review_count", "proposal_candidates"):
            value = summary.get(key)
            if isinstance(value, int):
                return value
    return None


def _true_like(value: Any, *, key: str) -> bool:
    if key == "apply_authority":
        if isinstance(value, str):
            return value.strip().lower() not in SAFE_APPLY_VALUES
        return value not in SAFE_APPLY_VALUES
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


def _extract_safety(payload: dict[str, Any]) -> dict[str, Any]:
    safety: dict[str, Any] = {}
    for key in AUTHORITY_KEYS:
        if key in payload:
            safety[key] = payload[key]
    nested = payload.get("safety")
    if isinstance(nested, dict):
        for key in AUTHORITY_KEYS | {"target_paths"}:
            if key in nested:
                safety[key] = nested[key]
    if "target_paths" in payload:
        safety["target_paths"] = payload["target_paths"]
    return safety


def _json_artifact(path: Path, rel_path: str) -> UnifiedReviewArtifact:
    notes: list[str] = []
    status: str | None = None
    review_items: int | None = None
    safety: dict[str, Any] = {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return UnifiedReviewArtifact(rel_path, "json", True, "blocked", None, {}, [f"invalid JSON: {exc.msg}"])
    if not isinstance(payload, dict):
        return UnifiedReviewArtifact(rel_path, "json", True, "blocked", None, {}, ["JSON artifact root must be an object"])

    raw_status = payload.get("status")
    status = str(raw_status) if raw_status is not None else None
    review_items = _review_item_count(payload)
    safety = _extract_safety(payload)
    findings = _authority_findings(payload)
    if findings:
        status = "blocked"
        notes.extend(findings)
    if status in {"ready_for_human_review", "ready_for_operator_review", "accepted", "ready-for-operator-review"}:
        notes.append("ready/review status inferred from JSON")
    elif review_items:
        notes.append("review item count inferred from JSON")
    if not notes:
        notes.append("machine-readable evidence pointer")
    return UnifiedReviewArtifact(rel_path, "json", True, status, review_items, safety, notes)


def _text_artifact(path: Path, rel_path: str, kind: str) -> UnifiedReviewArtifact:
    notes: list[str] = ["repo-local pointer only"]
    text = path.read_text(encoding="utf-8", errors="replace")
    status: str | None = None
    lowered = text.lower()
    if "proposal-only" in lowered or "review" in lowered:
        status = "proposal_only"
        notes.append("proposal/review language inferred from text")
    if "live_mutation_authorized: false" in lowered or "apply_authority: none" in lowered:
        notes.append("inert safety language present")
    return UnifiedReviewArtifact(rel_path, kind, True, status, None, {}, notes)


def _artifact(path: str | Path, repo: Path) -> UnifiedReviewArtifact:
    resolved, rel_path = _relative_to_repo(path, repo)
    kind = _artifact_kind(resolved, rel_path)
    if not resolved.exists():
        return UnifiedReviewArtifact(rel_path, kind, False, None, None, {}, ["missing pointer"])
    if resolved.is_dir():
        return UnifiedReviewArtifact(rel_path, "directory", True, "proposal_only", None, {}, ["repo-local pointer directory only"])
    if kind == "json":
        return _json_artifact(resolved, rel_path)
    return _text_artifact(resolved, rel_path, kind)


def _summary(artifacts: list[UnifiedReviewArtifact]) -> dict[str, int]:
    ready_count = sum(
        1
        for artifact in artifacts
        if artifact.exists and artifact.status in {"ready_for_human_review", "ready_for_operator_review", "ready-for-operator-review"}
    )
    blocked_count = sum(1 for artifact in artifacts if artifact.status == "blocked")
    proposal_only_count = sum(
        1
        for artifact in artifacts
        if artifact.exists
        and (
            artifact.status == "proposal_only"
            or artifact.review_items is not None
            or any("proposal" in note or "review" in note for note in artifact.notes)
        )
    )
    return {
        "total_artifacts": len(artifacts),
        "present_artifacts": sum(1 for artifact in artifacts if artifact.exists),
        "missing_artifacts": sum(1 for artifact in artifacts if not artifact.exists),
        "ready_for_human_review_count": ready_count,
        "blocked_count": blocked_count,
        "proposal_only_count": proposal_only_count,
    }


def _status(summary: dict[str, int]) -> str:
    if summary["blocked_count"]:
        return "blocked"
    if summary["present_artifacts"] and (summary["ready_for_human_review_count"] or summary["proposal_only_count"]):
        return "ready_for_operator_review"
    return "no_current_artifacts"


def _next_gates(status: str) -> list[str]:
    if status == "blocked":
        return [
            "Stop before any apply path.",
            "Inspect blocked artifact notes and replace authority-bearing evidence with inert proposal/review evidence.",
        ]
    if status == "ready_for_operator_review":
        return [
            "Hermes/Dmitry review the indexed pointers.",
            "Keep full-vault indexing scale-up proposal-only until a separate approval manifest, backup, apply, and verify packet exists.",
        ]
    return ["Create or refresh repo-local proposal/review artifacts before operator review."]


def build_unified_operator_review_index(
    *,
    repo: str | Path | None = None,
    artifacts: Iterable[str | Path] | None = None,
    generated_at: str | None = None,
) -> UnifiedOperatorReviewIndex:
    repo_root = _repo_root(repo)
    raw_artifacts = list(artifacts) if artifacts is not None else _default_artifacts(repo_root)
    artifact_records = [_artifact(path, repo_root) for path in raw_artifacts]
    summary = _summary(artifact_records)
    status = _status(summary)
    return UnifiedOperatorReviewIndex(
        mode=MODE,
        generated_at=generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo_root=str(repo_root),
        status=status,
        artifacts=artifact_records,
        summary=summary,
        safety={**SAFETY, "target_paths": []},
        next_gates=_next_gates(status),
    )


def unified_operator_review_index_to_markdown(index: UnifiedOperatorReviewIndex) -> str:
    lines = [
        "# Unified Operator Review Index",
        "",
        f"- mode: `{index.mode}`",
        f"- status: `{index.status}`",
        f"- repo_root: `{index.repo_root}`",
        f"- generated_at: `{index.generated_at}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in index.summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- live_mutation_authorized: `{str(index.safety['live_mutation_authorized']).lower()}`",
            f"- approval_manifest_created: `{str(index.safety['approval_manifest_created']).lower()}`",
            f"- approval_manifest_authority: `{str(index.safety['approval_manifest_authority']).lower()}`",
            f"- apply_authority: `{index.safety['apply_authority']}`",
            f"- target_paths: `{index.safety['target_paths']}`",
            "",
            "## Artifacts",
            "",
        ]
    )
    for artifact in index.artifacts:
        exists = "present" if artifact.exists else "missing"
        status = artifact.status or "unknown"
        notes = "; ".join(artifact.notes)
        lines.append(f"- `{exists}` `{artifact.kind}` `{status}` {artifact.path} — {notes}")
    lines.extend(["", "## Next Gates", ""])
    lines.extend(f"- {gate}" for gate in index.next_gates)
    lines.append("")
    return "\n".join(lines)


def write_unified_operator_review_index(index: UnifiedOperatorReviewIndex, out_dir: str | Path) -> tuple[Path, Path]:
    out = _output_dir(out_dir, Path(index.repo_root))
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "unified-operator-review-index.json"
    report_path = out / "REPORT.md"
    json_path.write_text(json.dumps(index.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(unified_operator_review_index_to_markdown(index), encoding="utf-8")
    return json_path, report_path
