from __future__ import annotations

import json
import re
import shutil
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

LINK_PATTERN = re.compile(r"(?<!\\)\[\[([^\]\|#]+)(?:#[^\]]+)?(?:\|[^\]]+)?\]\]")
IGNORED_DIR_NAMES = {
    ".git",
    ".obsidian",
    ".trash",
    "_Archive",
    "_Backups",
    "node_modules",
    "__pycache__",
}


def _is_ignored_path(path: Path) -> bool:
    return any(part in IGNORED_DIR_NAMES or part.startswith(".") for part in path.parts)


class ApplyError(RuntimeError):
    """Raised when an apply request fails safety checks."""


@dataclass(frozen=True)
class NoteRecord:
    path: str
    title: str
    outgoing_links: list[str]
    resolved_links: list[str]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_path(path: Path) -> Path:
    return path.expanduser().resolve()


def _iter_markdown_files(vault_root: Path) -> Iterable[Path]:
    vault_root = _norm_path(vault_root)
    for path in sorted(vault_root.rglob("*.md")):
        if _is_ignored_path(path.relative_to(vault_root)):
            continue
        if path.is_file():
            yield path


def _mask_code_spans_and_fences(text: str) -> str:
    """Replace Markdown code spans/fences with spaces so examples are not active links."""

    masked_lines: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            masked_lines.append(" " * len(line))
            continue
        if in_fence:
            masked_lines.append(" " * len(line))
            continue

        chars = list(line)
        in_code = False
        i = 0
        while i < len(chars):
            if chars[i] == "`":
                in_code = not in_code
                chars[i] = " "
            elif in_code:
                chars[i] = " "
            i += 1
        masked_lines.append("".join(chars))
    return "".join(masked_lines)


def _extract_links(text: str) -> list[str]:
    text = _mask_code_spans_and_fences(text)
    links: list[str] = []
    for match in LINK_PATTERN.finditer(text):
        target = match.group(1).strip()
        if target:
            links.append(target)
    return links


def _candidate_targets(link: str, current_file: Path, vault_root: Path) -> list[Path]:
    raw = link.strip()
    if not raw:
        return []

    vault_root = _norm_path(vault_root)
    current_file = _norm_path(current_file)
    candidates: list[Path] = []
    raw_path = Path(raw)

    def add_candidate(candidate: Path) -> None:
        candidate = candidate.expanduser()
        if candidate.suffix.lower() != ".md":
            candidate = candidate.with_suffix(".md")
        try:
            resolved = candidate.resolve()
        except FileNotFoundError:
            resolved = candidate.absolute()
        if resolved not in candidates:
            candidates.append(resolved)

    if raw_path.is_absolute():
        add_candidate(raw_path)
    else:
        add_candidate(vault_root / raw_path)
        add_candidate(current_file.parent / raw_path)
        add_candidate(vault_root / raw_path.name)
        add_candidate(vault_root / raw_path.with_suffix(".md"))

    stem = raw_path.stem if raw_path.suffix else raw_path.name
    for file_path in _iter_markdown_files(vault_root):
        if file_path.stem == stem:
            add_candidate(file_path)
    return candidates


def observe_vault(vault_root: str | Path) -> dict[str, Any]:
    vault_root = _norm_path(Path(vault_root))
    if not vault_root.exists():
        raise FileNotFoundError(f"Vault root does not exist: {vault_root}")
    if not vault_root.is_dir():
        raise NotADirectoryError(f"Vault root is not a directory: {vault_root}")

    note_records: list[NoteRecord] = []
    outgoing_by_note: dict[str, list[str]] = {}
    link_targets_by_note: dict[str, list[str]] = {}
    incoming_counts: defaultdict[str, int] = defaultdict(int)
    broken_links: list[dict[str, Any]] = []

    for file_path in _iter_markdown_files(vault_root):
        text = file_path.read_text(encoding="utf-8")
        outgoing = _extract_links(text)
        resolved: list[str] = []
        for link in outgoing:
            candidates = _candidate_targets(link, file_path, vault_root)
            resolved_path = next((candidate for candidate in candidates if candidate.exists()), None)
            if resolved_path is None:
                broken_links.append(
                    {
                        "source": str(file_path),
                        "target": link,
                        "status": "broken",
                    }
                )
            else:
                resolved_str = str(resolved_path)
                resolved.append(resolved_str)
                incoming_counts[resolved_str] += 1
        outgoing_by_note[str(file_path)] = outgoing
        link_targets_by_note[str(file_path)] = resolved
        note_records.append(
            NoteRecord(
                path=str(file_path),
                title=file_path.stem,
                outgoing_links=outgoing,
                resolved_links=resolved,
            )
        )

    notes = [record.__dict__ for record in note_records]
    orphans = [note["path"] for note in notes if not note["outgoing_links"] and incoming_counts[note["path"]] == 0]

    duplicates: list[dict[str, Any]] = []
    stems: defaultdict[str, list[str]] = defaultdict(list)
    for note in notes:
        stems[Path(note["path"]).stem].append(note["path"])
    for stem, paths in sorted(stems.items()):
        if len(paths) > 1:
            duplicates.append({"stem": stem, "paths": paths})

    observation = {
        "vault_root": str(vault_root),
        "created_at": _utcnow(),
        "counts": {
            "notes": len(notes),
            "broken_links": len(broken_links),
            "orphans": len(orphans),
            "duplicates": len(duplicates),
        },
        "notes": notes,
        "broken_links": broken_links,
        "orphans": orphans,
        "duplicates": duplicates,
    }
    return observation


