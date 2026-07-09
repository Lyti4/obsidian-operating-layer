# Hermes Native Memory First Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing read-only Obsidian memory bridge reproducible, tested, and truthfully documented without changing the live vault, Hermes service, or scheduled jobs.

**Architecture:** Keep this slice repo-only. The bridge remains a small standard-library CLI over Markdown files; it gains a symlink-escape guard and automated tests. Graphify test outputs are isolated by deleting only test-owned derived roots, and runtime docs record the currently paused scheduler state.

**Tech Stack:** Python 3.11 standard library, pytest, Ruff, Markdown.

---

### Task 1: Add failing memory bridge tests

**Files:**
- Create: `tests/test_hermes_obslayer_memory.py`
- Create later: `tools/hermes_obslayer_memory.py`

- [x] **Step 1: Write the CLI and safety tests**

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "hermes_obslayer_memory.py"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_memory_bridge_returns_ranked_relative_json_hits(tmp_path: Path) -> None:
    (tmp_path / "Projects").mkdir()
    (tmp_path / "Projects" / "Hermes Memory.md").write_text(
        "Obsidian Operating Layer stores durable Hermes decisions.\n",
        encoding="utf-8",
    )
    completed = run_tool("Hermes decisions", "--vault", str(tmp_path), "--json")
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["hits"][0]["path"] == "Projects/Hermes Memory.md"


def test_memory_bridge_refuses_symlink_escape(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("private external marker\n", encoding="utf-8")
    (vault / "linked.md").symlink_to(outside)
    completed = run_tool("external marker", "--vault", str(vault), "--json")
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["hits"] == []
```

- [x] **Step 2: Run tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_hermes_obslayer_memory.py -q
```

Expected: failure because the tracked tool is absent in a clean checkout; after the existing script is added unchanged, the symlink-escape test must still fail.

### Task 2: Add and harden the lexical memory bridge

**Files:**
- Create: `tools/hermes_obslayer_memory.py`
- Test: `tests/test_hermes_obslayer_memory.py`

- [x] **Step 1: Add the existing standard-library CLI**

Create the tracked file with this implementation (the symlink boundary from Step 2 is included so the final planned state is explicit):

```python
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
        matched = [term for term in terms if term in lowered or term in title or term in path_lowered]
        if not matched:
            continue
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
        print(
            json.dumps(
                {
                    "vault": str(Path(args.vault).expanduser()),
                    "query": query,
                    "count": len(hits),
                    "hits": [asdict(hit) for hit in hits],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for hit in hits:
            print(f"{hit.score:>4}  {hit.path}\n      {hit.snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 2: Add the minimal symlink boundary**

Inside `_iter_notes`, resolve each candidate and skip it unless the resolved path remains under the resolved vault root:

```python
resolved = p.resolve()
try:
    resolved.relative_to(vault)
except ValueError:
    continue
```

Read from `resolved`, but keep the reported path relative to the logical vault root.

- [x] **Step 3: Run tests and verify GREEN**

Run:

```bash
python3 -m pytest tests/test_hermes_obslayer_memory.py -q
python3 tools/hermes_obslayer_memory.py --self-test
```

Expected: all tests pass and self-test prints `self-test: ok`.

### Task 3: Isolate Graphify incremental test outputs

**Files:**
- Modify: `tests/test_graphify_incremental_index.py`

- [x] **Step 1: Reproduce the stale-derived-root failure**

Run the bounded smoke/query test against the existing stale repo-local test root and confirm that `embedding_run_json` can become `None` when a previous test run left valid embedding sidecars.

- [x] **Step 2: Delete only test-owned derived roots before each test**

Add a helper:

```python
def clean_test_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    return path
```

Use it when constructing `dry-derived-*`, `run-derived-*`, and `bad-derived-*` roots. Do not change production incremental behavior because preserved derived embeddings are correct outside tests.

- [x] **Step 3: Verify the regression twice**

Run:

```bash
python3 -m pytest tests/test_graphify_incremental_index.py -q
python3 -m pytest tests/test_graphify_incremental_index.py -q
```

Expected: both consecutive runs pass.

### Task 4: Record the real runtime state and audit

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `docs/RUNTIME_STATUS.md`
- Create: `docs/audits/hermes-native-memory-audit-2026-07-10.md`

- [x] **Step 1: Correct scheduler wording**

Use this status sentence in `AGENTS.md` and the equivalent expanded table in `docs/RUNTIME_STATUS.md`:

```text
Current verified state (2026-07-10): the approved Nanobot scout/reviewer/deep-review definitions still exist, but jobs 212b7e8f3c21, d2a5fd33b29f, and 835d51562f73 are paused. Verify with `hermes cron list --all`; this repo-only slice does not resume them.
```

- [x] **Step 2: Document the bridge boundary**

Add this exact boundary under the README project layout and runtime status:

```text
`tools/hermes_obslayer_memory.py` is a tracked read-only lexical fallback over Markdown notes. It is not yet an active Hermes MemoryProvider, automatic capture path, or semantic indexer; those remain later separately accepted slices.
```

- [x] **Step 3: Save the structured audit**

Create `docs/audits/hermes-native-memory-audit-2026-07-10.md` with these exact top-level sections and no secret values or raw note bodies:

```markdown
# Аудит нативной памяти Hermes через Obsidian
## Краткий вердикт
## Кто
## Зачем
## Почему
## Что уже работает
## Что пока не работает
## Что делаем
## Границы
## Проверка
## Следующий шаг
## Термины
```

The facts must include: built-in Hermes memory is enabled; `codebase-memory-mcp` indexes this repository rather than the vault; Ollama `bge-m3`, local `faster-whisper`, and `ffmpeg` are present; automatic capture and an active Obslayer MemoryProvider are absent; three Obsidian scheduler jobs are paused; and the accepted next order is repo hygiene, local STT, read-only provider, sandbox inbox, approved append-only inbox, then incremental semantic indexing.

### Task 5: Validate the complete slice

**Files:**
- All files above.

- [x] **Step 1: Run narrow checks**

```bash
python3 -m pytest tests/test_hermes_obslayer_memory.py tests/test_graphify_incremental_index.py -q
git diff --check
```

- [x] **Step 2: Run project verification**

```bash
. .venv/bin/activate
make verify
```

Expected: pytest, Ruff, and compileall pass. If any check fails, inspect and fix the failure before reporting.

- [x] **Step 3: Inspect scope**

```bash
git status --short
git diff --stat
git diff -- AGENTS.md README.md docs/RUNTIME_STATUS.md docs/audits/hermes-native-memory-audit-2026-07-10.md docs/spec-kit/51-hermes-native-memory-first-slice.md tests/test_graphify_incremental_index.py tests/test_hermes_obslayer_memory.py tools/hermes_obslayer_memory.py
```

Expected: only the approved repo-only files changed; no `out/`, vault, service, auth, cron, or secret-bearing files are tracked.

- [x] **Step 4: Commit only after separate approval**

Do not commit or push in this slice unless Dmitry separately authorizes it. A future approved command would stage explicit paths only, never `git add .`.
