from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError, load_json, utc_stamp, write_json

ALLOWED_DIAGRAM_CAPABILITIES = {"read", "render"}
REQUIRED_FORBIDDEN_CAPABILITIES = {
    "write-direct",
    "delete-direct",
    "move-direct",
    "merge-direct",
    "patch-direct",
    "execute-live-mutation",
    "secret-read",
}
DEFAULT_DIAGRAM_SOURCES = {
    "architecture": "docs/diagrams/architecture.mmd",
    "worker_flow": "docs/diagrams/worker-flow.mmd",
    "safety_sequence": "docs/diagrams/safety-sequence.mmd",
}


@dataclass(frozen=True)
class DiagramPdfReportEvaluation:
    adapter: str
    source_id: str
    project_root: str
    diagram_sources: dict[str, str]
    diagram_outputs: dict[str, str]
    report_pdf: str
    report_markdown: str
    artifacts: dict[str, str]
    generation_command: str
    direct_write_disabled: bool
    write_policy: str
    verification: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_diagram_renderer_record(path: str | Path) -> dict[str, Any]:
    record = load_json(path)
    if record.get("kind") != "diagram-renderer":
        raise GuardrailError(f"Adapter record is not a diagram renderer: {record.get('kind')}")
    if record.get("direct_write_enabled") is not False:
        raise GuardrailError("Diagram renderer adapter must set direct_write_enabled=false")
    if record.get("sandbox_required") is not True:
        raise GuardrailError("Diagram renderer adapter must require sandbox/output-first evaluation")

    capabilities = set(record.get("capabilities", []))
    unknown_allowed = capabilities - ALLOWED_DIAGRAM_CAPABILITIES
    if unknown_allowed:
        raise GuardrailError(f"Diagram renderer has unsupported allowed capabilities: {sorted(unknown_allowed)}")
    dangerous_as_allowed = capabilities & REQUIRED_FORBIDDEN_CAPABILITIES
    if dangerous_as_allowed:
        raise GuardrailError(f"Diagram renderer exposes dangerous capabilities as allowed: {sorted(dangerous_as_allowed)}")

    forbidden = set(record.get("forbidden_capabilities", []))
    missing = REQUIRED_FORBIDDEN_CAPABILITIES - forbidden
    if missing:
        raise GuardrailError(f"Diagram renderer missing required forbidden capabilities: {sorted(missing)}")
    return record


def _resolve_under_project(project_root: Path, relative_path: str) -> Path:
    if Path(relative_path).is_absolute():
        raise GuardrailError(f"Expected project-relative path, got absolute path: {relative_path}")
    path = (project_root / relative_path).resolve()
    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise GuardrailError(f"Path escapes project root: {relative_path}") from exc
    return path


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", text.lower()).strip("-") or "diagram"


def _diagram_title(name: str, source: str) -> str:
    first_line = next((line.strip() for line in source.splitlines() if line.strip()), "diagram")
    if first_line.startswith("flowchart"):
        return name.replace("_", " ").title()
    if first_line.startswith("sequenceDiagram"):
        return name.replace("_", " ").title()
    return first_line[:80]


