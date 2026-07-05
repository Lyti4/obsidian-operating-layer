from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .candidate_scorer_v1 import score_candidate

MODE = "external-tool-benchmark-v1"


@dataclass(frozen=True)
class ExternalToolBenchmarkReport:
    mode: str
    status: str
    benchmark_id: str
    created_at: str
    behavior: str
    live_mutation_authorized: bool
    approval_manifest_created: bool
    direct_write_disabled: bool
    no_write_sandbox: bool
    read_only_comparison: bool
    targets: list[Any]
    tool_policy: dict[str, Any]
    scorer_packets: list[dict[str, Any]]
    reference_tools: list[dict[str, Any]]
    comparisons: list[dict[str, Any]]
    differences: list[dict[str, Any]]
    scorer_test_cases: list[dict[str, Any]]
    proposals: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_external_tool_benchmark_report(
    scored_packets: Iterable[Mapping[str, Any]] | None = None,
    *,
    benchmark_id: str | None = None,
    created_at: str | None = None,
) -> ExternalToolBenchmarkReport:
    packets = [_normalize_mapping(packet) for packet in (scored_packets or _default_scored_packets())]
    reference_tools = _reference_tools()
    comparisons: list[dict[str, Any]] = []
    differences: list[dict[str, Any]] = []
    scorer_test_cases: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []

    for tool in reference_tools:
        for packet in packets:
            comparison = _compare_tool_to_packet(tool, packet)
            comparisons.append(comparison)
            if comparison["difference"] is not None:
                difference = comparison["difference"]
                differences.append(difference)
                scorer_test_cases.append(_difference_to_test_case(difference))
                proposals.append(_difference_to_proposal(difference))

    return ExternalToolBenchmarkReport(
        mode=MODE,
        status="ok",
        benchmark_id=benchmark_id or f"external-tool-benchmark-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        created_at=created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        behavior="evidence-only",
        live_mutation_authorized=False,
        approval_manifest_created=False,
        direct_write_disabled=True,
        no_write_sandbox=True,
        read_only_comparison=True,
        targets=[],
        tool_policy={
            "external_tool_execution": "not-executed; deterministic repo-local comparison only",
            "write_capable_tools": "preview-or-read-only-mode-only",
            "difference_handling": "scorer_test_cases_or_proposals_only",
            "direct_edits_allowed": False,
        },
        scorer_packets=packets,
        reference_tools=reference_tools,
        comparisons=comparisons,
        differences=differences,
        scorer_test_cases=scorer_test_cases,
        proposals=proposals,
    )


def external_tool_benchmark_to_markdown(report: ExternalToolBenchmarkReport | Mapping[str, Any]) -> str:
    data = report.to_dict() if isinstance(report, ExternalToolBenchmarkReport) else _normalize_mapping(report)
    lines = [
        "# External tool benchmark",
        "",
        f"Benchmark id: `{data['benchmark_id']}`",
        f"Status: `{data['status']}`",
        "",
        "## Safety",
        "",
        f"- behavior: `{data['behavior']}`",
        f"- live_mutation_authorized: `{data['live_mutation_authorized']}`",
        f"- approval_manifest_created: `{data['approval_manifest_created']}`",
        f"- direct_write_disabled: `{data['direct_write_disabled']}`",
        f"- no_write_sandbox: `{data['no_write_sandbox']}`",
        f"- read_only_comparison: `{data['read_only_comparison']}`",
        f"- targets: `{len(data['targets'])}`",
        "",
        "## Reference tools",
        "",
        "Execution note: this is a deterministic read-only pattern simulation/comparison;",
        "no external tool subprocess, API, or write mode is executed by this benchmark.",
        "",
    ]
    for tool in data["reference_tools"]:
        lines.append(
            f"- `{tool['tool_id']}`: mode=`{tool['required_mode']}`, write_capable=`{tool['write_capable']}`, "
            f"executed=`{tool['executed']}`"
        )
    lines.extend(
        [
            "",
            "## Differences converted to tests/proposals",
            "",
            f"- comparisons: `{len(data['comparisons'])}`",
            f"- differences: `{len(data['differences'])}`",
            f"- scorer_test_cases: `{len(data['scorer_test_cases'])}`",
            f"- proposals: `{len(data['proposals'])}`",
            "",
        ]
    )
    for difference in data["differences"]:
        lines.append(
            f"- `{difference['tool_id']}` vs `{difference['source']}`: `{difference['difference_kind']}` → "
            f"test_case=`{difference['test_case_id']}`"
        )
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "Differences are captured as scorer test cases/proposals only. No note, vault, or approval-manifest target is produced.",
            "",
        ]
    )
    return "\n".join(lines)


def write_external_tool_benchmark_report(
    scored_packets: Iterable[Mapping[str, Any]] | None = None,
    *,
    out_dir: str | Path,
    benchmark_id: str | None = None,
) -> dict[str, str]:
    report = build_external_tool_benchmark_report(scored_packets, benchmark_id=benchmark_id)
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "external-tool-benchmark.json"
    markdown_path = root / "REPORT.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(external_tool_benchmark_to_markdown(report), encoding="utf-8")
    return {"status": "ok", "report_json": str(json_path), "report_markdown": str(markdown_path)}


