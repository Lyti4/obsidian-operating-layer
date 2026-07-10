import subprocess
from pathlib import Path

import pytest

from obslayer.project_docs_lag_audit import (
    instruction_artifacts_secret_shape_findings,
    parse_tool_registry,
    project_docs_lag_audit_to_markdown,
    run_project_docs_lag_audit,
    tracked_tool_paths,
)

REPO = Path(__file__).resolve().parents[1]


def _registry_row(
    tool: str = "tools/example.py",
    *,
    purpose: str = "fixture",
    kind: str = "cli",
    family: str = "reports-evidence",
    mode: str = "read-only",
    write_surface: str = "none",
    inputs: str = "args",
    outputs: str = "stdout",
    test: str = "tests/test_project_docs_lag_audit.py",
    instruction: str = "docs/tools/families/reports-evidence.md",
    spec: str = "none",
    status: str = "active",
) -> str:
    values = [tool, purpose, kind, family, mode, write_surface, inputs, outputs, test, instruction, spec, status]
    return "| " + " | ".join(f"`{v}`" if i in {0, 8, 9, 10} and v != "none" else v for i, v in enumerate(values)) + " |\n"


def _write_minimal_docs(repo: Path) -> None:
    instruction_links = "\n".join(
        [
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
        ]
    )
    docs = {
        "AGENTS.md": instruction_links + "\nmust not weaken\n",
        "README.md": "docs/INSTRUCTION_TREE.md\ndocs/tools/INDEX.md\n.specify/feature.json\n",
        "SECURITY.md": "AGENTS.md\ndocs/INSTRUCTION_TREE.md\nsrc/obslayer/AGENTS.md\n",
        "docs/AGENTS.md": "documentation scope\n",
        "docs/agents/AGENTS.md": "agent contract scope\n",
        "tools/AGENTS.md": "tool scope\n",
        "src/obslayer/AGENTS.md": "safety core scope\n",
        "tests/AGENTS.md": "test scope\n",
        "docs/RUNTIME_STATUS.md": "runtime status\n",
        ".specify/memory/constitution.md": "constitution\n",
        ".specify/feature.json": "{\"feature_directory\": \"specs/001-instruction-tree-tool-documentation\"}\n",
        "docs/INSTRUCTION_TREE.md": (
            instruction_links
            + "\n<!-- navigation-table:start -->\n"
            + "| area | nearest | follow-up | max links |\n"
            + "|---|---|---|---|\n"
            + "| `/` | `AGENTS.md` | `docs/INSTRUCTION_TREE.md` | `1` |\n"
            + "| `docs/` | `docs/AGENTS.md` | `docs/INSTRUCTION_TREE.md` | `2` |\n"
            + "| `docs/agents/` | `docs/agents/AGENTS.md` | `docs/agents/AGENTS.md` | `2` |\n"
            + "| `tools/` | `tools/AGENTS.md` | `docs/tools/INDEX.md` | `2` |\n"
            + "| `src/obslayer/` | `src/obslayer/AGENTS.md` | `docs/TOOLS_POLICY.md` | `2` |\n"
            + "| `tests/` | `tests/AGENTS.md` | `tests/AGENTS.md` | `2` |\n"
            + "<!-- navigation-table:end -->\n"
        ),
        "docs/TOOLS_POLICY.md": "policy\n",
        "docs/tools/families/reports-evidence.md": "guide\n",
        "docs/tools/INDEX.md": (
            "| tool | purpose | kind | family | mode | write_surface | inputs | outputs | test | instruction | spec | status |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            + _registry_row()
        ),
        "tools/example.py": "raise SystemExit(0)\n",
        "tests/test_project_docs_lag_audit.py": "def test_fixture():\n    assert True\n",
    }
    for rel, text in docs.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _replace_registry(repo: Path, rows: list[str]) -> None:
    (repo / "docs/tools/INDEX.md").write_text(
        "| tool | purpose | kind | family | mode | write_surface | inputs | outputs | test | instruction | spec | status |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        + "".join(rows),
        encoding="utf-8",
    )


def _check(audit, name: str):
    return next(check for check in audit.checks if check.name == name)


def test_project_docs_lag_audit_ok(tmp_path: Path) -> None:
    _write_minimal_docs(tmp_path)

    audit = run_project_docs_lag_audit(tmp_path, generated_utc="2026-07-04T00:00:00Z")
    text = project_docs_lag_audit_to_markdown(audit)

    assert audit.status == "ok"
    assert all(check.status == "ok" for check in audit.checks)
    assert "Status: `ok`" in text
    assert "- none" in text
    assert "repository documentation structure" in text


