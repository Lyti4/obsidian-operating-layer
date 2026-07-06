from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError

MODE = "obslayer.candidate-volume-operator-packet.v1"
ALLOWED_PREFIXES = ("out", "docs")
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
PROTECTED_BUCKETS = ("_Backups", "_Archive", ".obsidian", ".trash", "Soul")


@dataclass(frozen=True)
class CandidateVolumeOperatorPacket:
    mode: str
    generated_at: str
    repo_root: str
    status: str
    vault_root: str
    observed_at: str | None
    file_counts: dict[str, int]
    protected_hits_count: int
    protected_bucket_counts: dict[str, int]
    sample_notes_count: int
    proposal: dict[str, Any]
    verify: dict[str, Any]
    unified: dict[str, Any]
    route_buckets: dict[str, list[str]]
    safety: dict[str, Any]
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        # Mirror fixed inert safety at the root for compatibility with
        # unified/operator gate validators that inspect top-level authority fields.
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


def _load_object(path: str | Path, repo: Path, *, purpose: str) -> dict[str, Any]:
    resolved, _ = _repo_local_path(path, repo, purpose=purpose)
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardrailError(f"{purpose} must be a JSON object: {resolved}")
    return payload


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


def _protected_bucket(path_value: Any) -> str:
    path = str(path_value or "").lstrip("/")
    for bucket in PROTECTED_BUCKETS:
        if path == bucket or path.startswith(f"{bucket}/"):
            return bucket
    return "other"


def _protected_hit_path(hit: Any) -> str:
    if isinstance(hit, dict):
        for key in ("path", "file", "target", "note"):
            value = hit.get(key)
            if isinstance(value, str):
                return value
    return str(hit)


def _protected_bucket_counts(protected_hits: Any) -> tuple[int, dict[str, int]]:
    counts = {bucket: 0 for bucket in (*PROTECTED_BUCKETS, "other")}
    if not isinstance(protected_hits, list):
        return 0, counts
    for hit in protected_hits:
        counts[_protected_bucket(_protected_hit_path(hit))] += 1
    return len(protected_hits), counts


def _file_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    counts: dict[str, int] = {}
    for key, count in value.items():
        if isinstance(count, int):
            counts[str(key)] = count
    return counts


def _proposal_summary(proposal: dict[str, Any]) -> dict[str, Any]:
    targets = proposal.get("targets")
    targets_count = len(targets) if isinstance(targets, list) else 0
    return {
        "mode": proposal.get("mode"),
        "dry_run_default": proposal.get("dry_run_default"),
        "approval_required": proposal.get("approval_required"),
        "targets_count": targets_count,
        "risk_class": proposal.get("risk_class"),
    }


def _verify_summary(verify: dict[str, Any]) -> dict[str, Any]:
    issues = verify.get("issues")
    return {"ok": verify.get("ok"), "issues_count": len(issues) if isinstance(issues, list) else 0}


def _unified_summary(unified: dict[str, Any]) -> dict[str, Any]:
    summary = unified.get("summary") if isinstance(unified.get("summary"), dict) else {}
    return {
        "status": unified.get("status"),
        "blocked_count": int(summary.get("blocked_count") or 0),
        "missing_count": int(summary.get("missing_count") or summary.get("missing_artifacts") or 0),
        "proposal_only_count": int(summary.get("proposal_only_count") or 0),
        "ready_for_human_review_count": int(summary.get("ready_for_human_review_count") or 0),
    }


def _target_label(target: Any, index: int) -> str:
    if isinstance(target, dict):
        for key in ("path", "target_path", "file"):
            value = target.get(key)
            if isinstance(value, str) and value:
                return value
    return f"targets[{index}]"


