from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

MODE = "obslayer.acceptance-bundle.v1"
DOCTOR_MODE = "obslayer.acceptance-bundle-doctor.v1"
ALLOWED_ARTIFACT_ROOTS = ("out", "docs/spec-kit", "docs/acceptance", "src", "tests", "tools")
PASSING_CHECK_STATUSES = {"passed", "ok"}
FAILING_CHECK_STATUSES = {"failed", "error"}


@dataclass(frozen=True)
class AcceptanceBundleArtifact:
    name: str
    path: str
    required: bool
    exists: bool
    kind: str
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AcceptanceBundleCheck:
    name: str
    command: str
    status: str
    required: bool
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AcceptanceBundleDoctorReport:
    mode: str
    status: str
    created_at: str
    repo: str
    artifacts: list[AcceptanceBundleArtifact]
    checks: list[AcceptanceBundleCheck]
    findings: list[str]
    summary: dict[str, Any]
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = [artifact.to_dict() for artifact in self.artifacts]
        payload["checks"] = [check.to_dict() for check in self.checks]
        return payload


def _repo_root(repo: str | Path | None = None) -> Path:
    return Path(repo).expanduser().resolve() if repo is not None else Path.cwd().resolve()


def _as_bool(value: Any, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _artifact_path_under_allowed_roots(path: Path, repo: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo)
    except ValueError:
        return False
    rel_posix = rel.as_posix()
    return any(rel_posix == root or rel_posix.startswith(f"{root}/") for root in ALLOWED_ARTIFACT_ROOTS)


def _doctor_artifact(raw: Any, repo: Path) -> AcceptanceBundleArtifact:
    findings: list[str] = []
    if not isinstance(raw, Mapping):
        return AcceptanceBundleArtifact("", "", True, False, "", ["artifact entry must be an object"])

    name = str(raw.get("name") or "")
    raw_path = str(raw.get("path") or "")
    required = _as_bool(raw.get("required"), True)
    kind = str(raw.get("kind") or "evidence")

    if not name:
        findings.append("artifact name is required")
    if not raw_path:
        findings.append("artifact path is required")
        return AcceptanceBundleArtifact(name, raw_path, required, False, kind, findings)

    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()

    if not _artifact_path_under_allowed_roots(resolved, repo):
        findings.append("artifact path must stay under repo out/, docs/spec-kit/, src/, tests/, or tools/")
    exists = resolved.exists()
    if required and not exists:
        findings.append("required artifact is missing")

    return AcceptanceBundleArtifact(name, str(resolved), required, exists, kind, findings)


def _doctor_check(raw: Any) -> AcceptanceBundleCheck:
    findings: list[str] = []
    if not isinstance(raw, Mapping):
        return AcceptanceBundleCheck("", "", "", True, ["check entry must be an object"])

    name = str(raw.get("name") or "")
    command = str(raw.get("command") or "")
    status = str(raw.get("status") or "")
    required = _as_bool(raw.get("required"), True)

    if not name:
        findings.append("check name is required")
    if not command:
        findings.append("check command is required")
    if required and status not in PASSING_CHECK_STATUSES:
        findings.append("required check must have status passed/ok")
    if status in FAILING_CHECK_STATUSES:
        findings.append("check reports failure")

    return AcceptanceBundleCheck(name, command, status, required, findings)


def doctor_acceptance_bundle(bundle: Mapping[str, Any], *, repo: str | Path | None = None) -> AcceptanceBundleDoctorReport:
    """Validate a repo-only acceptance/evidence bundle without granting apply authority."""

    repo_root = _repo_root(repo)
    findings: list[str] = []

    if bundle.get("mode") != MODE:
        findings.append(f"bundle mode must be {MODE}")
    if bundle.get("live_mutation_authorized") is not False:
        findings.append("live_mutation_authorized must be false")
    if bundle.get("approval_manifest_created") is not False:
        findings.append("approval_manifest_created must be false")
    if bundle.get("apply_authority", "none") != "none":
        findings.append("apply_authority must be none")
    if bundle.get("target_paths") not in (None, []):
        findings.append("acceptance bundle must not carry live target paths")
    if bundle.get("findings") not in (None, []):
        findings.append("bundle findings must be empty before acceptance")

    artifacts_raw = bundle.get("artifacts")
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        findings.append("artifacts must be a non-empty list")
        artifacts_raw = []
    checks_raw = bundle.get("checks")
    if not isinstance(checks_raw, list) or not checks_raw:
        findings.append("checks must be a non-empty list")
        checks_raw = []

    artifacts = [_doctor_artifact(raw, repo_root) for raw in artifacts_raw]
    checks = [_doctor_check(raw) for raw in checks_raw]

    for artifact in artifacts:
        findings.extend(f"artifact {artifact.name or '<unnamed>'}: {issue}" for issue in artifact.findings)
    for check in checks:
        findings.extend(f"check {check.name or '<unnamed>'}: {issue}" for issue in check.findings)

    return AcceptanceBundleDoctorReport(
        mode=DOCTOR_MODE,
        status="accepted" if not findings else "blocked",
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo=str(repo_root),
        artifacts=artifacts,
        checks=checks,
        findings=findings,
        summary={
            "artifact_count": len(artifacts),
            "required_artifact_count": sum(1 for artifact in artifacts if artifact.required),
            "check_count": len(checks),
            "required_check_count": sum(1 for check in checks if check.required),
        },
        safety={
            "live_mutation_authorized": False,
            "approval_manifest_created": False,
            "apply_authority": "none",
            "targets": [],
        },
    )


def load_acceptance_bundle(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("acceptance bundle root must be a JSON object")
    return payload


def load_and_doctor_acceptance_bundle(path: str | Path, *, repo: str | Path | None = None) -> AcceptanceBundleDoctorReport:
    return doctor_acceptance_bundle(load_acceptance_bundle(path), repo=repo)


def acceptance_bundle_doctor_to_markdown(report: AcceptanceBundleDoctorReport) -> str:
    lines = [
        "# Acceptance Bundle Doctor",
        "",
        f"- mode: `{report.mode}`",
        f"- status: `{report.status}`",
        f"- repo: `{report.repo}`",
        f"- artifacts: {report.summary['artifact_count']}",
        f"- checks: {report.summary['check_count']}",
        "",
        "## Safety",
        "",
        f"- live_mutation_authorized: `{str(report.safety['live_mutation_authorized']).lower()}`",
        f"- approval_manifest_created: `{str(report.safety['approval_manifest_created']).lower()}`",
        f"- apply_authority: `{report.safety['apply_authority']}`",
        "",
        "## Findings",
        "",
    ]
    if report.findings:
        lines.extend(f"- {finding}" for finding in report.findings)
    else:
        lines.append("- none")
    lines.extend(["", "## Checks", ""])
    for check in report.checks:
        lines.append(f"- `{check.status}` {check.name}: `{check.command}`")
    lines.extend(["", "## Artifacts", ""])
    for artifact in report.artifacts:
        marker = "required" if artifact.required else "optional"
        exists = "exists" if artifact.exists else "missing"
        lines.append(f"- `{exists}` `{marker}` {artifact.name}: `{artifact.path}`")
    lines.append("")
    return "\n".join(lines)


def write_acceptance_bundle_doctor_report(report: AcceptanceBundleDoctorReport, out_dir: str | Path) -> tuple[Path, Path]:
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "acceptance-bundle-doctor.json"
    report_path = out / "REPORT.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(acceptance_bundle_doctor_to_markdown(report), encoding="utf-8")
    return json_path, report_path
