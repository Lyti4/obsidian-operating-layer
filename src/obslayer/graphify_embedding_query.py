from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .graphify_embedding_handoff import _is_relative_to, _require_not_live, _safe_derived_root
from .graphify_embedding_runner import (
    ALLOWED_OLLAMA_MODELS,
    DEFAULT_HASHING_DIMENSIONS,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    _hashing_embedding,
    _ollama_embed,
    _ollama_unload,
)
from .guardrails import GuardrailError, write_json
from .indexing_wrapper import normalize_loopback_ollama_base_url


@dataclass(frozen=True)
class GraphifyEmbeddingQueryHit:
    path: str
    score: float
    chunk_index: int
    token_count: int
    char_count: int
    embedding_file: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphifyEmbeddingQueryResult:
    query: str
    hits: list[GraphifyEmbeddingQueryHit]

    def to_dict(self) -> dict[str, Any]:
        return {"query": self.query, "hits": [item.to_dict() for item in self.hits]}


@dataclass(frozen=True)
class GraphifyEmbeddingQueryReport:
    mode: str
    run_json: str
    derived_root: str
    provider: str
    model: str | None
    records: int
    embedded_files: int
    skipped: int
    embedding_sidecar_files: int
    chunks_indexed: int
    missing_embedding_files: list[str]
    skipped_records: list[dict[str, Any]]
    queries: list[GraphifyEmbeddingQueryResult]
    safety: dict[str, bool]
    ollama_unloaded_after_query: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["queries"] = [item.to_dict() for item in self.queries]
        return data


def _safe_run_json(path: str | Path) -> Path:
    run_json = _require_not_live(path)
    allowed = Path(__file__).resolve().parents[2] / "out" / "reports" / "graphify-embedding-runs"
    if run_json.name != "embedding-run.json" or not run_json.is_file():
        raise GuardrailError(f"Expected embedding-run.json: {run_json}")
    if not _is_relative_to(run_json, allowed.resolve()):
        raise GuardrailError(f"Embedding query run json must live under {allowed}: {run_json}")
    return run_json


def _safe_query_report_dir(path: str | Path) -> Path:
    report_dir = _require_not_live(path)
    allowed = Path(__file__).resolve().parents[2] / "out" / "reports" / "graphify-embedding-query-smoke"
    if not _is_relative_to(report_dir, allowed.resolve()):
        raise GuardrailError(f"Embedding query report dir must live under {allowed}: {report_dir}")
    return report_dir


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    an = math.sqrt(sum(value * value for value in a)) or 1.0
    bn = math.sqrt(sum(value * value for value in b)) or 1.0
    return dot / (an * bn)


def _query_vector(
    query: str,
    *,
    provider: str,
    dimensions: int,
    ollama_base_url: str,
    ollama_model: str,
    ollama_timeout_seconds: int,
) -> list[float]:
    if not query.strip():
        raise GuardrailError("query must not be empty")
    if provider == "local-hashing-v1":
        vector, _tokens = _hashing_embedding(query, dimensions=dimensions)
        return vector
    if provider == "ollama":
        vector, _tokens = _ollama_embed(
            query,
            base_url=ollama_base_url,
            model=ollama_model,
            timeout_seconds=ollama_timeout_seconds,
            keep_alive="30s",
        )
        return vector
    raise GuardrailError(f"Unsupported query provider: {provider}")


