from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .guardrails import GuardrailError

MODE = "obslayer.unified-control-plane-index.v1"
OUTPUT_ROOT = "out/reports/unified-control-plane-index"
ALLOWED_INPUT_PREFIXES = ("out/reports", "out/proposals", "docs")
MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_REPORTS = 50
DEFAULT_DISCOVERY_LIMIT = 200
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
SAFE_APPLY_VALUES = {None, False, "", "false", "none", "no", "0"}
TRUE_STRINGS = {"1", "true", "yes", "y", "enabled", "enable", "approved", "authorize", "authorized"}
CANONICAL_DOCS: tuple[tuple[str, str], ...] = (
    ("docs/acceptance/index.md", "accepted-capability-ledger"),
    ("docs/spec-kit/35-agentic-os-control-plane-map.md", "control-plane-map"),
    ("docs/spec-kit/36-current-evidence-index.md", "current-evidence-index"),
    ("docs/spec-kit/38-unified-queue-state-decision-surface-v1.md", "queue-state-vocabulary"),
    ("docs/spec-kit/40-indexing-manifest-and-doctor-contract.md", "indexing-doctor-contract"),
    ("docs/spec-kit/47-unified-operator-review-index.md", "operator-review-index-spec"),
    ("docs/spec-kit/49-manifest-candidate-selector.md", "manifest-candidate-selector-spec"),
    ("docs/spec-kit/50-unified-control-plane-evidence-index.md", "unified-control-plane-index-spec"),
    ("docs/triage/kanban-board.md", "triage-board"),
)
FAMILY_CANONICAL_DOCS: dict[str, str | None] = {
    "manifest-candidate-selector": "docs/spec-kit/49-manifest-candidate-selector.md",
    "unified-operator-review-index": "docs/spec-kit/47-unified-operator-review-index.md",
    "unified-control-plane-index": "docs/spec-kit/50-unified-control-plane-evidence-index.md",
}
OPTIONAL_GENERATED_PATHS = (
    "out/reports/nanobot-cron-scout/20260707T093200Z/REPORT.md",
    "out/reports/nanobot-hermes-reviewer/20260707T093248Z/REPORT.md",
    "out/reports/manifest-candidate-selector/grouped-next5-smoke/REPORT.md",
    "out/reports/unified-operator-review-index/hermes-smoke/REPORT.md",
    "out/reports/candidate-volume-operator-packet/full-vault-proposal-only-20260706T182612Z/REPORT.md",
)
KNOWN_REPORT_FAMILIES = (
    "nanobot-cron-scout",
    "nanobot-hermes-reviewer",
    "nanobot-companion-deep-review",
    "manifest-candidate-selector",
    "unified-operator-review-index",
    "candidate-volume-operator-packet",
    "operator-review-packet",
)
NOISE_PATTERNS = (
    "provider quota",
    "quota exceeded",
    "oauth",
    "auth missing",
    "authentication missing",
    "dry-run no-op",
    "dry run no-op",
    "empty dry-run",
    "empty dry run",
    "runtime failure without project evidence",
)
READY_PATTERNS = (
    "proposal candidate",
    "proposal candidates",
    "review item",
    "review items",
    "next action",
    "next actions",
    "operator review",
    "ready_for_operator_review",
    "ready for operator review",
    "concrete proposal",
)
BLOCKED_PATTERNS = (
    "status: blocked",
    "current task status: blocked",
    "current card status: blocked",
    "verdict: blocker",
    "current report verdict: blocker",
    "required verification failed",
    "verification failed",
)
HISTORICAL_ACCEPTED_PATTERNS = (
    "post-verify passed",
    "post verify passed",
    "backup recorded",
    "explicit operator approval",
    "accepted for the single",
    "not a standing authorization",
    "historical/stale evidence",
    "already applied",
)


@dataclass(frozen=True)
class CanonicalDoc:
    path: str
    exists: bool
    role: str
    status_hint: str
    summary: str
    stable_key: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["source_path"] = self.path
        payload["canonical_doc"] = self.path
        return payload


