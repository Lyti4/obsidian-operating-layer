from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .guardrails import GuardrailError, is_protected_relative, load_json, normalize_vault_root, validate_approval_manifest, validate_targets

MODE = "approved-apply-readiness-v1"


@dataclass(frozen=True)
class ApplyReadinessTarget:
    path: str
    status: str
    sha256_present: bool
    evidence_present: bool
    old_text_present: bool
    new_text_present: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApplyReadinessReport:
    mode: str
    status: str
    behavior: str
    ready_for_human_approved_apply: bool
    issues: list[str]
    warnings: list[str]
    target_count: int
    targets: list[ApplyReadinessTarget]
    proposal_path: str
    approval_manifest_path: str
    vault_root: str
    backup_root: str
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["targets"] = [target.to_dict() for target in self.targets]
        return payload


def evaluate_approved_apply_readiness(
    proposal: Mapping[str, Any],
    approval_manifest: Mapping[str, Any],
    *,
    proposal_path: str | Path,
    approval_manifest_path: str | Path,
) -> ApplyReadinessReport:
    """Validate a proposal/approval-manifest bundle without applying it.

    This is a preflight gate only. It never grants live apply authority and never
    creates approval manifests or live targets.
    """

    issues: list[str] = []
    warnings: list[str] = []
    target_reports: list[ApplyReadinessTarget] = []
    proposal_resolved = Path(proposal_path).expanduser().resolve()
    manifest_resolved = Path(approval_manifest_path).expanduser().resolve()

    manifest_obj = None
    vault_root = ""
    backup_root = ""
    try:
        manifest_obj = validate_approval_manifest(dict(approval_manifest))
        vault_root = manifest_obj.vault_root
        backup_root = manifest_obj.backup_root
    except (GuardrailError, TypeError, ValueError) as exc:
        issues.append(f"approval manifest failed guardrail validation: {exc}")
        raw_vault = approval_manifest.get("vault_root") or proposal.get("vault_root") or ""
        vault_root = str(raw_vault)
        backup_root = str(approval_manifest.get("backup_root") or "")

    raw_manifest_proposal = approval_manifest.get("proposal") or approval_manifest.get("proposal_path")
    if not raw_manifest_proposal:
        issues.append("approval manifest must explicitly name the proposal file")
    else:
        manifest_proposal = Path(str(raw_manifest_proposal)).expanduser().resolve()
        if manifest_proposal != proposal_resolved:
            issues.append(f"approval manifest proposal does not match proposal path: {manifest_proposal} != {proposal_resolved}")

    if proposal.get("vault_root") and vault_root:
        try:
            proposal_root = normalize_vault_root(str(proposal["vault_root"]))
            manifest_root = normalize_vault_root(vault_root)
            if proposal_root != manifest_root:
                issues.append(f"proposal vault_root does not match manifest vault_root: {proposal_root} != {manifest_root}")
        except GuardrailError as exc:
            issues.append(f"vault_root failed validation: {exc}")

    proposal_targets = proposal.get("targets")
    if not isinstance(proposal_targets, list) or not proposal_targets:
        issues.append("proposal targets must be a non-empty list")
        proposal_targets = []

    if manifest_obj is not None and proposal_targets:
        try:
            proposal_relpaths = _proposal_target_relpaths(Path(manifest_obj.vault_root), proposal_targets)
            approved_relpaths = validate_targets(manifest_obj.vault_root, manifest_obj.targets)
            proposal_set = sorted(path.as_posix() for path in proposal_relpaths)
            approved_set = sorted(path.as_posix() for path in approved_relpaths)
            if proposal_set != approved_set:
                issues.append(
                    "proposal targets do not match approval manifest; "
                    f"not_approved={sorted(set(proposal_set) - set(approved_set))}; "
                    f"extra_approved={sorted(set(approved_set) - set(proposal_set))}"
                )
        except (GuardrailError, TypeError, ValueError) as exc:
            issues.append(f"target alignment failed guardrail validation: {exc}")

    max_files = int(approval_manifest.get("max_files_per_run", 25) or 25)
    if proposal_targets and len(proposal_targets) > max_files:
        issues.append(f"proposal target count {len(proposal_targets)} exceeds max_files_per_run {max_files}")

    for raw_target in proposal_targets:
        if not isinstance(raw_target, Mapping):
            issues.append("proposal target must be an object")
            continue
        raw_path = str(raw_target.get("path") or "")
        if not raw_path:
            issues.append("proposal target missing path")
            continue
        try:
            rel = _target_relpath(Path(vault_root), raw_path) if vault_root else Path(raw_path)
            if is_protected_relative(rel):
                issues.append(f"proposal target is protected and cannot be applied: {rel.as_posix()}")
        except (GuardrailError, TypeError, ValueError) as exc:
            issues.append(f"proposal target path failed validation: {exc}")

        sha_present = bool(raw_target.get("base_sha256"))
        evidence_present = bool(raw_target.get("evidence"))
        old_present = "old_text" in raw_target
        new_present = "new_text" in raw_target
        if not sha_present:
            issues.append(f"proposal target lacks base_sha256 hash binding: {raw_path}")
        if not evidence_present:
            issues.append(f"proposal target lacks evidence reference: {raw_path}")
        if not new_present:
            issues.append(f"proposal target lacks new_text: {raw_path}")
        if not old_present:
            warnings.append(f"proposal target has no old_text anchor; full-file replacement only if intentionally approved: {raw_path}")
        target_reports.append(
            ApplyReadinessTarget(
                path=raw_path,
                status="ready" if sha_present and evidence_present and new_present else "not-ready",
                sha256_present=sha_present,
                evidence_present=evidence_present,
                old_text_present=old_present,
                new_text_present=new_present,
            )
        )

    safety = {
        "behavior": "readiness-only/evidence-only",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
        "approval_manifest_authority": False,
        "targets": [],
        "apply_authority": "none",
    }
    ready = not issues and bool(target_reports)
    return ApplyReadinessReport(
        mode=MODE,
        status="ready" if ready else "not-ready",
        behavior="readiness-only/evidence-only",
        ready_for_human_approved_apply=ready,
        issues=issues,
        warnings=warnings,
        target_count=len(target_reports),
        targets=target_reports,
        proposal_path=str(proposal_resolved),
        approval_manifest_path=str(manifest_resolved),
        vault_root=vault_root,
        backup_root=backup_root,
        safety=safety,
    )