def build_proposal(
    observation: dict[str, Any],
    *,
    label: str | None = None,
    actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    actions = list(actions or [])
    source_counts = dict(observation.get("counts", {}))
    proposal = {
        "proposal_id": f"proposal-{uuid.uuid4().hex[:12]}",
        "created_at": _utcnow(),
        "label": label or "obsidian-operating-layer proposal",
        "dry_run": True,
        "target_vault": observation.get("vault_root"),
        "source_counts": source_counts,
        "risk_class": "read-only-first",
        "requires_approval_manifest": True,
        "actions": actions,
        "summary": {
            "notes": source_counts.get("notes", 0),
            "broken_links": source_counts.get("broken_links", 0),
            "orphans": source_counts.get("orphans", 0),
            "duplicates": source_counts.get("duplicates", 0),
        },
        "recommendation": "Dry-run only until an explicit approval manifest is supplied.",
    }
    return proposal


def _load_json_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _default_backup_dir(proposal_id: str) -> Path:
    return Path.cwd() / "obslayer-backups" / proposal_id


def apply_proposal(
    proposal: dict[str, Any],
    *,
    dry_run: bool = True,
    approval_manifest: str | Path | None = None,
    backup_dir: str | Path | None = None,
) -> dict[str, Any]:
    if dry_run or proposal.get("dry_run", True):
        return {
            "proposal_id": proposal.get("proposal_id"),
            "dry_run": True,
            "applied_actions": 0,
            "backups": [],
            "message": "Dry-run mode: no files changed.",
        }

    if approval_manifest is None:
        raise ApplyError("Real apply requires an explicit approval manifest.")

    manifest = _load_json_file(approval_manifest)
    if not manifest.get("approved"):
        raise ApplyError("Approval manifest is not approved.")
    if manifest.get("proposal_id") != proposal.get("proposal_id"):
        raise ApplyError("Approval manifest does not match the proposal id.")
    if manifest.get("target_vault") != proposal.get("target_vault"):
        raise ApplyError("Approval manifest does not match the target vault.")

    target_root = _norm_path(Path(proposal["target_vault"]))
    if backup_dir is None:
        backup_root = _default_backup_dir(proposal.get("proposal_id", "proposal"))
    else:
        backup_root = Path(backup_dir)
    backup_root.mkdir(parents=True, exist_ok=True)

    backups: list[str] = []
    applied_actions = 0
    for action in proposal.get("actions", []):
        kind = action.get("kind")
        if kind != "write_text":
            raise ApplyError(f"Unsupported action kind: {kind}")

        target_path = _norm_path(Path(action["path"]))
        if not _safe_within_root(target_path, target_root):
            raise ApplyError(f"Action escapes target vault: {target_path}")

        if target_path.exists():
            backup_path = backup_root / target_path.relative_to(target_root)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_path, backup_path)
            backups.append(str(backup_path))

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(action.get("content", ""), encoding="utf-8")
        applied_actions += 1

    return {
        "proposal_id": proposal.get("proposal_id"),
        "dry_run": False,
        "applied_actions": applied_actions,
        "backups": backups,
        "message": "Apply completed.",
    }


def verify_proposal(observation: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if observation.get("vault_root") != proposal.get("target_vault"):
        issues.append("Observation vault root does not match proposal target vault.")
    if observation.get("counts") != proposal.get("source_counts"):
        issues.append("Observation counts do not match proposal source counts.")
    if proposal.get("dry_run") is not True and not proposal.get("actions"):
        issues.append("Non-dry-run proposal has no actions.")

    return {
        "proposal_id": proposal.get("proposal_id"),
        "passed": not issues,
        "issues": issues,
        "checked_counts": observation.get("counts", {}),
    }


def format_observation_markdown(observation: dict[str, Any]) -> str:
    counts = observation.get("counts", {})
    lines = [
        "# Obsidian observation",
        "",
        f"- Vault: `{observation.get('vault_root')}`",
        f"- Created: `{observation.get('created_at', '')}`",
        "",
        "## Counts",
        f"- Notes: {counts.get('notes', 0)}",
        f"- Broken links: {counts.get('broken_links', 0)}",
        f"- Orphans: {counts.get('orphans', 0)}",
        f"- Duplicates: {counts.get('duplicates', 0)}",
    ]
    if observation.get("broken_links"):
        lines.extend(["", "## Broken links"])
        for item in observation["broken_links"][:20]:
            lines.append(f"- {item['source']} -> {item['target']}")
    if observation.get("orphans"):
        lines.extend(["", "## Orphans"])
        for path in observation["orphans"][:20]:
            lines.append(f"- {path}")
    return "\n".join(lines) + "\n"


def format_proposal_markdown(proposal: dict[str, Any]) -> str:
    summary = proposal.get("summary", {})
    lines = [
        "# Obsidian proposal",
        "",
        f"- Proposal id: `{proposal.get('proposal_id')}`",
        f"- Label: {proposal.get('label')}",
        f"- Target vault: `{proposal.get('target_vault')}`",
        f"- Dry run: `{proposal.get('dry_run')}`",
        "",
        "## Source counts",
        f"- Notes: {summary.get('notes', 0)}",
        f"- Broken links: {summary.get('broken_links', 0)}",
        f"- Orphans: {summary.get('orphans', 0)}",
        f"- Duplicates: {summary.get('duplicates', 0)}",
        "",
        "## Safety",
        f"- Requires approval manifest: `{proposal.get('requires_approval_manifest')}`",
        f"- Risk class: {proposal.get('risk_class')}",
    ]
    return "\n".join(lines) + "\n"


def format_verification_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Obsidian verification",
        "",
        f"- Proposal id: `{result.get('proposal_id')}`",
        f"- Passed: `{result.get('passed')}`",
        "",
        "## Issues",
    ]
    issues = result.get("issues", [])
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"
