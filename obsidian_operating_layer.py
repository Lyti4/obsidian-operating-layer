from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Observation:
    vault: str
    notes: list[str]
    counts: dict[str, int]


@dataclass
class Proposal:
    vault: str
    dry_run: bool
    changes: list[dict[str, Any]]


def scan_vault(vault: Path) -> Observation:
    md_files = list(vault.rglob("*.md")) if vault.exists() else []
    notes = [str(p.relative_to(vault)) for p in md_files[:20]]
    return Observation(vault=str(vault), notes=notes, counts={"markdown_files": len(md_files)})


def render_report(title: str, payload: dict[str, Any]) -> str:
    return f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```\n"


def write_bundle(out_dir: Path, stem: str, payload: dict[str, Any], title: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_report(title, payload), encoding="utf-8")
    return json_path