@pytest.mark.parametrize(
    ("mutation", "check_name"),
    [
        ("missing_registry", "tool_registry_document_present"),
        ("malformed_row", "tool_registry_parseable"),
        ("missing_tool", "tool_registry_complete"),
        ("stale_tool", "tool_registry_no_stale_entries"),
        ("duplicate_tool", "tool_registry_unique"),
        ("empty_field", "tool_registry_required_fields"),
        ("invalid_value", "tool_registry_controlled_values"),
        ("cross_field", "tool_registry_cross_field_rules"),
        ("missing_reference", "tool_registry_references_exist"),
        ("missing_instruction_target", "instruction_tree_references_exist"),
        ("secret_shape", "instruction_artifacts_no_secret_shapes"),
    ],
)
def test_project_docs_lag_audit_structural_failures(tmp_path: Path, mutation: str, check_name: str) -> None:
    _write_minimal_docs(tmp_path)
    if mutation == "missing_registry":
        (tmp_path / "docs/tools/INDEX.md").unlink()
    elif mutation == "malformed_row":
        (tmp_path / "docs/tools/INDEX.md").write_text(
            "| tool | purpose | kind | family | mode | write_surface | inputs | outputs | test | instruction | spec | status |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| `tools/example.py` | too-short |\n",
            encoding="utf-8",
        )
    elif mutation == "missing_tool":
        (tmp_path / "tools/missing.py").write_text("\n", encoding="utf-8")
    elif mutation == "stale_tool":
        _replace_registry(tmp_path, [_registry_row(), _registry_row("tools/stale.py")])
    elif mutation == "duplicate_tool":
        _replace_registry(tmp_path, [_registry_row(), _registry_row(purpose="duplicate")])
    elif mutation == "empty_field":
        _replace_registry(tmp_path, [_registry_row(purpose="")])
    elif mutation == "invalid_value":
        _replace_registry(tmp_path, [_registry_row(kind="worker")])
    elif mutation == "cross_field":
        _replace_registry(
            tmp_path,
            [_registry_row(kind="internal", family="reports-evidence", status="active", test="tests/test_project_docs_lag_audit.py")],
        )
    elif mutation == "missing_reference":
        _replace_registry(tmp_path, [_registry_row(test="tests/missing.py")])
    elif mutation == "missing_instruction_target":
        (tmp_path / "docs/AGENTS.md").unlink()
    elif mutation == "secret_shape":
        (tmp_path / "docs/AGENTS.md").write_text("api_key = abcdefghijklmnop\n", encoding="utf-8")

    audit = run_project_docs_lag_audit(tmp_path)

    assert audit.status == "lagging"
    assert _check(audit, check_name).status == "lagging"
    assert _check(audit, check_name).missing_markers


def test_instruction_artifacts_do_not_contain_secret_shapes(tmp_path: Path) -> None:
    _write_minimal_docs(tmp_path)
    secret_file = tmp_path / "specs/001-instruction-tree-tool-documentation/spec.md"
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    secret_file.write_text("token: supersecretvalue\n", encoding="utf-8")

    findings = instruction_artifacts_secret_shape_findings(tmp_path)

    assert findings == ["specs/001-instruction-tree-tool-documentation/spec.md"]
    assert "supersecretvalue" not in str(findings)


def test_instruction_tree_required_files_and_root_links() -> None:
    required = (
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
    )
    missing = [path for path in required if not (REPO / path).is_file()]
    assert missing == []

    root_text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    for link in (
        "docs/INSTRUCTION_TREE.md",
        "docs/AGENTS.md",
        "docs/agents/AGENTS.md",
        "docs/tools/INDEX.md",
        "tools/AGENTS.md",
        "src/obslayer/AGENTS.md",
        "tests/AGENTS.md",
        ".specify/memory/constitution.md",
        "docs/RUNTIME_STATUS.md",
    ):
        assert link in root_text
    assert "must not weaken" in root_text

    readme_text = (REPO / "README.md").read_text(encoding="utf-8")
    for link in ("docs/INSTRUCTION_TREE.md", "docs/tools/INDEX.md", ".specify/feature.json"):
        assert link in readme_text

    security_text = (REPO / "SECURITY.md").read_text(encoding="utf-8")
    for link in ("AGENTS.md", "docs/INSTRUCTION_TREE.md", "src/obslayer/AGENTS.md"):
        assert link in security_text