def _load_embedding_chunks(run_payload: dict[str, Any], derived_root: Path) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    records = run_payload.get("records")
    if not isinstance(records, list):
        raise GuardrailError("embedding-run.json is missing records list")
    chunks: list[dict[str, Any]] = []
    missing: list[str] = []
    skipped: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("status") != "embedded":
            skipped.append(record)
            continue
        raw_embedding_file = record.get("embedding_file")
        if not isinstance(raw_embedding_file, str):
            missing.append(str(record.get("path") or "<unknown>"))
            continue
        embedding_file = _require_not_live(raw_embedding_file)
        if not _is_relative_to(embedding_file, derived_root):
            raise GuardrailError(f"Embedding file escapes derived root: {embedding_file}")
        if not embedding_file.is_file():
            missing.append(str(record.get("path") or embedding_file))
            continue
        payload = json.loads(embedding_file.read_text(encoding="utf-8"))
        path = str(payload.get("path") or record.get("path") or "")
        for chunk in payload.get("chunks") or []:
            if not isinstance(chunk, dict) or not isinstance(chunk.get("vector"), list):
                continue
            chunks.append(
                {
                    "path": path,
                    "chunk_index": int(chunk.get("chunk_index") or 0),
                    "token_count": int(chunk.get("token_count") or 0),
                    "char_count": int(chunk.get("char_count") or 0),
                    "vector": [float(value) for value in chunk["vector"]],
                    "embedding_file": str(embedding_file),
                }
            )
    return chunks, missing, skipped


def run_graphify_embedding_query_smoke(
    *,
    run_json: str | Path,
    queries: list[str],
    top_k: int = 8,
    provider: str | None = None,
    dimensions: int | None = None,
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL,
    ollama_model: str = DEFAULT_OLLAMA_MODEL,
    ollama_timeout_seconds: int = 360,
    unload_ollama_after_query: bool = True,
) -> GraphifyEmbeddingQueryReport:
    if not queries:
        raise GuardrailError("at least one query is required")
    if top_k < 1 or top_k > 50:
        raise GuardrailError("top_k must be between 1 and 50")
    run_path = _safe_run_json(run_json)
    run_payload = json.loads(run_path.read_text(encoding="utf-8"))
    derived = _safe_derived_root(run_payload.get("derived_root"))
    run_provider = str(run_payload.get("provider") or "")
    query_provider = provider or run_provider
    if query_provider not in {"ollama", "local-hashing-v1"}:
        raise GuardrailError(f"Unsupported query provider: {query_provider}")
    if query_provider != run_provider:
        raise GuardrailError("query provider must match the embedding-run provider")
    normalized_ollama_url = normalize_loopback_ollama_base_url(ollama_base_url) if query_provider == "ollama" else ollama_base_url
    if query_provider == "ollama" and ollama_model not in ALLOWED_OLLAMA_MODELS:
        raise GuardrailError(f"Ollama query model must be bge-m3 for this runner: {ollama_model!r}")
    query_dimensions = dimensions or int(run_payload.get("dimensions") or DEFAULT_HASHING_DIMENSIONS)
    chunks, missing, skipped = _load_embedding_chunks(run_payload, derived)
    if not chunks:
        raise GuardrailError("no embedding chunks available for query smoke")

    results: list[GraphifyEmbeddingQueryResult] = []
    ollama_unloaded: bool | None = None
    try:
        for query in queries:
            qv = _query_vector(
                query,
                provider=query_provider,
                dimensions=query_dimensions,
                ollama_base_url=normalized_ollama_url,
                ollama_model=ollama_model,
                ollama_timeout_seconds=ollama_timeout_seconds,
            )
            scored = sorted(((_cosine(qv, item["vector"]), item) for item in chunks), key=lambda pair: pair[0], reverse=True)
            seen: set[str] = set()
            hits: list[GraphifyEmbeddingQueryHit] = []
            for score, item in scored:
                path = str(item["path"])
                if path in seen:
                    continue
                seen.add(path)
                hits.append(
                    GraphifyEmbeddingQueryHit(
                        path=path,
                        score=round(float(score), 6),
                        chunk_index=int(item["chunk_index"]),
                        token_count=int(item["token_count"]),
                        char_count=int(item["char_count"]),
                        embedding_file=str(item["embedding_file"]),
                    )
                )
                if len(hits) >= top_k:
                    break
            results.append(GraphifyEmbeddingQueryResult(query=query, hits=hits))
    finally:
        if query_provider == "ollama" and unload_ollama_after_query:
            ollama_unloaded = _ollama_unload(
                base_url=normalized_ollama_url,
                model=ollama_model,
                timeout_seconds=min(max(ollama_timeout_seconds, 5), 60),
            )

    embedded_files = sum(1 for record in run_payload.get("records", []) if isinstance(record, dict) and record.get("status") == "embedded")
    sidecar_files = sum(1 for _ in (derived / "embeddings").glob("*.json"))
    return GraphifyEmbeddingQueryReport(
        mode="graphify-embedding-query-smoke",
        run_json=str(run_path),
        derived_root=str(derived),
        provider=query_provider,
        model=ollama_model if query_provider == "ollama" else None,
        records=len(run_payload.get("records", [])),
        embedded_files=embedded_files,
        skipped=len(skipped),
        embedding_sidecar_files=sidecar_files,
        chunks_indexed=len(chunks),
        missing_embedding_files=missing,
        skipped_records=skipped,
        queries=results,
        safety={
            "embedding_run_report_only": True,
            "derived_cache_only": True,
            "live_vault_refused": True,
            "live_mutation": False,
            "ollama_loopback_only": query_provider != "ollama" or normalized_ollama_url in {"http://localhost:11434", "http://127.0.0.1:11434"},
            "provider_matches_run": query_provider == run_provider,
        },
        ollama_unloaded_after_query=ollama_unloaded,
    )


