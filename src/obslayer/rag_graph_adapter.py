from __future__ import annotations

import json
import re
import resource
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError, is_protected_relative, load_json, utc_stamp, write_json

ALLOWED_RAG_GRAPH_CAPABILITIES = {"read", "search", "graph", "analyze", "metadata-read", "propose"}
REQUIRED_FORBIDDEN_CAPABILITIES = {
    "write-direct",
    "delete-direct",
    "move-direct",
    "merge-direct",
    "patch-direct",
    "execute-live-mutation",
    "secret-read",
}
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_/-]+)")
PROPOSAL_ONLY_FINDING_TYPES = {"candidate-backlink", "duplicate-candidate", "merge-candidate", "moc-candidate", "metadata-suggestion"}


@dataclass(frozen=True)
class RagGraphAdapterEvaluation:
    adapter: str
    source_id: str
    sandbox_vault: str
    allowed_capabilities: list[str]
    forbidden_capabilities: list[str]
    direct_write_disabled: bool
    sandbox_required: bool
    write_policy: str
    fixed_queries: list[str]
    source_exclude_prefixes: list[str]
    findings: list[dict[str, Any]]
    artifacts: dict[str, str]
    verification: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_rag_graph_adapter_record(path: str | Path) -> dict[str, Any]:
    record = load_json(path)
    if record.get("kind") != "rag-engine":
        raise GuardrailError(f"Adapter record is not a RAG/graph engine: {record.get('kind')}")
    if record.get("direct_write_enabled") is not False:
        raise GuardrailError("RAG/graph adapter must set direct_write_enabled=false")
    if record.get("sandbox_required") is not True:
        raise GuardrailError("RAG/graph adapter must require sandbox evaluation")

    capabilities = set(record.get("capabilities", []))
    unknown_allowed = capabilities - ALLOWED_RAG_GRAPH_CAPABILITIES
    if unknown_allowed:
        raise GuardrailError(f"RAG/graph adapter has unsupported allowed capabilities: {sorted(unknown_allowed)}")
    dangerous_as_allowed = capabilities & REQUIRED_FORBIDDEN_CAPABILITIES
    if dangerous_as_allowed:
        raise GuardrailError(f"RAG/graph adapter exposes dangerous capabilities as allowed: {sorted(dangerous_as_allowed)}")

    forbidden = set(record.get("forbidden_capabilities", []))
    missing = REQUIRED_FORBIDDEN_CAPABILITIES - forbidden
    if missing:
        raise GuardrailError(f"RAG/graph adapter missing required forbidden capabilities: {sorted(missing)}")
    return record


def _safe_sandbox_vault(path: str | Path) -> Path:
    vault = Path(path).expanduser().resolve()
    if not vault.exists() or not vault.is_dir():
        raise GuardrailError(f"Sandbox vault does not exist or is not a directory: {vault}")
    if is_protected_relative(vault.name):
        raise GuardrailError(f"Sandbox vault name is protected: {vault.name}")
    if "sandbox" not in {part.lower() for part in vault.parts} and not any("sandbox" in part.lower() for part in vault.parts):
        raise GuardrailError(f"RAG/graph evaluation requires an explicit sandbox path: {vault}")
    return vault


def _markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root)
        if is_protected_relative(rel):
            continue
        files.append(path)
    return sorted(files)


def _frontmatter_tags(text: str) -> list[str]:
    if not text.startswith("---\n"):
        return []
    end = text.find("\n---", 4)
    if end == -1:
        return []
    tags: list[str] = []
    lines = text[4:end].splitlines()
    in_tags = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("tags:"):
            in_tags = True
            raw = stripped.partition(":")[2].strip()
            if raw.startswith("[") and raw.endswith("]"):
                tags.extend(item.strip().strip('"\'') for item in raw[1:-1].split(",") if item.strip())
            elif raw:
                tags.append(raw.strip('"\''))
            continue
        if in_tags and stripped.startswith("-"):
            tags.append(stripped[1:].strip().strip('"\''))
        elif in_tags and stripped and not line.startswith(" "):
            in_tags = False
    return [tag.lstrip("#") for tag in tags if tag]