def _default_scored_packets() -> list[dict[str, Any]]:
    notes_by_path = {
        "Memory/A.md": {"path": "Memory/A.md", "top": "Memory"},
        "Memory/B.md": {"path": "Memory/B.md", "top": "Memory"},
        "_Archive/B.md": {"path": "_Archive/B.md", "top": "_Archive", "protected_or_archive_surface": True},
    }
    ambiguous = score_candidate(
        link={"source": "Memory/A.md", "status": "ambiguous", "old_link": "[[B]]", "candidates": ["Memory/B.md", "_Archive/B.md"]},
        notes_by_path=notes_by_path,
    )
    ambiguous["old_link"] = "[[B]]"
    broken = score_candidate(
        link={"source": "Memory/A.md", "status": "broken", "old_link": "[[Missing]]", "candidates": []},
        notes_by_path=notes_by_path,
    )
    broken["old_link"] = "[[Missing]]"
    return [ambiguous, broken]


def _reference_tools() -> list[dict[str, Any]]:
    return [
        {
            "tool_id": "wikilink-linter-preview",
            "pattern": "preview-before-write-and-skip-ambiguous",
            "write_capable": True,
            "required_mode": "preview-no-write",
            "executed": False,
            "write_attempted": False,
            "direct_write_disabled": True,
        },
        {
            "tool_id": "vault-inspector-readonly",
            "pattern": "read-only-health-audit",
            "write_capable": False,
            "required_mode": "read-only-audit",
            "executed": False,
            "write_attempted": False,
            "direct_write_disabled": True,
        },
        {
            "tool_id": "obsidian-api-link-semantics",
            "pattern": "metadata-cache-resolved-unresolved-links",
            "write_capable": True,
            "required_mode": "metadata-cache-read-only",
            "executed": False,
            "write_attempted": False,
            "direct_write_disabled": True,
        },
        {
            "tool_id": "dataview-query-surface",
            "pattern": "query-only-link-health-table",
            "write_capable": False,
            "required_mode": "read-only-query",
            "executed": False,
            "write_attempted": False,
            "direct_write_disabled": True,
        },
    ]


def _compare_tool_to_packet(tool: Mapping[str, Any], packet: Mapping[str, Any]) -> dict[str, Any]:
    source = str(packet.get("source", ""))
    status = str(packet.get("status", ""))
    candidate_count = len(packet.get("candidates") or [])
    review_required = bool(packet.get("review_required"))
    hard_stop = bool(packet.get("hard_stop"))
    tool_id = str(tool["tool_id"])
    external_decision = _external_decision(tool_id, status, candidate_count)
    scorer_decision = _scorer_decision(review_required=review_required, hard_stop=hard_stop, candidate_count=candidate_count)
    difference = _comparison_difference(
        tool_id=tool_id,
        source=source,
        status=status,
        external_decision=external_decision,
        scorer_decision=scorer_decision,
        review_required=review_required,
    )
    return {
        "tool_id": tool_id,
        "source": source,
        "status": status,
        "external_decision": external_decision,
        "scorer_decision": scorer_decision,
        "candidate_count": candidate_count,
        "read_only": True,
        "write_attempted": False,
        "difference": difference,
    }


def _external_decision(tool_id: str, status: str, candidate_count: int) -> str:
    if tool_id == "wikilink-linter-preview" and (status == "ambiguous" or candidate_count != 1):
        return "skip-ambiguous-preview-only"
    if tool_id == "vault-inspector-readonly" and status in {"broken", "ambiguous"}:
        return f"report-{status}-health-finding"
    if tool_id == "obsidian-api-link-semantics":
        if status == "broken":
            return "metadata-cache-unresolved-link"
        if status == "ambiguous" or candidate_count > 1:
            return "metadata-cache-multiple-resolution-candidates"
    if tool_id == "dataview-query-surface":
        return "query-row-no-mutation"
    return "no-action-read-only"


def _scorer_decision(*, review_required: bool, hard_stop: bool, candidate_count: int) -> str:
    if hard_stop:
        return "hard-stop-review-only"
    if review_required:
        return "operator-review-required"
    if candidate_count == 1:
        return "single-candidate-evidence-only"
    return "evidence-only"


def _comparison_difference(
    *,
    tool_id: str,
    source: str,
    status: str,
    external_decision: str,
    scorer_decision: str,
    review_required: bool,
) -> dict[str, Any] | None:
    if tool_id == "dataview-query-surface":
        return None
    if external_decision == scorer_decision:
        return None
    if status in {"broken", "ambiguous"} or review_required:
        difference_kind = "external-readonly-signal-to-scorer-regression-case"
        test_case_id = _test_case_id(tool_id, source, status)
        return {
            "tool_id": tool_id,
            "source": source,
            "status": status,
            "difference_kind": difference_kind,
            "external_decision": external_decision,
            "scorer_decision": scorer_decision,
            "test_case_id": test_case_id,
            "direct_edit_allowed": False,
            "proposal_required": True,
        }
    return None


def _difference_to_test_case(difference: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "test_case_id": difference["test_case_id"],
        "source": difference["source"],
        "tool_id": difference["tool_id"],
        "status": difference["status"],
        "expected_behavior": "preserve-review-gate-and-no-live-mutation",
        "live_mutation_authorized": False,
        "approval_manifest_created": False,
    }


def _difference_to_proposal(difference: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "proposal_id": f"proposal-{difference['test_case_id']}",
        "proposal_type": "scorer-test-case",
        "source": difference["source"],
        "reason": difference["difference_kind"],
        "target_files": [],
        "direct_edit_allowed": False,
        "live_mutation_authorized": False,
    }


def _test_case_id(tool_id: str, source: str, status: str) -> str:
    slug = f"{tool_id}-{source}-{status}".lower()
    normalized = "".join(char if char.isalnum() else "-" for char in slug).strip("-")
    return normalized[:96]


def _normalize_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()}
