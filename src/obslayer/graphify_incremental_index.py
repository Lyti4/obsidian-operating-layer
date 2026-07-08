from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .graphify_embedding_handoff import (
    DEFAULT_GRAPHIFY_EMBEDDING_DERIVED_ROOT,
    write_graphify_embedding_handoff,
)
from .graphify_embedding_query import write_graphify_embedding_query_smoke_report
from .graphify_embedding_runner import write_graphify_embedding_run_report
from .guardrails import GuardrailError, write_json


DEFAULT_QUERIES = [
    "дубликаты Obsidian",
    "protected paths",
    "Runtime Error Full Audit",
    "Hermes CLI settings",
    "ParserRIba verification gate",
]


@dataclass(frozen=True)
class IncrementalCandidateState:
    path: str
    status: str
    reason: str
    embedding_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphifyIncrementalIndexReport:
    mode: str
    status: str
    handoff_manifest: str
    delta_manifest: str
    candidates_total: int
    delta_candidates: int
    unchanged_candidates: int
    max_delta_candidates: int
    dry_run: bool
    embedding_run_json: str | None
    query_smoke_json: str | None
    safety: dict[str, bool]
    candidate_states: list[IncrementalCandidateState]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidate_states"] = [item.to_dict() for item in self.candidate_states]
        return data


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _require_out_report_dir(path: str | Path, *, root_name: str) -> Path:
    repo = _repo_root()
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve()
    allowed = (repo / "out" / "reports" / root_name).resolve()
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise GuardrailError(f"output dir must live under {allowed}: {resolved}") from exc
    return resolved


def _embedding_output_path(derived_root: Path, rel_path: str) -> Path:
    import hashlib

    digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:16]
    return derived_root / "embeddings" / f"{digest}.json"