def test_instruction_navigation_is_at_most_three_links() -> None:
    text = (REPO / "docs/INSTRUCTION_TREE.md").read_text(encoding="utf-8")
    root_text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    table = text.split("<!-- navigation-table:start -->", 1)[1].split(
        "<!-- navigation-table:end -->", 1
    )[0]
    declared_counts: dict[str, int] = {}
    actual_counts: dict[str, int] = {}
    for line in table.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        area, nearest, follow_up = cells[:3]
        declared_counts[area] = int(cells[-1])
        for path in (nearest, follow_up):
            assert (REPO / path).exists(), path

        nearest_distance = 0 if nearest == "AGENTS.md" else 1 if nearest in root_text else 2
        assert nearest == "AGENTS.md" or nearest in root_text or nearest in text
        nearest_text = (REPO / nearest).read_text(encoding="utf-8")
        if follow_up in root_text:
            follow_up_distance = 1
        elif follow_up in nearest_text:
            follow_up_distance = nearest_distance + 1
        else:
            assert follow_up in text
            follow_up_distance = 2
        actual_counts[area] = max(nearest_distance, follow_up_distance)

    expected_areas = {"/", "docs/", "docs/agents/", "tools/", "src/obslayer/", "tests/"}
    assert set(declared_counts) == expected_areas
    assert set(actual_counts) == expected_areas
    assert max(actual_counts.values()) <= 3
    assert all(actual_counts[area] <= declared_counts[area] for area in expected_areas)


def test_tool_registry_covers_tracked_tools_exactly_once() -> None:
    entries = parse_tool_registry(REPO / "docs/tools/INDEX.md")
    documented = [entry.tool for entry in entries]
    tracked = tracked_tool_paths(REPO)

    assert len(tracked) == 58
    assert len(documented) == len(set(documented))
    assert set(documented) == tracked


def test_tool_set_uses_git_index_with_fixture_fallback(tmp_path: Path) -> None:
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "present.py").write_text("\n", encoding="utf-8")
    assert tracked_tool_paths(tmp_path) == {"tools/present.py"}

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tools / "tracked.py").write_text("\n", encoding="utf-8")
    (tools / "untracked.py").write_text("\n", encoding="utf-8")
    subprocess.run(["git", "add", "tools/present.py", "tools/tracked.py"], cwd=tmp_path, check=True)

    assert tracked_tool_paths(tmp_path) == {"tools/present.py", "tools/tracked.py"}


def test_internal_support_modules_are_not_cli() -> None:
    entries = {entry.tool: entry for entry in parse_tool_registry(REPO / "docs/tools/INDEX.md")}

    for tool in ("tools/_bootstrap.py", "tools/common.py"):
        assert entries[tool].kind == "internal"
        assert entries[tool].family == "internal-support"
        assert entries[tool].status == "internal"
        assert entries[tool].test.startswith("covered-by:")


def test_agent_contracts_include_documentation_duty_and_runtime_source() -> None:
    required_sections = (
        "## Назначение",
        "## Разрешённые действия",
        "## Запрещённые действия",
        "## Входы",
        "## Выходы",
        "## Граница записи",
        "## Передача",
        "## Доказательства",
        "## Влияние на документацию",
        "## Runtime source",
    )
    volatile_ids = ("212b7e8f3c21", "d2a5fd33b29f", "835d51562f73")

    for role in ("HERMES", "CODEX", "NANOBOT"):
        text = (REPO / "docs" / "agents" / f"{role}.md").read_text(encoding="utf-8")
        assert all(section in text for section in required_sections), role
        assert "docs/RUNTIME_STATUS.md" in text
        assert "documentation impact" in text
        assert not any(job_id in text for job_id in volatile_ids)


def test_nanobot_contract_is_project_wide_readonly_observer() -> None:
    text = (REPO / "docs" / "agents" / "NANOBOT.md").read_text(encoding="utf-8")
    observation_areas = (
        "repository-structure",
        "instruction-hierarchy",
        "tool-coverage",
        "test-health",
        "runtime-evidence",
        "open-plans",
        "documentation-drift",
    )

    assert all(f"`{area}`" in text for area in observation_areas)
    for marker in ("read-only", "proposal-only", "no scheduler activation", "handoff target"):
        assert marker in text
