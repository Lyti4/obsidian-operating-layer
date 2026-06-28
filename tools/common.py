from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

PROTECTED_PARTS = {".obsidian", "_Backups", "_Archive", ".trash", "Soul-Vault/Hermes/Soul", "Soul-Vault/Soul"}


def is_protected(path: Path) -> bool:
    p = str(path).replace("\\", "/")
    return any(part in p for part in PROTECTED_PARTS)


def iter_markdown_files(vault: Path) -> Iterable[Path]:
    for path in vault.rglob("*.md"):
        if is_protected(path):
            continue
        yield path


def load_json(path: Path):
    return json.loads(path.read_text())


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
