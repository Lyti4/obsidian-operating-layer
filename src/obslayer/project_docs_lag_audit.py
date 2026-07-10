from __future__ import annotations

import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError


@dataclass(frozen=True)
class DocLagCheck:
    name: str
    document: str
    required_markers: list[str]
    status: str
    missing_markers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectDocsLagAudit:
    status: str
    generated_utc: str
    repo: str
    checks: list[DocLagCheck]
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = [check.to_dict() for check in self.checks]
        return payload


@dataclass(frozen=True)
class ToolRegistryEntry:
    tool: str
    purpose: str
    kind: str
    family: str
    mode: str
    write_surface: str
    inputs: str
    outputs: str
    test: str
    instruction: str
    spec: str
    status: str
    line_number: int


TOOL_REGISTRY_HEADER: tuple[str, ...] = (
    "tool",
    "purpose",
    "kind",
    "family",
    "mode",
    "write_surface",
    "inputs",
    "outputs",
    "test",
    "instruction",
    "spec",
    "status",
)

ALLOWED_KINDS = {"cli", "internal"}
ALLOWED_FAMILIES = {
    "hermes-memory",
    "core-vault-workflow",
    "indexing-graphify-semantic",
    "link-hygiene",
    "operator-control-plane",
    "agent-collaboration",
    "reports-evidence",
    "internal-support",
}
ALLOWED_MODES = {"read-only", "proposal-only", "sandbox", "approved-write"}
ALLOWED_STATUSES = {"active", "experimental", "deprecated", "internal"}

INSTRUCTION_TARGETS = (
    "AGENTS.md",
    "docs/AGENTS.md",
    "docs/INSTRUCTION_TREE.md",
    "docs/agents/AGENTS.md",
    "docs/tools/INDEX.md",
    "tools/AGENTS.md",
    "src/obslayer/AGENTS.md",
    "tests/AGENTS.md",
    ".specify/memory/constitution.md",
    ".specify/feature.json",
    "docs/RUNTIME_STATUS.md",
)

SECRET_SCAN_ROOTS = (
    ".specify",
    "specs",
    "AGENTS.md",
    "docs",
    "tools/AGENTS.md",
    "src/obslayer/AGENTS.md",
    "tests/AGENTS.md",
)
SECRET_SHAPE_RE = re.compile(
    r"(?i)(-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s`'\"]{8,})"
)


def tracked_tool_paths(repo: str | Path) -> set[str]:
    repo_path = Path(repo).expanduser().resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "ls-files", "--", "tools/*.py"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0:
        return {
            line.strip().replace("\\", "/")
            for line in result.stdout.splitlines()
            if line.strip()
        }

    tools_dir = repo_path / "tools"
    if not tools_dir.is_dir():
        return set()
    return {
        path.relative_to(repo_path).as_posix()
        for path in tools_dir.glob("*.py")
        if path.is_file()
    }


def _tool_registry_cells(line: str) -> list[str]:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return [
        cell[1:-1].strip()
        if len(cell) >= 2 and cell.startswith("`") and cell.endswith("`")
        else cell
        for cell in cells
    ]