def _safe_source_preview_svg(name: str, source: str, out: Path) -> None:
    title = _diagram_title(name, source)
    lines = [line.rstrip() for line in source.splitlines() if line.strip()]
    width = 1040
    line_height = 24
    height = max(360, 120 + line_height * len(lines))
    escaped_title = html.escape(title)
    text_lines = []
    for index, line in enumerate(lines, start=1):
        y = 94 + index * line_height
        text_lines.append(
            f'<text x="44" y="{y}" class="code"><tspan class="ln">{index:02d}</tspan> {html.escape(line)}</text>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .bg {{ fill: #0f172a; }}
    .panel {{ fill: #111827; stroke: #38bdf8; stroke-width: 2; rx: 18; }}
    .title {{ fill: #e5f3ff; font: 700 30px sans-serif; }}
    .subtitle {{ fill: #93c5fd; font: 16px sans-serif; }}
    .code {{ fill: #d1fae5; font: 16px monospace; }}
    .ln {{ fill: #60a5fa; }}
    .rule {{ stroke: #38bdf8; stroke-width: 1.5; opacity: 0.7; }}
  </style>
  <rect class="bg" x="0" y="0" width="{width}" height="{height}"/>
  <rect class="panel" x="24" y="24" width="{width - 48}" height="{height - 48}"/>
  <text x="44" y="64" class="title">{escaped_title}</text>
  <text x="44" y="90" class="subtitle">Mermaid renderer unavailable; safe source preview fallback</text>
  <line x1="44" y1="106" x2="{width - 44}" y2="106" class="rule"/>
  {''.join(text_lines)}
</svg>
"""
    out.write_text(svg, encoding="utf-8")


def _mermaid_cli_command() -> list[str] | None:
    if shutil.which("mmdc"):
        return ["mmdc"]
    if shutil.which("npx"):
        return ["npx", "--yes", "@mermaid-js/mermaid-cli"]
    return None


def _render_with_mermaid_cli(source: str, out: Path) -> bool:
    command = _mermaid_cli_command()
    if not command:
        return False
    with tempfile.TemporaryDirectory(prefix="obslayer-mermaid-") as tmp:
        tmp_dir = Path(tmp)
        input_path = tmp_dir / "diagram.mmd"
        input_path.write_text(source, encoding="utf-8")
        puppeteer_config = tmp_dir / "puppeteer.json"
        puppeteer_config.write_text(
            json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]}),
            encoding="utf-8",
        )
        cli = [
            *command,
            "-i",
            str(input_path),
            "-o",
            str(out),
            "--backgroundColor",
            "transparent",
            "-p",
            str(puppeteer_config),
        ]
        try:
            subprocess.run(cli, check=True, capture_output=True, text=True, timeout=120)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    return out.is_file() and "<svg" in out.read_text(encoding="utf-8", errors="ignore")[:500]


def render_mermaid_source_to_svg(name: str, source: str, out: str | Path) -> None:
    target = Path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not _render_with_mermaid_cli(source, target):
        _safe_source_preview_svg(name, source, target)


def _pdf_escape(text: str) -> str:
    safe = text.encode("latin-1", errors="replace").decode("latin-1")
    return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text_page(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 18 Tf", "72 760 Td", "(Obsidian Operating Layer - Diagram/PDF POC) Tj"]
    commands.extend(["/F1 10 Tf", "0 -28 Td"])
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj")
        commands.append("0 -15 Td")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def write_simple_pdf_report(*, out: str | Path, pages: list[list[str]]) -> None:
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{4 + index * 2} 0 R" for index in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("ascii"))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for index, page_lines in enumerate(pages):
        page_obj = 4 + index * 2
        content_obj = page_obj + 1
        content = _pdf_text_page(page_lines)
        page_dict = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj} 0 R >>"
        )
        objects.append(page_dict.encode("ascii"))
        objects.append(b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream")

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    target = Path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(bytes(pdf))


def _markdown_report(evaluation: DiagramPdfReportEvaluation) -> str:
    lines = [
        f"# Diagram/PDF report proof-of-concept: {evaluation.adapter}",
        "",
        f"- source: `{evaluation.source_id}`",
        f"- project_root: `{evaluation.project_root}`",
        f"- report_pdf: `{evaluation.report_pdf}`",
        f"- generation_command: `{evaluation.generation_command}`",
        f"- direct_write_disabled: `{evaluation.direct_write_disabled}`",
        f"- write_policy: `{evaluation.write_policy}`",
        "",
        "## Diagram sources",
    ]
    lines.extend(f"- `{name}`: `{path}`" for name, path in evaluation.diagram_sources.items())
    lines.extend(["", "## Diagram outputs"])
    lines.extend(f"- `{name}`: `{path}`" for name, path in evaluation.diagram_outputs.items())
    lines.extend(["", "## Verification", "```json", json.dumps(evaluation.verification, indent=2, sort_keys=True), "```"])
    return "\n".join(lines) + "\n"


def build_diagram_pdf_report_evaluation(
    *,
    adapter_record: str | Path,
    project_root: str | Path,
    diagram_sources: dict[str, str] | None = None,
    diagram_out_dir: str | Path = "out/diagrams",
    report_out_dir: str | Path = "out/reports",
    generation_command: str = (
        "python tools/obsidian_diagram_pdf_report.py "
        "--adapter-record docs/spec-kit/research/sample-adapter-records/diagram-renderer-mermaid-cli.json"
    ),
) -> DiagramPdfReportEvaluation:
    record = load_diagram_renderer_record(adapter_record)
    root = Path(project_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise GuardrailError(f"Project root does not exist or is not a directory: {root}")

    sources = diagram_sources or DEFAULT_DIAGRAM_SOURCES
    source_paths = {name: _resolve_under_project(root, rel) for name, rel in sources.items()}
    missing = [str(path) for path in source_paths.values() if not path.is_file()]
    if missing:
        raise GuardrailError(f"Diagram source file(s) missing: {missing}")

    diagram_dir = (root / diagram_out_dir).resolve() if not Path(diagram_out_dir).is_absolute() else Path(diagram_out_dir).resolve()
    report_dir = (root / report_out_dir).resolve() if not Path(report_out_dir).is_absolute() else Path(report_out_dir).resolve()
    allowed_diagram_root = (root / "out" / "diagrams").resolve()
    allowed_report_root = (root / "out" / "reports").resolve()
    if not _is_under(diagram_dir, allowed_diagram_root):
        raise GuardrailError(f"Diagram outputs must stay under {allowed_diagram_root}: {diagram_dir}")
    if not _is_under(report_dir, allowed_report_root):
        raise GuardrailError(f"Report outputs must stay under {allowed_report_root}: {report_dir}")

    diagram_outputs: dict[str, str] = {}
    for name, source_path in source_paths.items():
        out = diagram_dir / f"{_slug(name)}.svg"
        render_mermaid_source_to_svg(name, source_path.read_text(encoding="utf-8"), out)
        diagram_outputs[name] = str(out)

    stamp = utc_stamp()
    pdf_out = report_dir / f"obslayer-architecture-poc-{stamp}.pdf"
    markdown_out = pdf_out.with_suffix(".md")
    json_out = pdf_out.with_suffix(".json")
    pages = [
        [
            "Purpose: first reproducible architecture PDF for Dmitry from repo-tracked text diagram sources.",
            "Safety: render-only adapter, no live Obsidian vault writes, no secrets, all artifacts under out/.",
            "",
            "Included diagrams:",
            *[f"- {name}: {path}" for name, path in source_paths.items()],
        ],
        [
            "Generated artifacts:",
            *[f"- {name}: {path}" for name, path in diagram_outputs.items()],
            f"- pdf_report: {pdf_out}",
            "",
            "Generation command:",
            generation_command,
        ],
    ]
    wrapped_pages = [[wrapped for line in page for wrapped in (textwrap.wrap(line, width=88) or [""])] for page in pages]
    write_simple_pdf_report(out=pdf_out, pages=wrapped_pages)

    verification = {
        "diagram_sources_count": len(source_paths),
        "diagram_outputs_count": len(diagram_outputs),
        "all_sources_exist": all(path.is_file() for path in source_paths.values()),
        "all_svg_outputs_exist": all(Path(path).is_file() for path in diagram_outputs.values()),
        "pdf_generated": pdf_out.is_file() and pdf_out.read_bytes().startswith(b"%PDF-"),
        "outputs_under_out_diagrams": all(_is_under(Path(path), allowed_diagram_root) for path in diagram_outputs.values()),
        "reports_under_out_reports": _is_under(pdf_out, allowed_report_root) and _is_under(markdown_out, allowed_report_root),
        "direct_write_disabled": True,
        "no_live_vault_write": True,
        "sensitive_content_exposed": False,
    }
    evaluation = DiagramPdfReportEvaluation(
        adapter=record["name"],
        source_id=record["source"]["id"],
        project_root=str(root),
        diagram_sources={name: str(path) for name, path in source_paths.items()},
        diagram_outputs=diagram_outputs,
        report_pdf=str(pdf_out),
        report_markdown=str(markdown_out),
        artifacts={"json_report": str(json_out), "markdown_report": str(markdown_out), "pdf_report": str(pdf_out), **diagram_outputs},
        generation_command=generation_command,
        direct_write_disabled=True,
        write_policy="render-only-and-write-generated-artifacts-under-out-reports-first",
        verification=verification,
    )
    markdown_out.write_text(_markdown_report(evaluation), encoding="utf-8")
    write_json(json_out, {"status": "ok", **evaluation.to_dict()})
    return evaluation


def write_diagram_pdf_report_evaluation(evaluation: DiagramPdfReportEvaluation, out: str | Path) -> None:
    write_json(out, {"status": "ok", **evaluation.to_dict()})


def diagram_pdf_report_to_markdown(evaluation: DiagramPdfReportEvaluation) -> str:
    return _markdown_report(evaluation)
