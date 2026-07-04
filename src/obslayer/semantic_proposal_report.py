from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .graphify_embedding_handoff import _is_relative_to, _require_not_live
from .guardrails import GuardrailError, write_json


@dataclass(frozen=True)
class SemanticProposalCandidate:
    path: str
    queries: list[str]
    best_score: float
    hit_count: int
    chunks: list[int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticProposalReport:
    mode: str
    query_smoke_json: str
    status: str
    proposal_id: str
    source_id: str
    risk_class: str
    dry_run_default: bool
    approval_required: bool
    live_mutation_authorized: bool
    targets: list[dict[str, Any]]
    evidence: list[str]
    queries: list[str]
    candidates: list[SemanticProposalCandidate]
    summary: dict[str, Any]
    safety: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidates"] = [candidate.to_dict() for candidate in self.candidates]
        return data


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _safe_query_smoke_json(path: str | Path) -> Path:
    query_json = _require_not_live(path)
    allowed = _repo_root() / "out" / "reports" / "graphify-embedding-query-smoke"
    if query_json.name != "query-smoke.json" or not query_json.is_file():
        raise GuardrailError(f"Expected query-smoke.json: {query_json}")
    if not _is_relative_to(query_json, allowed.resolve()):
        raise GuardrailError(f"query-smoke.json must live under {allowed}: {query_json}")
    return query_json


def _safe_semantic_proposal_out_dir(path: str | Path) -> Path:
    out_dir = _require_not_live(path)
    allowed = _repo_root() / "out" / "proposals" / "semantic-query-reports"
    if not _is_relative_to(out_dir, allowed.resolve()):
        raise GuardrailError(f"Semantic proposal reports must live under {allowed}: {out_dir}")
    return out_dir


def _extract_hits(payload: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    queries: list[str] = []
    by_path: dict[str, dict[str, Any]] = {}
    for query_item in payload.get("queries") or []:
        if not isinstance(query_item, dict):
            continue
        query = str(query_item.get("query") or "").strip()
        if not query:
            continue
        queries.append(query)
        raw_hits = query_item.get("top") if isinstance(query_item.get("top"), list) else query_item.get("hits")
        for hit in raw_hits or []:
            if not isinstance(hit, dict):
                continue
            path = str(hit.get("path") or "").strip()
            if not path:
                continue
            score = float(hit.get("score") or 0.0)
            chunk_index = int(hit.get("chunk_index") or 0)
            row = by_path.setdefault(path, {"path": path, "queries": set(), "best_score": score, "hit_count": 0, "chunks": set()})
            row["queries"].add(query)
            row["best_score"] = max(float(row["best_score"]), score)
            row["hit_count"] = int(row["hit_count"]) + 1
            row["chunks"].add(chunk_index)
    return queries, by_path


def build_semantic_proposal_report(
    *,
    query_smoke_json: str | Path,
    proposal_id: str | None = None,
    max_candidates: int = 25,
) -> SemanticProposalReport:
    if max_candidates < 1 or max_candidates > 100:
        raise GuardrailError("max_candidates must be between 1 and 100")
    query_path = _safe_query_smoke_json(query_smoke_json)
    payload = json.loads(query_path.read_text(encoding="utf-8"))
    if payload.get("mode") != "graphify-embedding-query-smoke":
        raise GuardrailError("query-smoke.json mode must be graphify-embedding-query-smoke")
    safety = payload.get("safety") if isinstance(payload.get("safety"), dict) else {}
    # Older accepted query-smoke reports predate the explicit safety block. Refuse only
    # an explicit live-mutation signal; this converter still emits an empty-target,
    # proposal-only report and never authorizes apply.
    if safety.get("live_mutation") is True:
        raise GuardrailError("query smoke reports live_mutation=true")
    if payload.get("missing_embedding_files"):
        raise GuardrailError("query smoke has missing embedding files; refuse proposal report")

    queries, by_path = _extract_hits(payload)
    candidates = [
        SemanticProposalCandidate(
            path=str(row["path"]),
            queries=sorted(str(item) for item in row["queries"]),
            best_score=round(float(row["best_score"]), 6),
            hit_count=int(row["hit_count"]),
            chunks=sorted(int(item) for item in row["chunks"]),
        )
        for row in by_path.values()
    ]
    candidates.sort(key=lambda item: (item.hit_count, item.best_score, item.path), reverse=True)
    candidates = candidates[:max_candidates]
    pid = proposal_id or f"semantic-query-report-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    return SemanticProposalReport(
        mode="semantic-query-proposal-only-report",
        query_smoke_json=str(query_path),
        status="needs-review",
        proposal_id=pid,
        source_id="graphify-final468-semantic-query",
        risk_class="read_only_only",
        dry_run_default=True,
        approval_required=True,
        live_mutation_authorized=False,
        targets=[],
        evidence=[str(query_path)],
        queries=queries,
        candidates=candidates,
        summary={
            "records": payload.get("records"),
            "embedded_files": payload.get("embedded_files") or payload.get("processed"),
            "skipped": payload.get("skipped"),
            "chunks_indexed": payload.get("chunks_indexed"),
            "candidate_paths": len(candidates),
        },
        safety={
            "proposal_only": True,
            "read_only_evidence": True,
            "targets_empty": True,
            "live_mutation_authorized": False,
            "requires_human_review": True,
            "derived_cache_only": safety.get("derived_cache_only") is True or "derived_root" in payload,
            "source_query_live_mutation_not_true": safety.get("live_mutation") is not True,
        },
    )


def semantic_proposal_report_to_markdown(report: SemanticProposalReport) -> str:
    lines = [
        "# Semantic query proposal-only report",
        "",
        f"Proposal id: `{report.proposal_id}`",
        f"Status: `{report.status}`",
        f"Risk: `{report.risk_class}`",
        "",
        "## Boundary",
        "",
        "- This is a proposal-only / read-only semantic discovery report.",
        "- It contains candidate notes for human review, not edits.",
        "- `targets` is intentionally empty; live vault mutation is not authorized.",
        "",
        "## Evidence",
        "",
    ]
    for item in report.evidence:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Query intents", ""])
    for query in report.queries:
        lines.append(f"- {query}")
    lines.extend([
        "",
        "## Candidate notes",
        "",
        "| rank | best score | hits | path | query matches | chunks |",
        "|---:|---:|---:|---|---|---|",
    ])
    for idx, candidate in enumerate(report.candidates, 1):
        queries = "; ".join(candidate.queries)
        chunks = ", ".join(str(item) for item in candidate.chunks)
        lines.append(f"| {idx} | {candidate.best_score:.6f} | {candidate.hit_count} | `{candidate.path}` | {queries} | {chunks} |")
    lines.extend(["", "## Summary", ""])
    for key, value in report.summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Safety", ""])
    for key, value in report.safety.items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_semantic_proposal_report(
    *,
    query_smoke_json: str | Path,
    out_dir: str | Path,
    proposal_id: str | None = None,
    max_candidates: int = 25,
) -> dict[str, str]:
    report_dir = _safe_semantic_proposal_out_dir(out_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report = build_semantic_proposal_report(
        query_smoke_json=query_smoke_json,
        proposal_id=proposal_id,
        max_candidates=max_candidates,
    )
    json_path = report_dir / "proposal.json"
    md_path = report_dir / "REPORT.md"
    write_json(json_path, {"created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **report.to_dict()})
    md_path.write_text(semantic_proposal_report_to_markdown(report), encoding="utf-8")
    return {
        "status": "ok",
        "proposal": str(json_path),
        "report": str(md_path),
        "candidate_paths": str(len(report.candidates)),
        "targets": str(len(report.targets)),
    }