def load_and_evaluate_approved_apply_readiness(
    *,
    proposal_path: str | Path,
    approval_manifest_path: str | Path,
) -> ApplyReadinessReport:
    proposal_resolved = Path(proposal_path).expanduser().resolve()
    manifest_resolved = Path(approval_manifest_path).expanduser().resolve()
    proposal = load_json(proposal_resolved)
    manifest = load_json(manifest_resolved)
    return evaluate_approved_apply_readiness(
        proposal,
        manifest,
        proposal_path=proposal_resolved,
        approval_manifest_path=manifest_resolved,
    )


def approved_apply_readiness_to_markdown(report: ApplyReadinessReport) -> str:
    payload = report.to_dict()
    lines = [
        "# Approved Apply Readiness v1",
        "",
        f"- status: `{payload['status']}`",
        f"- behavior: `{payload['behavior']}`",
        f"- ready_for_human_approved_apply: `{payload['ready_for_human_approved_apply']}`",
        f"- target_count: `{payload['target_count']}`",
        "",
        "## Safety",
        "",
    ]
    for key, value in payload["safety"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Issues", ""])
    if payload["issues"]:
        lines.extend(f"- {issue}" for issue in payload["issues"])
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- none")
    lines.extend(["", "## Targets", ""])
    if payload["targets"]:
        for target in payload["targets"]:
            lines.append(
                f"- `{target['path']}` — {target['status']} "
                f"(sha256={target['sha256_present']}, evidence={target['evidence_present']}, "
                f"old_text={target['old_text_present']}, new_text={target['new_text_present']})"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_approved_apply_readiness_bundle(report: ApplyReadinessReport, out_dir: str | Path) -> dict[str, str]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "approved-apply-readiness-v1.json"
    report_path = target / "REPORT.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(approved_apply_readiness_to_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "report": str(report_path)}


def _proposal_target_relpaths(vault_root: Path, targets: list[Any]) -> list[Path]:
    return [_target_relpath(vault_root, str(target.get("path") or "")) for target in targets if isinstance(target, Mapping)]


def _target_relpath(vault_root: Path, raw_path: str) -> Path:
    root = normalize_vault_root(vault_root)
    candidate = Path(raw_path).expanduser()
    target_path = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        return target_path.relative_to(root)
    except ValueError as exc:
        raise GuardrailError(f"target escapes vault root: {target_path}") from exc