def graphify_embedding_query_to_markdown(report: GraphifyEmbeddingQueryReport) -> str:
    lines = [
        "# Graphify embedding query smoke",
        "",
        f"Provider: `{report.provider}`",
        f"Records: {report.records}",
        f"Embedded files: {report.embedded_files}",
        f"Skipped: {report.skipped}",
        f"Embedding sidecar files: {report.embedding_sidecar_files}",
        f"Chunks indexed: {report.chunks_indexed}",
        f"Missing embedding files: {len(report.missing_embedding_files)}",
        "",
    ]
    if report.skipped_records:
        lines.extend(["## Skipped records", ""])
        for item in report.skipped_records:
            lines.append(f"- `{item.get('path')}` — {item.get('skipped_reason')}")
        lines.append("")
    lines.extend(["## Query results", ""])
    for result in report.queries:
        lines.extend([f"### {result.query}", "", "| rank | score | path | chunk |", "|---:|---:|---|---:|"])
        for index, hit in enumerate(result.hits, 1):
            lines.append(f"| {index} | {hit.score:.6f} | `{hit.path}` | {hit.chunk_index} |")
        lines.append("")
    lines.extend(["## Safety", ""])
    for key, value in report.safety.items():
        lines.append(f"- {key}: {value}")
    if report.ollama_unloaded_after_query is not None:
        lines.extend(["", "## Ollama lifecycle", "", f"- unloaded_after_query: `{report.ollama_unloaded_after_query}`"])
    lines.append("")
    return "\n".join(lines)


def write_graphify_embedding_query_smoke_report(
    *,
    run_json: str | Path,
    out_dir: str | Path,
    queries: list[str],
    top_k: int = 8,
    provider: str | None = None,
    dimensions: int | None = None,
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL,
    ollama_model: str = DEFAULT_OLLAMA_MODEL,
    ollama_timeout_seconds: int = 360,
    unload_ollama_after_query: bool = True,
) -> dict[str, str]:
    report_dir = _safe_query_report_dir(out_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report = run_graphify_embedding_query_smoke(
        run_json=run_json,
        queries=queries,
        top_k=top_k,
        provider=provider,
        dimensions=dimensions,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_timeout_seconds=ollama_timeout_seconds,
        unload_ollama_after_query=unload_ollama_after_query,
    )
    json_path = report_dir / "query-smoke.json"
    md_path = report_dir / "REPORT.md"
    write_json(json_path, {"created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **report.to_dict()})
    md_path.write_text(graphify_embedding_query_to_markdown(report), encoding="utf-8")
    return {
        "status": "ok",
        "report": str(md_path),
        "json": str(json_path),
        "chunks_indexed": str(report.chunks_indexed),
        "queries": str(len(report.queries)),
        "missing_embedding_files": str(len(report.missing_embedding_files)),
    }