def _note_key(path: Path, root: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix()


def _slug_to_note(slug: str, note_keys: set[str]) -> str | None:
    normalized = slug.strip().strip("/").removesuffix(".md")
    if normalized in note_keys:
        return normalized
    matches = [key for key in note_keys if Path(key).name == normalized]
    if len(matches) == 1:
        return matches[0]
    return None


def normalize_rag_graph_findings(sandbox_vault: str | Path) -> list[dict[str, Any]]:
    root = _safe_sandbox_vault(sandbox_vault)
    files = _markdown_files(root)
    note_keys = {_note_key(path, root) for path in files}
    notes: dict[str, dict[str, Any]] = {}
    inbound: dict[str, set[str]] = defaultdict(set)
    missing_links: list[tuple[str, str]] = []

    for path in files:
        key = _note_key(path, root)
        text = path.read_text(encoding="utf-8", errors="replace")
        links = sorted({match.strip() for match in WIKILINK_RE.findall(text) if match.strip()})
        resolved_links: list[str] = []
        for link in links:
            target = _slug_to_note(link, note_keys)
            if target is None:
                missing_links.append((key, link))
            else:
                resolved_links.append(target)
                inbound[target].add(key)
        tags = sorted(set(_frontmatter_tags(text) + TAG_RE.findall(text)))
        notes[key] = {"path": path.relative_to(root).as_posix(), "links": sorted(set(resolved_links)), "tags": tags, "chars": len(text)}

    findings: list[dict[str, Any]] = []
    for source, target in sorted(missing_links):
        findings.append(
            {
                "type": "nonexistent-link",
                "severity": "medium",
                "source": source,
                "target": target,
                "evidence": f"{source}.md links to [[{target}]], but no matching sandbox note exists.",
                "proposal_required": True,
                "executed": False,
            }
        )

    for key, data in sorted(notes.items()):
        if not data["links"] and not inbound.get(key):
            findings.append(
                {
                    "type": "orphan-note",
                    "severity": "low",
                    "source": key,
                    "evidence": "No inbound or outbound wikilinks found in sandbox copy.",
                    "proposal_required": True,
                    "executed": False,
                }
            )

    tag_to_notes: dict[str, list[str]] = defaultdict(list)
    for key, data in notes.items():
        for tag in data["tags"]:
            tag_to_notes[tag].append(key)

    for tag, members in sorted(tag_to_notes.items()):
        unique_members = sorted(set(members))
        if len(unique_members) < 2:
            continue
        findings.append(
            {
                "type": "moc-candidate",
                "severity": "low",
                "cluster": tag,
                "notes": unique_members,
                "evidence": f"{len(unique_members)} sandbox notes share tag `{tag}`.",
                "proposal_required": True,
                "executed": False,
            }
        )
        for left in unique_members:
            linked = set(notes[left]["links"])
            for right in unique_members:
                if left != right and right not in linked:
                    findings.append(
                        {
                            "type": "candidate-backlink",
                            "severity": "low",
                            "source": left,
                            "target": right,
                            "evidence": f"Both notes share tag `{tag}` but are not linked in the sandbox graph.",
                            "proposal_required": True,
                            "executed": False,
                        }
                    )
                    break

    basename_counts = Counter(Path(key).stem.lower() for key in note_keys)
    for basename, count in sorted(basename_counts.items()):
        if count > 1:
            findings.append(
                {
                    "type": "duplicate-candidate",
                    "severity": "medium",
                    "name": basename,
                    "notes": sorted(key for key in note_keys if Path(key).stem.lower() == basename),
                    "evidence": "Multiple sandbox notes share the same case-insensitive basename.",
                    "proposal_required": True,
                    "executed": False,
                }
            )

    findings.append(
        {
            "type": "graph-summary",
            "severity": "info",
            "notes_scanned": len(files),
            "wikilinks_resolved": sum(len(data["links"]) for data in notes.values()),
            "findings_before_summary": len(findings),
            "proposal_required": False,
            "executed": False,
        }
    )
    return findings


def _finding_source_label(finding: dict[str, Any]) -> str:
    return str(finding.get("source") or finding.get("cluster") or finding.get("name") or "sandbox")


def _matches_source_prefix(finding: dict[str, Any], prefixes: list[str]) -> bool:
    label = _finding_source_label(finding)
    return any(label == prefix or label.startswith(f"{prefix}/") for prefix in prefixes)


def build_rag_graph_adapter_evaluation(
    *,
    adapter_record: str | Path,
    sandbox_vault: str | Path,
    fixed_queries: list[str] | None = None,
    artifact_root: str | Path | None = None,
    source_exclude_prefixes: list[str] | None = None,
) -> RagGraphAdapterEvaluation:
    started = time.perf_counter()
    record = load_rag_graph_adapter_record(adapter_record)
    sandbox = _safe_sandbox_vault(sandbox_vault)
    queries = fixed_queries or [
        "Find notes related to Obsidian Operating Layer.",
        "Find orphan notes with high connection potential.",
        "Suggest MOC for automation/safety architecture.",
        "Detect possible duplicates among project reports.",
        "Suggest backlinks for final architecture spec.",
    ]
    raw_findings = normalize_rag_graph_findings(sandbox)
    prefixes = sorted(set(source_exclude_prefixes or []))
    excluded_findings = [item for item in raw_findings if _matches_source_prefix(item, prefixes)]
    findings = [item for item in raw_findings if not _matches_source_prefix(item, prefixes)]
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    max_rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    direct_write_disabled = all(item.get("executed") is False for item in findings)
    proposal_only_types = {item["type"] for item in findings if item.get("proposal_required") is True}
    proposal_only_allowed = PROPOSAL_ONLY_FINDING_TYPES | {"nonexistent-link", "orphan-note"}
    finding_counts_by_type = Counter(item["type"] for item in findings)
    finding_counts_by_severity = Counter(item["severity"] for item in findings)
    top_sources_by_finding_count = Counter(_finding_source_label(item) for item in findings).most_common(10)
    excluded_counts_by_type = Counter(item["type"] for item in excluded_findings)

    artifacts: dict[str, str] = {}
    if artifact_root is not None:
        root = Path(artifact_root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        stem = record["name"].replace("/", "-").replace(" ", "-")
        artifacts = {"json_report": str(root / f"rag-graph-evaluation-{stem}-{utc_stamp()}.json")}

    return RagGraphAdapterEvaluation(
        adapter=record["name"],
        source_id=record["source"]["id"],
        sandbox_vault=str(sandbox),
        allowed_capabilities=sorted(record.get("capabilities", [])),
        forbidden_capabilities=sorted(record.get("forbidden_capabilities", [])),
        direct_write_disabled=direct_write_disabled,
        sandbox_required=True,
        write_policy="normalize-findings-only-and-convert-write-like-suggestions-to-proposals",
        fixed_queries=queries,
        source_exclude_prefixes=prefixes,
        findings=findings,
        artifacts=artifacts,
        verification={
            "sandboxed": True,
            "direct_write_disabled": direct_write_disabled,
            "normalized_findings_only": all("type" in item and item.get("executed") is False for item in findings),
            "proposal_only_for_write_like_suggestions": proposal_only_types <= proposal_only_allowed,
            "notes_scanned": next((item["notes_scanned"] for item in findings if item["type"] == "graph-summary"), 0),
            "fixed_query_count": len(queries),
            "finding_count": len(findings),
            "raw_finding_count": len(raw_findings),
            "excluded_finding_count": len(excluded_findings),
            "source_exclude_prefixes": prefixes,
            "excluded_counts_by_type": dict(sorted(excluded_counts_by_type.items())),
            "finding_counts_by_type": dict(sorted(finding_counts_by_type.items())),
            "finding_counts_by_severity": dict(sorted(finding_counts_by_severity.items())),
            "top_sources_by_finding_count": [
                {"source": source, "count": count} for source, count in top_sources_by_finding_count
            ],
            "benchmark_metrics": {
                "wall_time_ms": elapsed_ms,
                "max_rss_kb": max_rss_kb,
                "cost_model": "local-wrapper-no-llm-call",
            },
        },
    )


def write_rag_graph_adapter_evaluation(evaluation: RagGraphAdapterEvaluation, out: str | Path) -> None:
    write_json(out, {"status": "ok", **evaluation.to_dict()})


def rag_graph_evaluation_to_markdown(evaluation: RagGraphAdapterEvaluation) -> str:
    lines = [
        f"# RAG/graph adapter evaluation: {evaluation.adapter}",
        "",
        f"- source: `{evaluation.source_id}`",
        f"- sandbox_vault: `{evaluation.sandbox_vault}`",
        f"- direct_write_disabled: `{evaluation.direct_write_disabled}`",
        f"- write_policy: `{evaluation.write_policy}`",
        f"- source_exclude_prefixes: `{evaluation.source_exclude_prefixes}`",
        "",
        "## Fixed queries",
    ]
    lines.extend(f"- {query}" for query in evaluation.fixed_queries)
    lines.extend(
        [
            "",
            "## Finding summary",
            "- raw findings before source-prefix filtering: "
            f"`{evaluation.verification.get('raw_finding_count', len(evaluation.findings))}`",
            "- active findings after source-prefix filtering: "
            f"`{evaluation.verification.get('finding_count', len(evaluation.findings))}`",
            f"- excluded findings: `{evaluation.verification.get('excluded_finding_count', 0)}`",
            "",
            "### Counts by type",
        ]
    )
    for finding_type, count in evaluation.verification.get("finding_counts_by_type", {}).items():
        lines.append(f"- `{finding_type}`: {count}")
    lines.extend(["", "### Counts by severity"])
    for severity, count in evaluation.verification.get("finding_counts_by_severity", {}).items():
        lines.append(f"- `{severity}`: {count}")
    lines.extend(["", "### Top sources by finding count"])
    for item in evaluation.verification.get("top_sources_by_finding_count", []):
        lines.append(f"- `{item['source']}`: {item['count']}")
    if evaluation.verification.get("excluded_counts_by_type"):
        lines.extend(["", "### Excluded counts by type"])
        for finding_type, count in evaluation.verification["excluded_counts_by_type"].items():
            lines.append(f"- `{finding_type}`: {count}")

    lines.extend(["", "## Normalized findings"])
    for finding in evaluation.findings:
        label = finding.get("source") or finding.get("cluster") or finding.get("name") or "sandbox"
        lines.append(f"- `{finding['type']}` / `{finding['severity']}` / `{label}` — {finding.get('evidence', 'summary finding')}")
    lines.extend(
        [
            "",
            "## Verification",
            "```json",
            json.dumps(evaluation.verification, indent=2, sort_keys=True),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"
