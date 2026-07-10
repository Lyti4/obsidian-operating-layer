import subprocess
from pathlib import Path

from obslayer.project_docs_lag_audit import (
    parse_tool_registry,
    project_docs_lag_audit_to_markdown,
    run_project_docs_lag_audit,
    tracked_tool_paths,
)

REPO = Path(__file__).resolve().parents[1]


def _write_minimal_docs(repo: Path, *, include_marker: bool = True) -> None:
    docs = {
        "docs/spec-kit/26-nanobot-standing-worker.md": "every 15m\n212b7e8f3c21\nproject-state.json\n",
        "docs/spec-kit/24-orchestration-backlog.md": "Nanobot 15-minute audit loop\nevery 15m\nproject-state.json\n",
        "docs/spec-kit/29-semantic-proposal-workflow.md": (
            "tools/obsidian_semantic_review_index.py\nout/proposals/semantic-review-indexes/\nReview index step\n"
            "Semantic/indexing manifest step\ntools/obsidian_semantic_manifest.py\nout/reports/semantic-manifests/\n"
        ),
        "docs/acceptance/index.md": (
            "Semantic targeted proposal/review index\ntools/obsidian_semantic_review_index.py\n"
            "Semantic indexing manifest\ntools/obsidian_semantic_manifest.py\nno live mutation authorization\n"
            "Agentic OS control plane map\ndocs/spec-kit/35-agentic-os-control-plane-map.md\n"
            "docs/spec-kit/36-current-evidence-index.md\ndoes not authorize live mutation\n"
        ),
        "docs/spec-kit/28-global-headroom-only-llm-channel.md": (
            "docs/spec-kit/schemas/llm-channel.schema.json\nmake llm-channel-smoke\nmake llm-channel-smoke-live\n"
        ),
        "docs/spec-kit/35-agentic-os-control-plane-map.md": (
            "Control-plane surfaces\nQueue state model\nAcceptance gates\nCurrent Nanobot synthesis\n"
        ),
        "docs/spec-kit/36-current-evidence-index.md": (
            "Control-plane source surfaces\nCurrent generated evidence pointers\nSafety boundary\n"
        ),
        "AGENTS.md": "15 minutes\n212b7e8f3c21\nbounded read-only/proposal-only\n",
        "docs/AGENTS.md": "documentation scope\n",
        "docs/agents/AGENTS.md": "agent contract scope\n",
        "tools/AGENTS.md": "tool scope\n",
        "src/obslayer/AGENTS.md": "safety core scope\n",
        "tests/AGENTS.md": "test scope\n",
        "docs/INSTRUCTION_TREE.md": "instruction tree\n",
        "docs/tools/INDEX.md": (
            "| tool | purpose | kind | family | mode | write_surface | inputs | outputs | test | instruction | spec | status |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| `tools/example.py` | fixture | cli | reports-evidence | read-only | none | args | stdout | "
            "`tests/test_project_docs_lag_audit.py` | `docs/AGENTS.md` | none | active |\n"
        ),
        "tools/example.py": "raise SystemExit(0)\n",
    }
    if not include_marker:
        docs["AGENTS.md"] = "212b7e8f3c21\nbounded read-only/proposal-only\n"
    for rel, text in docs.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_project_docs_lag_audit_ok(tmp_path: Path) -> None:
    _write_minimal_docs(tmp_path)

    audit = run_project_docs_lag_audit(tmp_path, generated_utc="2026-07-04T00:00:00Z")
    text = project_docs_lag_audit_to_markdown(audit)

    assert audit.status == "ok"
    assert all(check.status == "ok" for check in audit.checks)
    assert "Status: `ok`" in text
    assert "- none" in text


def test_project_docs_lag_audit_flags_missing_marker(tmp_path: Path) -> None:
    _write_minimal_docs(tmp_path, include_marker=False)

    audit = run_project_docs_lag_audit(tmp_path)

    assert audit.status == "lagging"
    assert any("operator_policy_mentions_15m_audit" in finding for finding in audit.findings)
    assert any("15 minutes" in check.missing_markers for check in audit.checks)


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
