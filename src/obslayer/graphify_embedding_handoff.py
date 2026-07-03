from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError, is_protected_relative, write_json
from .indexing_wrapper import DEFAULT_DERIVED_ROOT, DEFAULT_LIVE_VAULT_ROOT

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SANDBOX_ROOT = REPO_ROOT / "out" / "sandbox-vaults"
DEFAULT_GRAPHIFY_EMBEDDING_REPORT_ROOT = REPO_ROOT / "out" / "reports" / "graphify-embedding-handoff"
DEFAULT_GRAPHIFY_EMBEDDING_DERIVED_ROOT = DEFAULT_DERIVED_ROOT / "graphify-derived"
DEFAULT_EMBEDDING_EXTENSIONS = (".md", ".markdown", ".txt")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_existing_or_parent(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.exists():
        return candidate.resolve()
    return candidate.parent.resolve() / candidate.name


def _require_not_live(path: str | Path, *, live_vault_root: str | Path = DEFAULT_LIVE_VAULT_ROOT) -> Path:
    resolved = _resolve_existing_or_parent(path)
    live = Path(live_vault_root).expanduser().resolve()
    if _is_relative_to(resolved, live):
        raise GuardrailError(f"Graphify embedding handoff refuses live vault paths: {resolved}")
    return resolved


def _require_under(path: str | Path, root: str | Path, label: str) -> Path:
    resolved = _resolve_existing_or_parent(path)
    base = Path(root).expanduser().resolve()
    if not _is_relative_to(resolved, base):
        raise GuardrailError(f"{label} must live under {base}: {resolved}")
    return resolved


def _safe_sandbox_vault(path: str | Path, *, sandbox_root: str | Path = DEFAULT_SANDBOX_ROOT) -> Path:
    sandbox = _require_not_live(path)
    if not sandbox.is_dir():
        raise GuardrailError(f"Graphify embedding handoff requires an existing sandbox vault: {sandbox}")
    _require_under(sandbox, sandbox_root, "Graphify embedding sandbox")
    if sandbox == Path(sandbox_root).expanduser().resolve():
        raise GuardrailError("Graphify embedding sandbox must be a named sandbox vault")
    return sandbox


def _safe_report_dir(path: str | Path) -> Path:
    report_dir = _require_not_live(path)
    _require_under(report_dir, DEFAULT_GRAPHIFY_EMBEDDING_REPORT_ROOT, "Graphify embedding report dir")
    return report_dir


def _safe_derived_root(path: str | Path) -> Path:
    derived = _require_not_live(path)
    _require_under(derived, DEFAULT_GRAPHIFY_EMBEDDING_DERIVED_ROOT, "Graphify embedding derived root")
    return derived


def _safe_graph_path(path: str | Path) -> Path:
    graph = _require_not_live(path)
    if graph.name != "graph.json" or not graph.is_file():
        raise GuardrailError(f"Graphify embedding handoff requires an existing graph.json: {graph}")
    allowed_roots = [REPO_ROOT / "out", Path("/home/hermesadmin/tools/graphify/graphify-out")]
    if not any(_is_relative_to(graph, root.expanduser().resolve()) for root in allowed_roots):
        raise GuardrailError("Graphify graph.json must be a generated artifact under an approved out/ directory")
    return graph


def _relative_source_file(raw: Any, sandbox: Path) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip().replace("\\", "/")
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        try:
            rel = candidate.resolve().relative_to(sandbox)
        except ValueError:
            return None
    else:
        rel = Path(text)
    if rel.is_absolute() or ".." in rel.parts:
        return None
    rel_text = rel.as_posix()
    if is_protected_relative(rel_text):
        return None
    if rel.suffix.lower() not in DEFAULT_EMBEDDING_EXTENSIONS:
        return None
    target = sandbox / rel
    if not target.is_file():
        return None
    return rel_text


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class GraphifyEmbeddingCandidate:
    path: str
    hash: str
    community_ids: list[int | str]
    graph_node_count: int
    graph_edge_count: int
    score: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphifyEmbeddingHandoff:
    mode: str
    graph_json: str
    sandbox_vault: str
    derived_root: str
    candidates: list[GraphifyEmbeddingCandidate]
    graph_summary: dict[str, Any]
    embedding_policy: dict[str, Any]
    safety: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidates"] = [item.to_dict() for item in self.candidates]
        return data


def build_graphify_embedding_handoff(
    *,
    graph_json: str | Path,
    sandbox_vault: str | Path,
    derived_root: str | Path = DEFAULT_GRAPHIFY_EMBEDDING_DERIVED_ROOT,
    max_candidates: int = 50,
) -> GraphifyEmbeddingHandoff:
    """Build a graph-derived embedding manifest without running embeddings.

    The output is the only accepted input shape for later bounded embedding jobs:
    Graphify decides the source files first, then the embedding sidecar may consume
    this manifest. This function intentionally does not call an embedding model.
    """
    if max_candidates < 1 or max_candidates > 500:
        raise GuardrailError("Graphify embedding max_candidates must be between 1 and 500")
    graph_path = _safe_graph_path(graph_json)
    sandbox = _safe_sandbox_vault(sandbox_vault)
    derived = _safe_derived_root(derived_root)

    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = payload.get("nodes")
    links = payload.get("links")
    if not isinstance(nodes, list) or not isinstance(links, list):
        raise GuardrailError("Graphify graph.json must contain nodes and links lists")

    node_to_file: dict[str, str] = {}
    file_node_counts: Counter[str] = Counter()
    file_communities: dict[str, set[int | str]] = defaultdict(set)
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        rel = _relative_source_file(node.get("source_file"), sandbox)
        if not isinstance(node_id, str) or rel is None:
            continue
        node_to_file[node_id] = rel
        file_node_counts[rel] += 1
        community = node.get("community")
        if isinstance(community, (str, int)):
            file_communities[rel].add(community)

    file_edge_counts: Counter[str] = Counter()
    for link in links:
        if not isinstance(link, dict):
            continue
        for endpoint in (link.get("source"), link.get("target")):
            if isinstance(endpoint, str) and endpoint in node_to_file:
                file_edge_counts[node_to_file[endpoint]] += 1

    candidates: list[GraphifyEmbeddingCandidate] = []
    for rel, node_count in file_node_counts.items():
        score = int(node_count + file_edge_counts[rel])
        candidates.append(
            GraphifyEmbeddingCandidate(
                path=rel,
                hash=_file_hash(sandbox / rel),
                community_ids=sorted(file_communities[rel], key=str),
                graph_node_count=int(node_count),
                graph_edge_count=int(file_edge_counts[rel]),
                score=score,
                reason="Selected from Graphify graph.json; embeddings may only consume this graph-derived manifest.",
            )
        )
    candidates.sort(key=lambda item: (-item.score, item.path))
    candidates = candidates[:max_candidates]

    return GraphifyEmbeddingHandoff(
        mode="graphify-derived-embedding-manifest",
        graph_json=str(graph_path),
        sandbox_vault=str(sandbox),
        derived_root=str(derived),
        candidates=candidates,
        graph_summary={
            "nodes_total": len(nodes),
            "links_total": len(links),
            "source_files_in_graph": len(file_node_counts),
            "selected_candidates": len(candidates),
            "built_at_commit": payload.get("built_at_commit"),
        },
        embedding_policy={
            "auto_execute": False,
            "source_order": "graphify_score_desc",
            "provider": "local_only_or_explicitly_approved",
            "concurrency": 1,
            "checkpoint_resume_required": True,
            "derived_cache_only": True,
        },
        safety={
            "live_vault_refused": True,
            "sandbox_required": True,
            "protected_paths_excluded": True,
            "embeddings_started": False,
            "live_mutation": False,
        },
    )


def handoff_to_markdown(handoff: GraphifyEmbeddingHandoff) -> str:
    lines = [
        "# Graphify-derived embedding handoff",
        "",
        "Status: manifest only; embeddings not started.",
        "",
        "## Graph summary",
        "",
    ]
    for key, value in handoff.graph_summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Embedding policy", ""])
    for key, value in handoff.embedding_policy.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Candidates", ""])
    if not handoff.candidates:
        lines.append("No eligible markdown/text candidates were found in the sandbox graph.")
    else:
        lines.append("| rank | path | score | graph nodes | graph edges | communities | hash |")
        lines.append("|---:|---|---:|---:|---:|---|---|")
        for idx, item in enumerate(handoff.candidates, start=1):
            communities = ", ".join(str(value) for value in item.community_ids)
            lines.append(
                f"| {idx} | `{item.path}` | {item.score} | {item.graph_node_count} | "
                f"{item.graph_edge_count} | {communities} | `{item.hash}` |"
            )
    lines.extend([
        "",
        "## Safety",
        "",
    ])
    for key, value in handoff.safety.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def write_graphify_embedding_handoff(
    *,
    graph_json: str | Path,
    sandbox_vault: str | Path,
    out_dir: str | Path,
    derived_root: str | Path = DEFAULT_GRAPHIFY_EMBEDDING_DERIVED_ROOT,
    max_candidates: int = 50,
) -> dict[str, str]:
    handoff = build_graphify_embedding_handoff(
        graph_json=graph_json,
        sandbox_vault=sandbox_vault,
        derived_root=derived_root,
        max_candidates=max_candidates,
    )
    report_dir = _safe_report_dir(out_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = report_dir / "embedding-manifest.json"
    report_path = report_dir / "REPORT.md"
    write_json(manifest_path, handoff.to_dict())
    report_path.write_text(handoff_to_markdown(handoff), encoding="utf-8")
    return {
        "status": "ok",
        "manifest": str(manifest_path),
        "report": str(report_path),
        "candidates": str(len(handoff.candidates)),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