def build_candidate_volume_operator_packet(
    *,
    repo: str | Path | None = None,
    observation: str | Path,
    proposal: str | Path,
    verify: str | Path,
    unified_index: str | Path,
) -> CandidateVolumeOperatorPacket:
    repo_path = _repo_root(repo)
    observation_payload = _load_object(observation, repo_path, purpose="observation input")
    proposal_payload = _load_object(proposal, repo_path, purpose="proposal input")
    verify_payload = _load_object(verify, repo_path, purpose="verify input")
    unified_payload = _load_object(unified_index, repo_path, purpose="unified index input")

    findings: list[str] = []
    for name, payload in (
        ("observation", observation_payload),
        ("proposal", proposal_payload),
        ("verify", verify_payload),
        ("unified_index", unified_payload),
    ):
        findings.extend(f"{name}.{finding}" for finding in _authority_findings(payload))

    protected_hits_count, protected_bucket_counts = _protected_bucket_counts(observation_payload.get("protected_hits"))
    proposal_summary = _proposal_summary(proposal_payload)
    verify_summary = _verify_summary(verify_payload)
    unified_summary = _unified_summary(unified_payload)

    route_buckets = {
        "blocked": list(findings),
        "protected_manual_review": [],
        "proposal_only_ready": [],
        "stale_missing_artifact_cleanup": [],
        "first_manifest_candidate_queue": [],
    }
    targets = proposal_payload.get("targets")
    if isinstance(targets, list) and targets:
        route_buckets["protected_manual_review"].extend(_target_label(target, index) for index, target in enumerate(targets))
        route_buckets["proposal_only_ready"].append(
            f"proposal has {len(targets)} target(s); manual review only, no manifest authority"
        )
    else:
        route_buckets["proposal_only_ready"].append("proposal has no targets; operator volume checkpoint only")
    if unified_summary["missing_count"]:
        route_buckets["stale_missing_artifact_cleanup"].append(
            f"unified index reports {unified_summary['missing_count']} missing artifact(s)"
        )
    if verify_summary["ok"] is not True or verify_summary["issues_count"]:
        route_buckets["blocked"].append("verify evidence is not clean")
    if unified_summary["blocked_count"]:
        route_buckets["blocked"].append(f"unified index reports {unified_summary['blocked_count']} blocked artifact(s)")

    status = "blocked" if route_buckets["blocked"] else "ready_for_operator_review"
    return CandidateVolumeOperatorPacket(
        mode=MODE,
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo_root=str(repo_path),
        status=status,
        vault_root=str(observation_payload.get("vault_root") or ""),
        observed_at=observation_payload.get("observed_at") if isinstance(observation_payload.get("observed_at"), str) else None,
        file_counts=_file_counts(observation_payload.get("file_counts")),
        protected_hits_count=protected_hits_count,
        protected_bucket_counts=protected_bucket_counts,
        sample_notes_count=len(observation_payload.get("sample_notes")) if isinstance(observation_payload.get("sample_notes"), list) else 0,
        proposal=proposal_summary,
        verify=verify_summary,
        unified=unified_summary,
        route_buckets=route_buckets,
        safety={**SAFETY},
        findings=findings,
    )


def candidate_volume_operator_packet_to_markdown(packet: CandidateVolumeOperatorPacket) -> str:
    lines = [
        "# Candidate Volume Operator Packet",
        "",
        f"- mode: `{packet.mode}`",
        f"- status: `{packet.status}`",
        f"- generated_at: `{packet.generated_at}`",
        f"- vault_root: `{packet.vault_root}`",
        f"- observed_at: `{packet.observed_at}`",
        "",
        "## Safety",
        "- live_mutation_authorized: `false`",
        "- approval_manifest_created: `false`",
        "- approval_manifest_authority: `false`",
        "- apply_authority: `none`",
        "- target_paths: `[]`",
        "",
        "## Volume",
        f"- sample_notes_count: `{packet.sample_notes_count}`",
        f"- protected_hits_count: `{packet.protected_hits_count}`",
    ]
    for extension, count in sorted(packet.file_counts.items()):
        lines.append(f"- file_counts[{extension}]: `{count}`")
    for bucket, count in packet.protected_bucket_counts.items():
        lines.append(f"- protected_bucket_counts[{bucket}]: `{count}`")
    lines.extend(["", "## Proposal / Verify / Unified"])
    for key, value in packet.proposal.items():
        lines.append(f"- proposal.{key}: `{value}`")
    for key, value in packet.verify.items():
        lines.append(f"- verify.{key}: `{value}`")
    for key, value in packet.unified.items():
        lines.append(f"- unified.{key}: `{value}`")
    lines.extend(["", "## Route Buckets"])
    for bucket, values in packet.route_buckets.items():
        rendered = ", ".join(values) if values else "[]"
        lines.append(f"- {bucket}: `{rendered}`")
    lines.append("")
    return "\n".join(lines)


def write_candidate_volume_operator_packet(
    packet: CandidateVolumeOperatorPacket, out_dir: str | Path
) -> tuple[Path, Path]:
    repo = _repo_root(packet.repo_root)
    out, _ = _repo_local_path(out_dir, repo, purpose="candidate volume packet output")
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "candidate-volume-operator-packet.json"
    report_path = out / "REPORT.md"
    json_path.write_text(json.dumps(packet.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(candidate_volume_operator_packet_to_markdown(packet), encoding="utf-8")
    return json_path, report_path