def _find_tool_registry_header(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if line.startswith("|") and tuple(_tool_registry_cells(line)) == TOOL_REGISTRY_HEADER:
            return index
    return None


def parse_tool_registry(path: str | Path) -> list[ToolRegistryEntry]:
    registry_path = Path(path).expanduser()
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    header_line = _find_tool_registry_header(lines)
    if header_line is None:
        raise ValueError(f"Tool registry header not found: {registry_path}")

    entries: list[ToolRegistryEntry] = []
    for index, line in enumerate(lines[header_line + 2 :], start=header_line + 3):
        if not line.startswith("|"):
            if entries or line.strip():
                break
            continue
        cells = _tool_registry_cells(line)
        if len(cells) != len(TOOL_REGISTRY_HEADER):
            raise ValueError(f"Tool registry row {index} has {len(cells)} cells; expected 12")
        entries.append(ToolRegistryEntry(*cells, line_number=index))
    return entries


def _check(name: str, document: str, failures: list[str]) -> DocLagCheck:
    return DocLagCheck(
        name=name,
        document=document,
        required_markers=[],
        status="ok" if not failures else "lagging",
        missing_markers=failures,
    )


def _path_exists(repo_path: Path, rel: str) -> bool:
    return (repo_path / rel).exists()


def _test_target_exists(repo_path: Path, target: str) -> bool:
    if target.startswith("covered-by:"):
        target = target.removeprefix("covered-by:")
    return target.startswith("tests/") and _path_exists(repo_path, target)


def _tool_registry_checks(repo_path: Path) -> list[DocLagCheck]:
    registry_rel = "docs/tools/INDEX.md"
    registry_path = repo_path / registry_rel
    checks: list[DocLagCheck] = []

    if not registry_path.is_file():
        checks.append(_check("tool_registry_document_present", registry_rel, [registry_rel]))
        for name in (
            "tool_registry_parseable",
            "tool_registry_complete",
            "tool_registry_no_stale_entries",
            "tool_registry_unique",
            "tool_registry_required_fields",
            "tool_registry_controlled_values",
            "tool_registry_cross_field_rules",
            "tool_registry_references_exist",
        ):
            checks.append(_check(name, registry_rel, ["registry unavailable"]))
        return checks

    lines = registry_path.read_text(encoding="utf-8", errors="replace").splitlines()
    header_line = _find_tool_registry_header(lines)
    checks.append(_check("tool_registry_document_present", registry_rel, [] if header_line is not None else ["table header"] ))
    if header_line is None:
        checks.append(_check("tool_registry_parseable", registry_rel, ["table header"] ))
        return checks

    try:
        entries = parse_tool_registry(registry_path)
        parse_failures: list[str] = []
    except ValueError as exc:
        entries = []
        parse_failures = [str(exc)]
    checks.append(_check("tool_registry_parseable", registry_rel, parse_failures))
    if parse_failures:
        return checks

    tracked = tracked_tool_paths(repo_path)
    documented = [entry.tool for entry in entries]
    documented_set = set(documented)
    counts = Counter(documented)
    line_numbers: dict[str, list[int]] = defaultdict(list)
    for entry in entries:
        line_numbers[entry.tool].append(entry.line_number)

    checks.append(_check("tool_registry_complete", registry_rel, sorted(tracked - documented_set)))
    checks.append(_check("tool_registry_no_stale_entries", registry_rel, sorted(documented_set - tracked)))
    checks.append(
        _check(
            "tool_registry_unique",
            registry_rel,
            [f"{tool}:lines={','.join(map(str, line_numbers[tool]))}" for tool, count in sorted(counts.items()) if count > 1],
        )
    )

    required_failures: list[str] = []
    controlled_failures: list[str] = []
    cross_failures: list[str] = []
    ref_failures: list[str] = []
    for entry in entries:
        for field in TOOL_REGISTRY_HEADER:
            value = getattr(entry, field)
            if not value:
                required_failures.append(f"{entry.tool}:{field}")
        if entry.kind not in ALLOWED_KINDS:
            controlled_failures.append(f"{entry.tool}:kind={entry.kind}")
        if entry.family not in ALLOWED_FAMILIES:
            controlled_failures.append(f"{entry.tool}:family={entry.family}")
        if entry.mode not in ALLOWED_MODES:
            controlled_failures.append(f"{entry.tool}:mode={entry.mode}")
        if entry.status not in ALLOWED_STATUSES:
            controlled_failures.append(f"{entry.tool}:status={entry.status}")

        if entry.kind == "internal":
            if entry.family != "internal-support":
                cross_failures.append(f"{entry.tool}:internal-family")
            if entry.status != "internal":
                cross_failures.append(f"{entry.tool}:internal-status")
            if not entry.test.startswith("covered-by:"):
                cross_failures.append(f"{entry.tool}:internal-covered-by")
        if entry.kind == "cli" and entry.status == "internal":
            cross_failures.append(f"{entry.tool}:cli-internal-status")
        if entry.mode == "read-only" and entry.write_surface != "none":
            cross_failures.append(f"{entry.tool}:read-only-write-surface")
        if entry.mode == "approved-write" and not entry.instruction.startswith("docs/runbooks/"):
            cross_failures.append(f"{entry.tool}:approved-write-runbook")

        if not _test_target_exists(repo_path, entry.test):
            ref_failures.append(f"{entry.tool}:test:{entry.test}")
        if not _path_exists(repo_path, entry.instruction):
            ref_failures.append(f"{entry.tool}:instruction:{entry.instruction}")
        if entry.spec != "none" and not _path_exists(repo_path, entry.spec):
            ref_failures.append(f"{entry.tool}:spec:{entry.spec}")

    checks.append(_check("tool_registry_required_fields", registry_rel, sorted(required_failures)))
    checks.append(_check("tool_registry_controlled_values", registry_rel, sorted(controlled_failures)))
    checks.append(_check("tool_registry_cross_field_rules", registry_rel, sorted(cross_failures)))
    checks.append(_check("tool_registry_references_exist", registry_rel, sorted(ref_failures)))
    return checks


def _instruction_link_checks(repo_path: Path) -> list[DocLagCheck]:
    failures = [rel for rel in INSTRUCTION_TARGETS if not _path_exists(repo_path, rel)]
    tree = repo_path / "docs/INSTRUCTION_TREE.md"
    if tree.is_file():
        text = tree.read_text(encoding="utf-8", errors="replace")
        root_text = (repo_path / "AGENTS.md").read_text(encoding="utf-8", errors="replace")
        for rel in INSTRUCTION_TARGETS:
            if rel != "docs/INSTRUCTION_TREE.md" and rel not in text and rel not in root_text:
                failures.append(f"unlinked:{rel}")
        if "<!-- navigation-table:start -->" in text and "<!-- navigation-table:end -->" in text:
            table = text.split("<!-- navigation-table:start -->", 1)[1].split("<!-- navigation-table:end -->", 1)[0]
            for line in table.splitlines():
                if not line.startswith("| `"):
                    continue
                cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
                for rel in cells[1:3]:
                    if rel and not _path_exists(repo_path, rel):
                        failures.append(f"navigation:{rel}")
    checks = [_check("instruction_tree_references_exist", "docs/INSTRUCTION_TREE.md", sorted(set(failures)))]
    return checks


def instruction_artifacts_secret_shape_findings(repo: str | Path) -> list[str]:
    repo_path = Path(repo).expanduser().resolve()
    findings: set[str] = set()
    candidates: list[Path] = []
    for root in SECRET_SCAN_ROOTS:
        path = repo_path / root
        if path.is_file():
            candidates.append(path)
        elif path.is_dir():
            candidates.extend(p for p in path.rglob("*.md") if p.is_file())
            candidates.extend(p for p in path.rglob("*.json") if p.is_file())
    for path in candidates:
        rel = path.relative_to(repo_path).as_posix()
        if rel.startswith("out/"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if SECRET_SHAPE_RE.search(text):
            findings.add(rel)
    return sorted(findings)


def run_project_docs_lag_audit(repo: str | Path, *, generated_utc: str | None = None) -> ProjectDocsLagAudit:
    repo_path = Path(repo).expanduser().resolve()
    if not repo_path.is_dir():
        raise GuardrailError(f"Repo path is not a directory: {repo_path}")

    checks = [*_tool_registry_checks(repo_path), *_instruction_link_checks(repo_path)]
    secret_findings = instruction_artifacts_secret_shape_findings(repo_path)
    checks.append(_check("instruction_artifacts_no_secret_shapes", "instruction artifacts", secret_findings))

    findings: list[str] = []
    for check in checks:
        if check.status != "ok":
            findings.append(f"{check.name}: {', '.join(check.missing_markers)}")

    return ProjectDocsLagAudit(
        status="ok" if not findings else "lagging",
        generated_utc=generated_utc or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo=str(repo_path),
        checks=checks,
        findings=findings,
    )


def project_docs_lag_audit_to_markdown(audit: ProjectDocsLagAudit) -> str:
    lines = [
        "# Project Docs Lag Audit",
        "",
        f"Status: `{audit.status}`",
        f"Generated UTC: `{audit.generated_utc}`",
        f"Repo: `{audit.repo}`",
        "",
        "## Checks",
        "",
        "| check | status | document | findings |",
        "|---|---|---|---|",
    ]
    for check in audit.checks:
        missing = ", ".join(marker.replace("|", "\\|") for marker in check.missing_markers) or "none"
        lines.append(f"| `{check.name}` | `{check.status}` | `{check.document}` | {missing} |")
    lines.extend(["", "## Findings", ""])
    if audit.findings:
        lines.extend(f"- {finding}" for finding in audit.findings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            (
                "This audit is read-only and checks repository documentation structure. "
                "It does not authorize live vault mutation or approval manifests."
            ),
            "",
        ]
    )
    return "\n".join(lines)