@dataclass(frozen=True)
class EvidenceArtifact:
    path: str
    exists: bool
    kind: str
    source: str
    classification: str
    reason: str
    safe_to_dispatch: bool
    stable_key: str
    artifact_family: str | None
    artifact_stamp: str | None
    authority_state: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["source_path"] = self.path
        payload["canonical_doc"] = FAMILY_CANONICAL_DOCS.get(self.artifact_family)
        return payload


@dataclass(frozen=True)
class WorkerSignal:
    worker: str
    path: str
    signal: str
    recommended_owner: str
    requires_human_approval: bool
    stable_key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NextAction:
    id: str
    title: str
    owner: str
    stage: str
    allowed_scope: list[str]
    forbidden_scope: list[str]
    blocked_by: list[str]
    acceptance: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnifiedControlPlaneIndex:
    mode: str
    generated_at: str
    repo_root: str
    git: dict[str, Any]
    safety: dict[str, Any]
    canonical_docs: list[CanonicalDoc]
    evidence_artifacts: list[EvidenceArtifact]
    worker_signals: list[WorkerSignal]
    queue_state: dict[str, int]
    next_actions: list[NextAction]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["canonical_docs"] = [doc.to_dict() for doc in self.canonical_docs]
        payload["evidence_artifacts"] = [artifact.to_dict() for artifact in self.evidence_artifacts]
        payload["worker_signals"] = [signal.to_dict() for signal in self.worker_signals]
        payload["next_actions"] = [action.to_dict() for action in self.next_actions]
        return payload


def _repo_root(repo: str | Path | None = None) -> Path:
    return Path(repo).expanduser().resolve() if repo is not None else Path.cwd().resolve()