def _existing_state(derived_root: Path, candidate: dict[str, Any], provider: str) -> IncrementalCandidateState:
    rel_path = str(candidate.get("path") or "")
    expected_hash = str(candidate.get("hash") or "")
    embedding_file = _embedding_output_path(derived_root, rel_path)
    if not embedding_file.is_file():
        return IncrementalCandidateState(rel_path, "delta", "missing_embedding", str(embedding_file))
    try:
        payload = json.loads(embedding_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return IncrementalCandidateState(rel_path, "delta", "unreadable_embedding", str(embedding_file))
    if payload.get("path") != rel_path:
        return IncrementalCandidateState(rel_path, "delta", "path_mismatch", str(embedding_file))
    if payload.get("hash") != expected_hash:
        return IncrementalCandidateState(rel_path, "delta", "hash_changed", str(embedding_file))
    if payload.get("provider") != provider:
        return IncrementalCandidateState(rel_path, "delta", "provider_mismatch", str(embedding_file))
    chunks = payload.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        return IncrementalCandidateState(rel_path, "delta", "missing_chunks", str(embedding_file))
    return IncrementalCandidateState(rel_path, "unchanged", "embedding_current", str(embedding_file))


def _write_delta_manifest(handoff_manifest: Path, out_dir: Path, delta_candidates: list[dict[str, Any]]) -> Path:
    payload = json.loads(handoff_manifest.read_text(encoding="utf-8"))
    payload["candidates"] = delta_candidates
    payload["incremental_delta"] = {
        "source_manifest": str(handoff_manifest),
        "selected_count": len(delta_candidates),
        "selection_reason": "missing/stale/provider-mismatched derived embedding sidecars",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    delta_manifest = out_dir / "embedding-manifest.json"
    write_json(delta_manifest, payload)
    return delta_manifest


def incremental_report_to_markdown(report: GraphifyIncrementalIndexReport) -> str:
    lines = [
        "# Graphify incremental indexing wrapper",
        "",
        f"Status: `{report.status}`",
        f"Dry run: `{report.dry_run}`",
        f"Candidates total: {report.candidates_total}",
        f"Delta candidates: {report.delta_candidates}",
        f"Unchanged candidates: {report.unchanged_candidates}",
        "",
        "## Artifacts",
        "",
        f"- handoff manifest: `{report.handoff_manifest}`",
        f"- delta manifest: `{report.delta_manifest}`",
    ]
    if report.embedding_run_json:
        lines.append(f"- embedding run: `{report.embedding_run_json}`")
    if report.query_smoke_json:
        lines.append(f"- query smoke: `{report.query_smoke_json}`")
    lines += ["", "## Safety", ""]
    for key, value in report.safety.items():
        lines.append(f"- {key}: `{value}`")
    lines += ["", "## Candidate states", "", "| path | status | reason |", "|---|---:|---|"]
    for item in report.candidate_states:
        lines.append(f"| `{item.path}` | `{item.status}` | {item.reason} |")
    return "\n".join(lines) + "\n"


def run_graphify_incremental_index(
    *,
    graph_json: str | Path,
    sandbox_vault: str | Path,
    out_dir: str | Path,
    derived_root: str | Path = DEFAULT_GRAPHIFY_EMBEDDING_DERIVED_ROOT,
    max_candidates: int = 50,
    max_delta_candidates: int = 25,
    provider: str = "ollama",
    dry_run: bool = True,
    run_query_smoke: bool = False,
    queries: list[str] | None = None,
    allow_smoke_provider: bool = False,
) -> GraphifyIncrementalIndexReport:
    if max_delta_candidates < 1 or max_delta_candidates > 75:
        raise GuardrailError("max_delta_candidates must be between 1 and 75")
    if provider == "local-hashing-v1" and not allow_smoke_provider:
        raise GuardrailError("local-hashing-v1 requires allow_smoke_provider=True")

    out = _require_out_report_dir(out_dir, root_name="graphify-incremental-index")
    handoff_dir = _repo_root() / "out" / "reports" / "graphify-embedding-handoff" / f"incremental-{out.name}"
    handoff = write_graphify_embedding_handoff(
        graph_json=graph_json,
        sandbox_vault=sandbox_vault,
        out_dir=handoff_dir,
        derived_root=derived_root,
        max_candidates=max_candidates,
    )
    handoff_manifest = Path(handoff["manifest"]).resolve()
    payload = json.loads(handoff_manifest.read_text(encoding="utf-8"))
    derived = Path(payload["derived_root"]).resolve()
    candidates = payload.get("candidates") or []
    if not isinstance(candidates, list):
        raise GuardrailError("handoff manifest candidates must be a list")

    states = [_existing_state(derived, item, provider) for item in candidates if isinstance(item, dict)]
    delta = [item for item, state in zip(candidates, states, strict=False) if state.status == "delta"][:max_delta_candidates]
    delta_dir = _repo_root() / "out" / "reports" / "graphify-embedding-handoff" / f"incremental-delta-{out.name}"
    delta_manifest = _write_delta_manifest(handoff_manifest, delta_dir, delta)

    embedding_run_json: str | None = None
    query_smoke_json: str | None = None
    if not dry_run and delta:
        run_result = write_graphify_embedding_run_report(
            manifest_path=delta_manifest,
            out_dir=_repo_root() / "out" / "reports" / "graphify-embedding-runs" / f"incremental-{out.name}",
            derived_root=derived,
            max_files=len(delta),
            provider=provider,
            allow_smoke_provider=allow_smoke_provider,
        )
        embedding_run_json = run_result["json"]
        if run_query_smoke:
            query_result = write_graphify_embedding_query_smoke_report(
                run_json=embedding_run_json,
                out_dir=_repo_root() / "out" / "reports" / "graphify-embedding-query-smoke" / f"incremental-{out.name}",
                queries=queries or DEFAULT_QUERIES,
                top_k=5,
                provider=provider,
            )
            query_smoke_json = query_result["json"]

    status = "ready"
    if not dry_run and delta and not embedding_run_json:
        status = "blocked"
    report = GraphifyIncrementalIndexReport(
        mode="obslayer.graphify-incremental-index.v1",
        status=status,
        handoff_manifest=str(handoff_manifest),
        delta_manifest=str(delta_manifest),
        candidates_total=len(candidates),
        delta_candidates=len(delta),
        unchanged_candidates=sum(1 for item in states if item.status == "unchanged"),
        max_delta_candidates=max_delta_candidates,
        dry_run=dry_run,
        embedding_run_json=embedding_run_json,
        query_smoke_json=query_smoke_json,
        safety={
            "live_vault_mutation": False,
            "approval_manifest_created": False,
            "manifest_only": True,
            "derived_cache_only": True,
            "uses_existing_graphify_handoff": True,
        },
        candidate_states=states,
    )
    write_json(out / "graphify-incremental-index.json", report.to_dict())
    (out / "REPORT.md").write_text(incremental_report_to_markdown(report), encoding="utf-8")
    return report
