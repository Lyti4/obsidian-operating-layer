from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from obslayer import GuardrailError, build_diagram_pdf_report_evaluation, load_diagram_renderer_record


def adapter_record() -> Path:
    repo = Path(__file__).resolve().parents[1]
    return repo / "docs" / "spec-kit" / "research" / "sample-adapter-records" / "diagram-renderer-mermaid-cli.json"


def make_project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    diagrams = root / "docs" / "diagrams"
    diagrams.mkdir(parents=True)
    (diagrams / "architecture.mmd").write_text("flowchart TB\n  A[Human] --> B[Safety core]\n", encoding="utf-8")
    (diagrams / "worker-flow.mmd").write_text("flowchart LR\n  A[Code] --> B[Verify]\n", encoding="utf-8")
    (diagrams / "safety-sequence.mmd").write_text(
        "sequenceDiagram\n  participant Worker\n  participant Vault\n  Worker->>Vault: approved apply only\n",
        encoding="utf-8",
    )
    return root


def test_load_diagram_renderer_record_enforces_render_only_contract() -> None:
    record = load_diagram_renderer_record(adapter_record())

    assert record["kind"] == "diagram-renderer"
    assert record["direct_write_enabled"] is False
    assert record["sandbox_required"] is True
    assert record["capabilities"] == ["read", "render"]
    assert "write-direct" in record["forbidden_capabilities"]


def test_load_diagram_renderer_record_rejects_live_write(tmp_path: Path) -> None:
    bad = json.loads(adapter_record().read_text(encoding="utf-8"))
    bad["direct_write_enabled"] = True
    bad_path = tmp_path / "bad-diagram.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")

    with pytest.raises(GuardrailError):
        load_diagram_renderer_record(bad_path)


def test_build_diagram_pdf_report_evaluation_writes_safe_artifacts(tmp_path: Path) -> None:
    project_root = make_project_root(tmp_path)
    evaluation = build_diagram_pdf_report_evaluation(adapter_record=adapter_record(), project_root=project_root)

    assert evaluation.adapter == "mermaid-cli"
    assert evaluation.direct_write_disabled is True
    assert evaluation.verification["pdf_generated"] is True
    assert evaluation.verification["all_svg_outputs_exist"] is True
    assert evaluation.verification["no_live_vault_write"] is True
    assert len(evaluation.diagram_outputs) == 3
    assert Path(evaluation.report_pdf).read_bytes().startswith(b"%PDF-")
    assert Path(evaluation.report_markdown).is_file()
    assert Path(evaluation.artifacts["json_report"]).is_file()
    assert str(project_root / "out" / "reports") in evaluation.report_pdf


def test_build_diagram_pdf_report_rejects_outputs_outside_out_reports(tmp_path: Path) -> None:
    project_root = make_project_root(tmp_path)

    with pytest.raises(GuardrailError):
        build_diagram_pdf_report_evaluation(
            adapter_record=adapter_record(),
            project_root=project_root,
            report_out_dir=tmp_path / "reports-outside-project",
        )


def test_diagram_pdf_report_cli_writes_json_markdown_pdf_and_svg(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    project_root = make_project_root(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "obsidian_diagram_pdf_report.py"),
            "--adapter-record",
            str(adapter_record()),
            "--project-root",
            str(project_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["pdf_generated"] is True
    assert payload["direct_write_disabled"] is True
    assert payload["no_live_vault_write"] is True
    assert Path(payload["json_report"]).is_file()
    assert Path(payload["markdown_report"]).is_file()
    assert Path(payload["pdf_report"]).read_bytes().startswith(b"%PDF-")
    assert len(payload["diagram_outputs"]) == 3
    assert all(Path(path).is_file() for path in payload["diagram_outputs"].values())
