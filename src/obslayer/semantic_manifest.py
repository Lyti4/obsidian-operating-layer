from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError, write_json

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEMANTIC_MANIFEST_OUT = REPO_ROOT / "out" / "reports" / "semantic-manifests"


@dataclass(frozen=True)
class SemanticManifestArtifact:
    name: str
    path: str
    mode: str | None
    status: str | None
    exists: bool
    safety_ok: bool
    summary: dict[str, Any]
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticManifest:
    mode: str
    status: str
    created_at: str
    repo: str
    artifacts: list[SemanticManifestArtifact]
    summary: dict[str, Any]
    live_mutation_authorized: bool
    approval_manifest_created: bool
    findings: list[str]
    next_safe_step: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = [artifact.to_dict() for artifact in self.artifacts]
        return payload


def _repo_root(repo: str | Path | None = None) -> Path:
    return Path(repo).expanduser().resolve() if repo is not None else REPO_ROOT


def _require_under_repo_out(path: str | Path, repo: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    out_root = (repo / "out").resolve()
    try:
        resolved.relative_to(out_root)
    except ValueError as exc:
        raise GuardrailError(f"semantic manifest artifacts must live under repo out/: {resolved}") from exc
    return resolved


def _load_json_artifact(name: str, path: Path, repo: Path) -> SemanticManifestArtifact:
    findings: list[str] = []
    if not path.is_file():
        return SemanticManifestArtifact(name, str(path), None, None, False, False, {}, ["missing artifact"])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return SemanticManifestArtifact(name, str(path), None, None, True, False, {}, [f"invalid json: {exc}"])
    if not isinstance(payload, dict):
        return SemanticManifestArtifact(name, str(path), None, None, True, False, {}, ["artifact root is not object"])

    mode = payload.get("mode") if isinstance(payload.get("mode"), str) else None
    status = payload.get("status") if isinstance(payload.get("status"), str) else None
    if payload.get("live_mutation_authorized") is not None and payload.get("live_mutation_authorized") is not False:
        findings.append("live_mutation_authorized must be false")
    if payload.get("approval_manifest_created") is not None and payload.get("approval_manifest_created") is not False:
        findings.append("approval_manifest_created must be false")
    targets = payload.get("targets")
    if targets is not None and targets != []:
        findings.append("semantic proposal artifact must not contain edit targets")
    safety = payload.get("safety")
    if isinstance(safety, dict):
        if safety.get("live_mutation") is not None and safety.get("live_mutation") is not False:
            findings.append("safety.live_mutation must be false")
        if safety.get("live_mutation_authorized") is not None and safety.get("live_mutation_authorized") is not False:
            findings.append("safety.live_mutation_authorized must be false")
        if safety.get("approval_manifest_created") is not None and safety.get("approval_manifest_created") is not False:
            findings.append("safety.approval_manifest_created must be false")

    summary: dict[str, Any] = {}
    for key in (
        "records",
        "processed",
        "skipped",
        "embedded_files",
        "embedding_sidecar_files",
        "chunks_indexed",
        "item_count",
        "candidate_count",
        "targets",
        "candidates",
        "groups",
    ):
        if key in payload:
            value = payload[key]
            if isinstance(value, list):
                summary[key] = len(value)
            elif isinstance(value, (str, int, float, bool)) or value is None:
                summary[key] = value
    if "graph_summary" in payload and isinstance(payload["graph_summary"], dict):
        summary["graph_summary"] = payload["graph_summary"]

    return SemanticManifestArtifact(name, str(path), mode, status, True, not findings, summary, findings)



def _read_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _candidate_pointer_paths(pointer: str, *, repo: Path, source_artifact: Path) -> tuple[Path, ...]:
    raw = Path(pointer).expanduser()
    if raw.is_absolute():
        return (raw.resolve(),)
    return (
        (repo / raw).resolve(),
        (source_artifact.parent / raw).resolve(),
    )


def _same_resolved_path(left: Any, right: Path, *, repo: Path, source_artifact: Path) -> bool:
    if not isinstance(left, str) or not left.strip():
        return False
    expected = right.resolve()
    return any(candidate == expected for candidate in _candidate_pointer_paths(left, repo=repo, source_artifact=source_artifact))


def _chain_findings(paths: dict[str, Path], *, repo: Path) -> list[str]:
    payloads = {name: _read_payload(path) for name, path in paths.items()}
    checks = (
        ("embedding_run", "manifest", "graphify_embedding_manifest"),
        ("query_smoke", "run_json", "embedding_run"),
        ("semantic_query_proposal", "query_smoke_json", "query_smoke"),
        ("candidate_decision_packet", "source_proposal", "semantic_query_proposal"),
        ("targeted_semantic_proposal", "source_decision_packet", "candidate_decision_packet"),
        ("semantic_review_index", "source_proposal", "targeted_semantic_proposal"),
    )
    findings: list[str] = []
    for source_name, source_key, target_name in checks:
        source_payload = payloads.get(source_name) or {}
        expected_path = paths[target_name]
        if source_key not in source_payload:
            findings.append(f"{source_name}: missing chain pointer {source_key}")
        elif not _same_resolved_path(source_payload[source_key], expected_path, repo=repo, source_artifact=paths[source_name]):
            findings.append(f"{source_name}: {source_key} does not point to {target_name}")
    return findings


def build_semantic_manifest(
    *,
    repo: str | Path | None = None,
    embedding_manifest: str | Path,
    embedding_run: str | Path,
    query_smoke: str | Path,
    semantic_proposal: str | Path,
    decision_packet: str | Path,
    targeted_proposal: str | Path,
    review_index: str | Path,
    created_at: str | None = None,
) -> SemanticManifest:
    repo_path = _repo_root(repo)
    paths = {
        "graphify_embedding_manifest": _require_under_repo_out(embedding_manifest, repo_path),
        "embedding_run": _require_under_repo_out(embedding_run, repo_path),
        "query_smoke": _require_under_repo_out(query_smoke, repo_path),
        "semantic_query_proposal": _require_under_repo_out(semantic_proposal, repo_path),
        "candidate_decision_packet": _require_under_repo_out(decision_packet, repo_path),
        "targeted_semantic_proposal": _require_under_repo_out(targeted_proposal, repo_path),
        "semantic_review_index": _require_under_repo_out(review_index, repo_path),
    }
    artifacts = [_load_json_artifact(name, path, repo_path) for name, path in paths.items()]
    findings = [f"{artifact.name}: {finding}" for artifact in artifacts for finding in artifact.findings]
    if all(artifact.exists for artifact in artifacts):
        findings.extend(_chain_findings(paths, repo=repo_path))
    summary = {
        "artifact_count": len(artifacts),
        "existing_artifacts": sum(1 for artifact in artifacts if artifact.exists),
        "safe_artifacts": sum(1 for artifact in artifacts if artifact.safety_ok),
        "missing_artifacts": [artifact.name for artifact in artifacts if not artifact.exists],
        "pipeline": [artifact.name for artifact in artifacts],
    }
    return SemanticManifest(
        mode="semantic-indexing-manifest",
        status="ready-for-operator-review" if not findings else "blocked",
        created_at=created_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo=str(repo_path),
        artifacts=artifacts,
        summary=summary,
        live_mutation_authorized=False,
        approval_manifest_created=False,
        findings=findings,
        next_safe_step=(
            "Use this manifest as the acceptance index for semantic/indexing evidence; any live apply still requires "
            "a separate explicit approval manifest, backup, apply, and verify cycle."
        ),
    )


def semantic_manifest_to_markdown(manifest: SemanticManifest) -> str:
    lines = [
        "# Semantic Indexing Manifest",
        "",
        f"Status: `{manifest.status}`",
        f"Mode: `{manifest.mode}`",
        f"Created UTC: `{manifest.created_at}`",
        f"Repo: `{manifest.repo}`",
        f"Live mutation authorized: `{manifest.live_mutation_authorized}`",
        f"Approval manifest created: `{manifest.approval_manifest_created}`",
        "",
        "## Artifact chain",
        "",
        "| artifact | exists | safety | mode | status | path |",
        "|---|---:|---:|---|---|---|",
    ]
    for artifact in manifest.artifacts:
        path = artifact.path.replace("|", "\\|")
        lines.append(
            f"| `{artifact.name}` | `{artifact.exists}` | `{artifact.safety_ok}` | "
            f"`{artifact.mode or 'n/a'}` | `{artifact.status or 'n/a'}` | `{path}` |"
        )
    lines.extend(["", "## Summary", ""])
    for key, value in manifest.summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Findings", ""])
    if manifest.findings:
        lines.extend(f"- {finding}" for finding in manifest.findings)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Safety boundary",
        "",
        "- This is a manifest/index over generated semantic and indexing artifacts only.",
        "- It does not authorize live vault mutation.",
        "- It does not create an approval manifest.",
        "- Generated artifacts remain under `out/` and ignored by git; this report is evidence, not source of truth.",
        "",
        "## Next safe step",
        "",
        manifest.next_safe_step,
        "",
    ])
    return "\n".join(lines)


def write_semantic_manifest(*, out_dir: str | Path, **kwargs: Any) -> dict[str, str]:
    out = _require_under_repo_out(out_dir, _repo_root(kwargs.get("repo")))
    manifest = build_semantic_manifest(**kwargs)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "semantic-manifest.json"
    report_path = out / "REPORT.md"
    write_json(manifest_path, manifest.to_dict())
    report_path.write_text(semantic_manifest_to_markdown(manifest), encoding="utf-8")
    return {
        "status": manifest.status,
        "manifest": str(manifest_path),
        "report": str(report_path),
        "findings": str(len(manifest.findings)),
        "artifacts": str(len(manifest.artifacts)),
    }
