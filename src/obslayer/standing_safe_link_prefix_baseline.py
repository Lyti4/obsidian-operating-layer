from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from obslayer.standing_safe_link_prefix_policy import classify_link_prefix_candidate, load_standing_safe_link_prefix_policy

MODE = "obslayer.standing-safe-link-prefix-baseline.v1"
LINK_RE = re.compile(r"\[\[Hermes/[^\]|]+(?:\|[^\]]+)?\]\]")


@dataclass(frozen=True)
class StandingSafeLinkPrefixBaseline:
    schema: str
    mode: str
    status: str
    created_at: str
    vault_root: str
    scan_root: str
    source_policy: str
    live_mutation_authorized: bool
    approval_manifest_created: bool
    apply_authority: str
    summary: dict[str, Any]
    allowed_examples: list[dict[str, Any]]
    excluded_examples: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_hidden_or_cache_path(path: Path) -> bool:
    return any(part in {".obsidian", ".trash", ".git", "__pycache__"} for part in path.parts)


def collect_existing_markdown_targets(vault_root: str | Path) -> set[str]:
    root = Path(vault_root).expanduser().resolve()
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.md")
        if path.is_file() and not _is_hidden_or_cache_path(path.relative_to(root))
    }


def iter_standing_link_occurrences(*, vault_root: str | Path, scan_root: str | Path | None = None) -> Iterable[tuple[str, str]]:
    root = Path(vault_root).expanduser().resolve()
    scan = Path(scan_root).expanduser().resolve() if scan_root is not None else root
    try:
        scan.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"scan_root must be inside vault_root: {scan}") from exc

    for path in sorted(scan.rglob("*.md")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if _is_hidden_or_cache_path(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        for link in LINK_RE.findall(text):
            yield rel.as_posix(), link


def build_standing_safe_link_prefix_baseline(
    *,
    vault_root: str | Path,
    scan_root: str | Path | None = None,
    existing_target_relpaths: Iterable[str] | None = None,
    allowed_example_limit: int = 20,
    excluded_example_limit: int = 20,
) -> StandingSafeLinkPrefixBaseline:
    root = Path(vault_root).expanduser().resolve()
    scan = Path(scan_root).expanduser().resolve() if scan_root is not None else root
    policy = load_standing_safe_link_prefix_policy()
    existing = set(existing_target_relpaths) if existing_target_relpaths is not None else collect_existing_markdown_targets(root)

    counts: Counter[str] = Counter()
    allowed_examples: list[dict[str, Any]] = []
    excluded_examples: list[dict[str, Any]] = []
    sources: set[str] = set()
    total_links = 0

    for source_relpath, link in iter_standing_link_occurrences(vault_root=root, scan_root=scan):
        total_links += 1
        sources.add(source_relpath)
        result = classify_link_prefix_candidate(
            source_relpath=source_relpath,
            link=link,
            existing_target_relpaths=existing,
        )
        counts[result.reason_code] += 1
        row = result.to_dict()
        if result.allowed:
            if len(allowed_examples) < allowed_example_limit:
                allowed_examples.append(row)
        elif len(excluded_examples) < excluded_example_limit:
            excluded_examples.append(row)

    allowed_count = counts.get("allowed", 0)
    summary = {
        "total_links": total_links,
        "source_files": len(sources),
        "allowed_count": allowed_count,
        "excluded_count": total_links - allowed_count,
        "counts_by_reason": dict(sorted(counts.items())),
        "actionable_apply_items": 0,
    }
    return StandingSafeLinkPrefixBaseline(
        schema=MODE,
        mode="read-only live classifier baseline",
        status="ok",
        created_at=_utc_now(),
        vault_root=str(root),
        scan_root=str(scan),
        source_policy=str(policy.get("policy_id", "standing-safe-link-prefix-hygiene")),
        live_mutation_authorized=False,
        approval_manifest_created=False,
        apply_authority="none",
        summary=summary,
        allowed_examples=allowed_examples,
        excluded_examples=excluded_examples,
    )


def standing_safe_link_prefix_baseline_to_markdown(packet: dict[str, Any]) -> str:
    summary = packet["summary"]
    lines = [
        "# Standing safe link-prefix baseline",
        "",
        "Status: read-only classifier baseline; no live mutation authority.",
        "",
        "## Summary",
        "",
        f"- total_links: `{summary['total_links']}`",
        f"- source_files: `{summary['source_files']}`",
        f"- allowed_count: `{summary['allowed_count']}`",
        f"- excluded_count: `{summary['excluded_count']}`",
        f"- actionable_apply_items: `{summary['actionable_apply_items']}`",
        f"- counts_by_reason: `{summary['counts_by_reason']}`",
        "",
        "## Authority",
        "",
        f"- live_mutation_authorized: `{packet['live_mutation_authorized']}`",
        f"- approval_manifest_created: `{packet['approval_manifest_created']}`",
        f"- apply_authority: `{packet['apply_authority']}`",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_standing_safe_link_prefix_baseline(
    *,
    vault_root: str | Path,
    out_dir: str | Path,
    scan_root: str | Path | None = None,
) -> dict[str, str]:
    baseline = build_standing_safe_link_prefix_baseline(vault_root=vault_root, scan_root=scan_root)
    packet = baseline.to_dict()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet_path = out / "standing-safe-link-prefix-baseline-v1.json"
    report_path = out / "REPORT.md"
    packet_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(standing_safe_link_prefix_baseline_to_markdown(packet), encoding="utf-8")
    return {"status": "ok", "packet": str(packet_path), "report": str(report_path)}