def _run_git(repo: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_state(repo: Path) -> dict[str, Any]:
    status_short = [line for line in _run_git(repo, ["status", "--short"]).splitlines() if line]
    return {
        "head": _run_git(repo, ["rev-parse", "--short", "HEAD"]) or "unknown",
        "branch": _run_git(repo, ["branch", "--show-current"]) or "unknown",
        "dirty": bool(status_short),
        "status_short": status_short,
    }


def _relative_to_repo(path: str | Path, repo: Path) -> tuple[Path, str]:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    try:
        rel = resolved.relative_to(repo)
    except ValueError as exc:
        raise GuardrailError(f"unified control-plane evidence path escapes repo: {resolved}") from exc
    rel_posix = rel.as_posix()
    if not any(rel_posix == prefix or rel_posix.startswith(f"{prefix}/") for prefix in ALLOWED_INPUT_PREFIXES):
        raise GuardrailError(
            "unified control-plane evidence inputs must stay under repo docs/, out/reports/, or out/proposals/: "
            f"{rel_posix}"
        )
    return resolved, rel_posix


def _output_dir(path: str | Path, repo: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    root = (repo / OUTPUT_ROOT).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise GuardrailError(f"unified control-plane output must stay under repo {OUTPUT_ROOT}/: {resolved}") from exc
    return resolved


def _status_hint(text: str) -> str:
    lowered = text.lower()
    if "accepted" in lowered:
        return "accepted"
    if "active" in lowered or "current" in lowered:
        return "active"
    if "proposed" in lowered or "proposal" in lowered:
        return "proposed"
    return "unknown"


def _summary(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip(" #\t")
        if line:
            return line[:160]
    return ""


def _spec_stable_key(rel_path: str) -> str:
    path = Path(rel_path)
    if rel_path.startswith("docs/spec-kit/"):
        slug = path.stem
        match = re.match(r"(?P<number>\d+)-(?P<name>.+)", slug)
        if match:
            return f"obslayer.spec.{match.group('number')}-{match.group('name')}"
        return f"obslayer.spec.{slug}"
    digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:16]
    return f"obslayer.path.{digest}"


def _canonical_doc(repo: Path, rel_path: str, role: str) -> CanonicalDoc:
    path = repo / rel_path
    if not path.exists():
        return CanonicalDoc(rel_path, False, role, "unknown", "missing canonical doc", _spec_stable_key(rel_path))
    text = path.read_text(encoding="utf-8", errors="replace")
    return CanonicalDoc(rel_path, True, role, _status_hint(text[:4096]), _summary(text), _spec_stable_key(rel_path))


def _kind(path: Path, rel_path: str) -> str:
    if rel_path.startswith("docs/"):
        return "doc"
    if path.suffix == ".json":
        name = path.name.lower()
        if "selector" in name:
            return "selector"
        if "review" in name:
            return "review"
        if "index" in name:
            return "index"
        return "index"
    if rel_path.startswith("out/proposals/"):
        return "proposal"
    if path.name == "REPORT.md" or path.suffix == ".md":
        return "report"
    return "unknown"


def _family_stamp(rel_path: str) -> tuple[str | None, str | None]:
    parts = Path(rel_path).parts
    if len(parts) >= 4 and parts[0] == "out" and parts[1] in {"reports", "proposals"}:
        family = parts[2]
        stamp = parts[3] if len(parts) >= 5 else None
        return family, stamp
    return None, None


def _artifact_stable_key(rel_path: str) -> str:
    family, stamp = _family_stamp(rel_path)
    path = Path(rel_path)
    if family and stamp and path.name == "REPORT.md":
        return f"obslayer.report.{family}.{stamp}"
    if family and stamp:
        stem = re.sub(r"[^a-zA-Z0-9_.-]+", "-", path.stem)
        return f"obslayer.artifact.{family}.{stamp}.{stem}"
    if rel_path.startswith("docs/spec-kit/") or rel_path.startswith("docs/"):
        return _spec_stable_key(rel_path)
    digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:16]
    return f"obslayer.path.{digest}"


def _source(rel_path: str, text: str = "") -> str:
    lowered = f"{rel_path}\n{text[:4096]}".lower()
    if "nanobot" in lowered:
        return "nanobot"
    if "companion" in lowered:
        return "companion"
    if "codex" in lowered:
        return "codex"
    if "hermes" in lowered:
        return "hermes"
    if rel_path.startswith("out/"):
        return "tool"
    return "unknown"


def _worker_from_source(source: str) -> str:
    if source in {"nanobot", "companion", "codex", "hermes"}:
        return source
    return "unknown"


def _recommended_owner(text: str, classification: str) -> str:
    lowered = text.lower()
    if classification == "blocked":
        return "Hermes"
    if "codex" in lowered:
        return "Codex"
    if "ops" in lowered:
        return "Ops"
    if "dmitry" in lowered:
        return "Dmitry"
    if "docs" in lowered:
        return "Docs"
    if "nanobot" in lowered:
        return "Nanobot"
    return "Hermes"


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


def _text_authority_findings(text: str) -> list[str]:
    lowered = text.lower()
    findings: list[str] = []
    if re.search(r"live_mutation_authorized\s*[:=]\s*true\b", lowered):
        findings.append("live_mutation_authorized claims apply/approval authority")
    if re.search(r"approval_manifest_created\s*[:=]\s*true\b", lowered):
        findings.append("approval_manifest_created claims apply/approval authority")
    if re.search(r"approval_manifest_authority\s*[:=]\s*true\b", lowered):
        findings.append("approval_manifest_authority claims apply/approval authority")
    if re.search(r"apply_authority\s*[:=]\s*(?!none\b|false\b|no\b|0\b)[a-z0-9_-]+", lowered):
        findings.append("apply_authority claims apply/approval authority")
    if re.search(r"target_paths\s*[:=]\s*\[[^\]\s]+", lowered):
        findings.append("target_paths claims apply/approval authority")
    return findings


def _is_historical_accepted(text: str, rel_path: str, accepted_text: str) -> bool:
    lowered = text.lower()
    accepted_lowered = accepted_text.lower()
    family, _stamp = _family_stamp(rel_path)
    accepted_path_or_family = rel_path.lower() in accepted_lowered or (family is not None and family.lower() in accepted_lowered)
    has_historical_signal = "live apply" in lowered and any(pattern in lowered for pattern in HISTORICAL_ACCEPTED_PATTERNS)
    return has_historical_signal and (accepted_path_or_family or "explicit operator approval" in lowered)




def _looks_stale_or_empty_checkpoint(text: str, payload: dict[str, Any] | None = None) -> bool:
    lowered = text.lower()
    stale_patterns = [
        "historical/stale",
        "historical stale",
        "must not be reused",
        "noop_already_applied",
        "already applied",
        "stale-noop",
        "stale noop",
    ]
    if any(pattern in lowered for pattern in stale_patterns):
        return True
    if not payload:
        return False
    status = str(payload.get("status", "")).strip().lower()
    if status in {"no_candidate", "noop_already_applied", "already_applied", "stale", "no_op", "noop"}:
        return True
    review_items = payload.get("review_items")
    if isinstance(review_items, list) and not review_items and status in {"", "no_candidate", "ready_for_operator_review"}:
        return True
    proposal = payload.get("proposal")
    if isinstance(proposal, dict):
        targets_count = proposal.get("targets_count")
        queue = proposal.get("first_manifest_candidate_queue")
        if targets_count == 0 and isinstance(queue, list) and not queue:
            return True
    if payload.get("targets_count") == 0 and payload.get("first_manifest_candidate_queue") == []:
        return True
    return False


def _looks_noise(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in NOISE_PATTERNS)


def _looks_ready(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in READY_PATTERNS)


def _looks_blocked(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in BLOCKED_PATTERNS)


def _read_text_artifact(path: Path, warnings: list[str]) -> str | None:
    size = path.stat().st_size
    if size > MAX_ARTIFACT_BYTES:
        warnings.append(f"skipped oversized artifact {path.name}: {size} bytes")
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _json_text_and_payload(path: Path, warnings: list[str]) -> tuple[str, dict[str, Any] | None]:
    text = _read_text_artifact(path, warnings)
    if text is None:
        return "", None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text, None
    if not isinstance(payload, dict):
        return text, None
    return text, payload


def _artifact(path: str | Path, repo: Path, accepted_text: str) -> EvidenceArtifact:
    resolved, rel_path = _relative_to_repo(path, repo)
    family, stamp = _family_stamp(rel_path)
    stable_key = _artifact_stable_key(rel_path)
    kind = _kind(resolved, rel_path)
    warnings: list[str] = []
    if not resolved.exists():
        return EvidenceArtifact(
            rel_path,
            False,
            kind,
            _source(rel_path),
            "missing_optional",
            "missing optional artifact path",
            False,
            stable_key,
            family,
            stamp,
            "none",
            ["missing optional artifact"],
        )
    if resolved.is_dir():
        return EvidenceArtifact(
            rel_path,
            True,
            "unknown",
            _source(rel_path),
            "informational",
            "directory pointer only",
            False,
            stable_key,
            family,
            stamp,
            "none",
            warnings,
        )

    text = ""
    payload: dict[str, Any] | None = None
    if resolved.suffix == ".json":
        text, payload = _json_text_and_payload(resolved, warnings)
    else:
        maybe_text = _read_text_artifact(resolved, warnings)
        text = maybe_text or ""
    source = _source(rel_path, text)
    if text == "" and warnings:
        return EvidenceArtifact(
            rel_path,
            True,
            kind,
            source,
            "informational",
            "; ".join(warnings),
            False,
            stable_key,
            family,
            stamp,
            "none",
            warnings,
        )

    findings = _authority_findings(payload) if payload is not None else _text_authority_findings(text)
    if findings:
        return EvidenceArtifact(
            rel_path,
            True,
            kind,
            source,
            "blocked",
            "; ".join(findings),
            False,
            stable_key,
            family,
            stamp,
            "requires_explicit_approval",
            warnings,
        )
    if _is_historical_accepted(text, rel_path, accepted_text):
        return EvidenceArtifact(
            rel_path,
            True,
            kind,
            source,
            "accepted_or_closed_evidence",
            "historical accepted live-apply evidence, not active authority",
            False,
            stable_key,
            family,
            stamp,
            "historical_accepted",
            warnings,
        )
    if _looks_noise(text):
        return EvidenceArtifact(
            rel_path,
            True,
            kind,
            source,
            "noise_or_trash",
            "provider/auth/dry-run/no-op/runtime-failure noise",
            False,
            stable_key,
            family,
            stamp,
            "none",
            warnings,
        )
    if _looks_stale_or_empty_checkpoint(text, payload):
        return EvidenceArtifact(
            rel_path,
            True,
            kind,
            source,
            "stale",
            "stale/no-op/empty checkpoint evidence; not dispatch-ready",
            False,
            stable_key,
            family,
            stamp,
            "none",
            warnings,
        )
    if _looks_blocked(text):
        return EvidenceArtifact(
            rel_path,
            True,
            kind,
            source,
            "blocked",
            "current unresolved blocker or failed verification",
            False,
            stable_key,
            family,
            stamp,
            "requires_explicit_approval",
            warnings,
        )
    if _looks_ready(text):
        return EvidenceArtifact(
            rel_path,
            True,
            kind,
            source,
            "ready_for_operator_review",
            "concrete proposal/review/next-action artifact with inert safety",
            True,
            stable_key,
            family,
            stamp,
            "proposal_only",
            warnings,
        )
    if rel_path.lower() in accepted_text.lower():
        return EvidenceArtifact(
            rel_path,
            True,
            kind,
            source,
            "accepted_or_closed_evidence",
            "path appears in accepted/closed docs",
            False,
            stable_key,
            family,
            stamp,
            "historical_accepted",
            warnings,
        )
    return EvidenceArtifact(
        rel_path,
        True,
        kind,
        source,
        "informational",
        "repo-local evidence pointer",
        False,
        stable_key,
        family,
        stamp,
        "none",
        warnings,
    )


def _safe_discovery_candidate(path: Path) -> bool:
    parts = path.parts
    if any(part.startswith(".") for part in parts):
        return False
    lowered = path.as_posix().lower()
    if any(token in lowered for token in ("secret", "credential", "token", ".env", "cache", "__pycache__")):
        return False
    return path.name == "REPORT.md" or path.suffix == ".json"


def _default_artifacts(repo: Path, max_reports: int) -> list[Path]:
    paths = [repo / rel for rel in OPTIONAL_GENERATED_PATHS]
    discovered: list[Path] = []
    inspected = 0
    for family in KNOWN_REPORT_FAMILIES:
        root = repo / "out" / "reports" / family
        if not root.is_dir():
            continue
        latest_child = next((child for child in sorted(root.iterdir(), key=lambda item: item.name, reverse=True) if child.is_dir()), None)
        if latest_child is None:
            for child in sorted(root.iterdir(), key=lambda item: item.name, reverse=True):
                inspected += 1
                if inspected > DEFAULT_DISCOVERY_LIMIT:
                    break
                if child.is_file() and _safe_discovery_candidate(child):
                    discovered.append(child)
                    break
            continue
        inspected += 1
        for candidate in sorted(latest_child.iterdir()):
            if len(discovered) >= max_reports or inspected > DEFAULT_DISCOVERY_LIMIT:
                break
            if candidate.is_file() and _safe_discovery_candidate(candidate):
                discovered.append(candidate)
        if len(discovered) >= max_reports or inspected > DEFAULT_DISCOVERY_LIMIT:
            break
    paths.extend(discovered[:max_reports])
    return list(dict.fromkeys(paths))


def _include_out_glob_artifacts(repo: Path, patterns: Iterable[str] | None, max_reports: int) -> list[Path]:
    if not patterns:
        return []
    included: list[Path] = []
    for pattern in patterns:
        normalized = pattern.strip()
        if not normalized or normalized.startswith("/") or ".." in Path(normalized).parts:
            raise GuardrailError(f"unsafe include-out-glob pattern: {pattern}")
        if not (normalized.startswith("out/reports/") or normalized.startswith("out/proposals/")):
            raise GuardrailError(f"include-out-glob must stay under out/reports or out/proposals: {pattern}")
        for candidate in sorted(repo.glob(normalized)):
            if len(included) >= max_reports:
                break
            if candidate.is_file() and _safe_discovery_candidate(candidate):
                _relative_to_repo(candidate, repo)
                included.append(candidate)
        if len(included) >= max_reports:
            break
    return list(dict.fromkeys(included))


def _queue_state(artifacts: list[EvidenceArtifact]) -> dict[str, int]:
    return {
        "ready_for_operator_review": sum(1 for artifact in artifacts if artifact.classification == "ready_for_operator_review"),
        "blocked": sum(1 for artifact in artifacts if artifact.classification == "blocked"),
        "stale": sum(1 for artifact in artifacts if artifact.classification == "stale"),
        "noise_or_trash": sum(1 for artifact in artifacts if artifact.classification == "noise_or_trash"),
        "accepted_or_closed": sum(
            1
            for artifact in artifacts
            if artifact.classification in {"accepted_or_closed", "accepted_or_closed_evidence"}
        ),
    }


def _worker_signals(artifacts: list[EvidenceArtifact]) -> list[WorkerSignal]:
    signals: list[WorkerSignal] = []
    for artifact in artifacts:
        if not artifact.exists or artifact.classification in {"missing_optional", "informational"}:
            continue
        worker = _worker_from_source(artifact.source)
        signals.append(
            WorkerSignal(
                worker=worker,
                path=artifact.path,
                signal=f"{artifact.classification}: {artifact.reason}",
                recommended_owner=_recommended_owner(artifact.reason + " " + artifact.path, artifact.classification),
                requires_human_approval=artifact.safe_to_dispatch or artifact.classification == "blocked",
                stable_key=artifact.stable_key,
            )
        )
    return signals


def _next_actions(blockers: list[str], queue_state: dict[str, int]) -> list[NextAction]:
    action = NextAction(
        id="unified-index.operator-review",
        title="Review deterministic unified control-plane evidence index",
        owner="Hermes",
        stage="operator_review",
        allowed_scope=["repo-only", "generated artifacts under out/"],
        forbidden_scope=["live vault mutation", "secrets", "auth/profile/service/cron changes"],
        blocked_by=blockers,
        acceptance=["JSON validates", "REPORT generated", "tests pass", "git diff checked"],
    )
    if queue_state["ready_for_operator_review"] or blockers:
        return [action]
    return []


def build_unified_control_plane_index(
    *,
    repo: str | Path | None = None,
    artifacts: Iterable[str | Path] | None = None,
    include_out_globs: Iterable[str] | None = None,
    max_reports: int = DEFAULT_MAX_REPORTS,
) -> UnifiedControlPlaneIndex:
    repo_root = _repo_root(repo)
    accepted_path = repo_root / "docs" / "acceptance" / "index.md"
    accepted_text = accepted_path.read_text(encoding="utf-8", errors="replace") if accepted_path.exists() else ""
    canonical_docs = [_canonical_doc(repo_root, rel_path, role) for rel_path, role in CANONICAL_DOCS]
    warnings = [
        f"missing canonical doc: {doc.path}"
        for doc in canonical_docs
        if not doc.exists
    ]
    raw_artifacts = list(artifacts) if artifacts is not None else _default_artifacts(repo_root, max_reports)
    raw_artifacts.extend(_include_out_glob_artifacts(repo_root, include_out_globs, max_reports))
    raw_artifacts = list(dict.fromkeys(raw_artifacts))
    evidence_artifacts = [_artifact(path, repo_root, accepted_text) for path in raw_artifacts]
    for artifact in evidence_artifacts:
        if artifact.classification == "missing_optional":
            warnings.append(f"missing optional artifact: {artifact.path}")
        for warning in artifact.warnings:
            if warning not in warnings and "missing optional artifact" not in warning:
                warnings.append(f"{artifact.path}: {warning}")
    queue_state = _queue_state(evidence_artifacts)
    blockers = [f"{artifact.path}: {artifact.reason}" for artifact in evidence_artifacts if artifact.classification == "blocked"]
    canonical_blockers = [
        f"missing required canonical doc: {doc.path}"
        for doc in canonical_docs
        if not doc.exists and doc.path.startswith("docs/spec-kit/")
    ]
    blockers.extend(canonical_blockers)
    queue_state["blocked"] += len(canonical_blockers)
    return UnifiedControlPlaneIndex(
        mode=MODE,
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo_root=str(repo_root),
        git=_git_state(repo_root),
        safety={**SAFETY},
        canonical_docs=canonical_docs,
        evidence_artifacts=evidence_artifacts,
        worker_signals=_worker_signals(evidence_artifacts),
        queue_state=queue_state,
        next_actions=_next_actions(blockers, queue_state),
        blockers=blockers,
        warnings=warnings,
    )


def unified_control_plane_index_to_markdown(index: UnifiedControlPlaneIndex) -> str:
    lines = [
        "# Unified Control-Plane Evidence Index",
        "",
        f"- mode: `{index.mode}`",
        f"- generated_at: `{index.generated_at}`",
        f"- repo_root: `{index.repo_root}`",
        f"- git_head: `{index.git['head']}`",
        f"- git_dirty: `{str(index.git['dirty']).lower()}`",
        "",
        "## Safety",
        "",
        f"- live_mutation_authorized: `{str(index.safety['live_mutation_authorized']).lower()}`",
        f"- approval_manifest_created: `{str(index.safety['approval_manifest_created']).lower()}`",
        f"- approval_manifest_authority: `{str(index.safety['approval_manifest_authority']).lower()}`",
        f"- apply_authority: `{index.safety['apply_authority']}`",
        f"- target_paths: `{index.safety['target_paths']}`",
        "",
        "## Queue State",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in index.queue_state.items())
    lines.extend(["", "## Canonical Docs", ""])
    for doc in index.canonical_docs:
        exists = "present" if doc.exists else "missing"
        lines.append(f"- `{exists}` `{doc.status_hint}` `{doc.role}` {doc.path}")
    lines.extend(["", "## Evidence Artifacts", ""])
    for artifact in index.evidence_artifacts:
        exists = "present" if artifact.exists else "missing"
        lines.append(
            f"- `{artifact.classification}` `{artifact.authority_state}` `{exists}` "
            f"`{artifact.stable_key}` {artifact.path} - {artifact.reason}"
        )
    lines.extend(["", "## Worker Signals", ""])
    if index.worker_signals:
        for signal in index.worker_signals:
            lines.append(f"- `{signal.worker}` -> `{signal.recommended_owner}` {signal.path}: {signal.signal}")
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions", ""])
    if index.next_actions:
        for action in index.next_actions:
            blocked_by = ", ".join(action.blocked_by) if action.blocked_by else "none"
            lines.append(f"- `{action.id}` `{action.owner}` `{action.stage}` blocked_by: {blocked_by}")
    else:
        lines.append("- none")
    lines.extend(["", "## Blockers", ""])
    if index.blockers:
        lines.extend(f"- {blocker}" for blocker in index.blockers)
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if index.warnings:
        lines.extend(f"- {warning}" for warning in index.warnings)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_unified_control_plane_index(index: UnifiedControlPlaneIndex, out_dir: str | Path) -> tuple[Path, Path]:
    out = _output_dir(out_dir, Path(index.repo_root))
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "control-plane-index.json"
    report_path = out / "REPORT.md"
    json_path.write_text(json.dumps(index.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(unified_control_plane_index_to_markdown(index), encoding="utf-8")
    return json_path, report_path
