from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAX_EMBEDDING_FILES_PER_RUN = 75


@dataclass(frozen=True)
class IndexingManifestPolicy:
    live_mutation_enabled: bool = False
    max_files_per_run: int = 50
    protected_paths: list[str] = field(default_factory=list)
    generated_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndexingManifest:
    mode: str
    created_at: str
    files_seen: list[str]
    indexed: list[str]
    skipped: list[str]
    protected_skipped: list[str]
    generated_skipped: list[str]
    broken_links: list[dict[str, Any]]
    orphans: list[str]
    duplicates: list[dict[str, Any]]
    artifacts: dict[str, str]
    policy: IndexingManifestPolicy

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["policy"] = self.policy.to_dict()
        return payload


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndexingDoctorReport:
    mode: str
    status: str
    checks: list[DoctorCheck]
    findings: list[str]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = [check.to_dict() for check in self.checks]
        return payload


def build_indexing_manifest(
    *,
    files_seen: list[str],
    indexed: list[str],
    skipped: list[str],
    protected_skipped: list[str] | None = None,
    generated_skipped: list[str] | None = None,
    broken_links: list[dict[str, Any]] | None = None,
    orphans: list[str] | None = None,
    duplicates: list[dict[str, Any]] | None = None,
    artifacts: dict[str, str] | None = None,
    policy: IndexingManifestPolicy | dict[str, Any] | None = None,
    created_at: str | None = None,
) -> IndexingManifest:
    """Build a deterministic manifest from explicit records only."""
    normalized_policy = (
        policy
        if isinstance(policy, IndexingManifestPolicy)
        else IndexingManifestPolicy(**(policy or {}))
    )
    return IndexingManifest(
        mode="obsidian-layer.indexing-manifest.v1",
        created_at=created_at
        or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        files_seen=list(files_seen),
        indexed=list(indexed),
        skipped=list(skipped),
        protected_skipped=list(protected_skipped or []),
        generated_skipped=list(generated_skipped or []),
        broken_links=list(broken_links or []),
        orphans=list(orphans or []),
        duplicates=list(duplicates or []),
        artifacts=dict(artifacts or {}),
        policy=normalized_policy,
    )


def manifest_from_dict(payload: dict[str, Any]) -> IndexingManifest:
    policy_payload = payload.get("policy") or {}
    policy = (
        policy_payload
        if isinstance(policy_payload, IndexingManifestPolicy)
        else IndexingManifestPolicy(**policy_payload)
    )
    return IndexingManifest(
        mode=str(payload.get("mode", "")),
        created_at=str(payload.get("created_at", "")),
        files_seen=list(payload.get("files_seen", [])),
        indexed=list(payload.get("indexed", [])),
        skipped=list(payload.get("skipped", [])),
        protected_skipped=list(payload.get("protected_skipped", [])),
        generated_skipped=list(payload.get("generated_skipped", [])),
        broken_links=list(payload.get("broken_links", [])),
        orphans=list(payload.get("orphans", [])),
        duplicates=list(payload.get("duplicates", [])),
        artifacts=dict(payload.get("artifacts", {})),
        policy=policy,
    )


def validate_indexing_manifest(manifest: IndexingManifest) -> list[str]:
    findings: list[str] = []
    files_seen = set(manifest.files_seen)
    indexed = set(manifest.indexed)
    skipped = set(manifest.skipped)
    protected = set(manifest.protected_skipped)
    generated = set(manifest.generated_skipped)

    if manifest.mode != "obsidian-layer.indexing-manifest.v1":
        findings.append("manifest mode must be obsidian-layer.indexing-manifest.v1")
    if len(files_seen) != len(manifest.files_seen):
        findings.append("files_seen must not contain duplicates")
    if len(indexed) != len(manifest.indexed):
        findings.append("indexed must not contain duplicates")
    if len(skipped) != len(manifest.skipped):
        findings.append("skipped must not contain duplicates")
    if indexed & skipped:
        findings.append("indexed and skipped must be disjoint")
    if files_seen != indexed | skipped:
        findings.append("files_seen must equal indexed plus skipped")
    if not protected <= skipped:
        findings.append("protected_skipped must be tracked in skipped")
    if not generated <= skipped:
        findings.append("generated_skipped must be tracked in skipped")
    if protected & generated:
        findings.append("protected_skipped and generated_skipped must be disjoint")
    if manifest.policy.max_files_per_run < 1:
        findings.append("policy.max_files_per_run must be positive")
    return findings


def build_indexing_doctor_report(
    manifest: IndexingManifest,
    *,
    required_artifacts: list[str] | None = None,
    artifact_base: str | Path | None = None,
    max_embedding_files_per_run: int = MAX_EMBEDDING_FILES_PER_RUN,
) -> IndexingDoctorReport:
    validation_findings = validate_indexing_manifest(manifest)
    checks = [
        DoctorCheck("manifest_valid", not validation_findings, "; ".join(validation_findings) or "ok"),
        DoctorCheck(
            "protected_skips_tracked",
            set(manifest.protected_skipped) <= set(manifest.skipped),
            f"{len(manifest.protected_skipped)} protected skip(s)",
        ),
        DoctorCheck(
            "generated_skips_tracked",
            set(manifest.generated_skipped) <= set(manifest.skipped),
            f"{len(manifest.generated_skipped)} generated skip(s)",
        ),
        DoctorCheck(
            "embedding_max_files_per_run",
            manifest.policy.max_files_per_run <= max_embedding_files_per_run,
            f"{manifest.policy.max_files_per_run} <= {max_embedding_files_per_run}",
        ),
        DoctorCheck(
            "live_mutation_disabled",
            not manifest.policy.live_mutation_enabled,
            "live mutation disabled" if not manifest.policy.live_mutation_enabled else "live mutation enabled",
        ),
    ]

    missing = _missing_required_artifacts(
        manifest.artifacts,
        required_artifacts or [],
        artifact_base=artifact_base,
    )
    checks.append(
        DoctorCheck(
            "required_artifacts_present",
            not missing,
            "ok" if not missing else "missing: " + ", ".join(missing),
        )
    )
    findings = [check.detail for check in checks if not check.passed]
    return IndexingDoctorReport(
        mode="obsidian-layer.indexing-doctor.v1",
        status="ready-for-operator-review" if not findings else "blocked",
        checks=checks,
        findings=findings,
        summary={
            "files_seen": len(manifest.files_seen),
            "indexed": len(manifest.indexed),
            "skipped": len(manifest.skipped),
            "protected_skipped": len(manifest.protected_skipped),
            "generated_skipped": len(manifest.generated_skipped),
            "broken_links": len(manifest.broken_links),
            "orphans": len(manifest.orphans),
            "duplicates": len(manifest.duplicates),
            "artifacts": sorted(manifest.artifacts),
        },
    )


def _missing_required_artifacts(
    artifacts: dict[str, str],
    required: list[str],
    *,
    artifact_base: str | Path | None,
) -> list[str]:
    missing: list[str] = []
    base = Path(artifact_base).resolve() if artifact_base is not None else None
    for name in required:
        raw_path = artifacts.get(name)
        if not raw_path:
            missing.append(name)
            continue
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            if base is None:
                missing.append(name)
                continue
            path = base / path
        if not path.is_file():
            missing.append(name)
    return missing
