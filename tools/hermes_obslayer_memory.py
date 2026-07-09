#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_VAULT = Path("/home/hermesadmin/Obsidian/ParserRIba-AgentOS")
EXCLUDED_DIRS = {".obsidian", ".trash", "_Backups", "_Archive", "__pycache__"}
MAX_FILE_BYTES = 2_000_000


@dataclass(frozen=True)
class Hit:
    path: str
    score: int
    title: str
    snippet: str


def _terms(query: str) -> list[str]:
    return [term.casefold() for term in re.findall(r"\w+", query, flags=re.UNICODE) if len(term) > 1]


def _iter_notes(vault: Path) -> Iterable[tuple[Path, Path]]:
    for path in vault.rglob("*.md"):
        rel_parts = path.relative_to(vault).parts
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        try:
            resolved = path.resolve()
            resolved.relative_to(vault)
            if resolved.is_file() and resolved.stat().st_size <= MAX_FILE_BYTES:
                yield path, resolved
        except (OSError, ValueError):
            continue


def _snippet(text: str, terms: list[str], width: int = 260) -> str:
    lowered = text.casefold()
    positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
    position = min(positions) if positions else 0
    start = max(0, position - width // 3)
    end = min(len(text), start + width)
    return " ".join(text[start:end].split())


def search(vault: Path, query: str, limit: int) -> list[Hit]:
    vault = vault.expanduser().resolve()
    if not vault.exists():
        raise SystemExit(f"vault not found: {vault}")
    terms = _terms(query)
    if not terms:
        raise SystemExit("empty query")
    hits: list[Hit] = []
    for note, resolved_note in _iter_notes(vault):
        try:
            text = resolved_note.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lowered = text.casefold()
        rel_path = note.relative_to(vault).as_posix()
        path_lowered = rel_path.casefold()
        title = note.stem.casefold()
        matched = [
            term
            for term in terms
            if term in lowered or term in title or term in path_lowered
        ]
        if not matched:
            continue
        # ponytail: simple lexical rank; swap to existing embedding run when we need semantic recall.
        score = (
            1000 * len(matched)
            + sum(lowered.count(term) for term in matched)
            + 25 * sum(term in title for term in matched)
            + 100 * sum(term in path_lowered for term in matched)
        )
        if all(term in lowered or term in title or term in path_lowered for term in terms):
            score += 500
        hits.append(Hit(rel_path, score, note.stem, _snippet(text, matched)))
    hits.sort(key=lambda hit: (-hit.score, hit.path.casefold()))
    return hits[:limit]


def self_test() -> None:
    with tempfile.TemporaryDirectory() as directory:
        vault = Path(directory)
        (vault / ".obsidian").mkdir()
        (vault / "Projects").mkdir()
        (vault / "Projects" / "Obsidian Layer.md").write_text(
            "Obsidian Operating Layer indexes ParserRIba memory.",
            encoding="utf-8",
        )
        (vault / "Noise.md").write_text("unrelated", encoding="utf-8")
        hits = search(vault, "ParserRIba memory", 5)
        assert hits and hits[0].path == "Projects/Obsidian Layer.md", hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Hermes read-only memory lookup through the Obsidian Operating Layer vault surface."
    )
    parser.add_argument("query", nargs="*")
    parser.add_argument("--vault", default=str(DEFAULT_VAULT))
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test: ok")
        return 0
    query = " ".join(args.query).strip()
    hits = search(Path(args.vault), query, args.limit)
    if args.json:
        payload = {
            "vault": str(Path(args.vault).expanduser()),
            "query": query,
            "count": len(hits),
            "hits": [asdict(hit) for hit in hits],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for hit in hits:
            print(f"{hit.score:>4}  {hit.path}\n      {hit.snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
