from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OperatorReviewQueueItem:
    id: str
    state: str
    title: str
    evidence_paths: list[str]
    existing_evidence_paths: list[str]
    missing_evidence_paths: list[str]
    live_mutation_authorized: bool
    next_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorReviewQueue:
    status: str
    mode: str
    created_at: str
    repo_root: str
    item_count: int
    live_mutation_authorized: bool
    approval_manifest_created: bool
    items: list[OperatorReviewQueueItem]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["items"] = [item.to_dict() for item in self.items]
        return payload


_DEFAULT_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "id": "orchestrator-consolidation-spec",
        "state": "review_ready",
        "title": "Orchestrator consolidation spec",
        "evidence_paths": [
            "docs/spec-kit/30-orchestrator-operating-spec.md",
            "docs/acceptance/index.md",
        ],
        "next_step": "Keep as first-read operator surface; update only when accepted boundaries change.",
    },
    {
        "id": "operator-flow-review-queue-spec",
        "state": "review_ready",
        "title": "Agentic OS operator flow and evidence-gated review queue spec",
        "evidence_paths": [
            "docs/spec-kit/31-operator-flow-and-review-queue.md",
            "docs/spec-kit/30-orchestrator-operating-spec.md",
        ],
        "next_step": "Use this generated index as deterministic review-queue companion evidence.",
    },
    {
        "id": "working-note-link-apply-postverify",
        "state": "applied_verified",
        "title": "Working-note link hygiene apply/post-verify",
        "evidence_paths": [
            "out/reports/working-note-link-apply/20260704T163336Z/REPORT.md",
            "out/reports/working-note-link-post-apply-verify/20260704T163336Z/REPORT.md",
            "out/reports/working-note-link-post-apply-observation/20260704T164100Z/REPORT.md",
        ],
        "next_step": "Treat as closed evidence unless a fresh scan finds regressions.",
    },
    {
        "id": "next-safe-working-note-disambiguation",
        "state": "proposal_drafted",
        "title": "Next safe working-note disambiguation proposal",
        "evidence_paths": [
            "out/proposals/working-note-link-next-safe-disambiguation/20260704T170712Z/REPORT.md",
        ],
        "next_step": "Promote to operator review only after exact candidate risk is rechecked.",
    },


    {
        "id": "agentic-improvement-loop",
        "state": "review_ready",
        "title": "Nanobot -> Hermes -> Spec Kit / Queue -> Codex continuous improvement loop",
        "evidence_paths": [
            "docs/spec-kit/34-agentic-improvement-loop.md",
            "docs/spec-kit/31-operator-flow-and-review-queue.md",
            ".codex-hermes/comm/hermes-inbox/agentic-os-project-wide-review-20260704.wrapper-20260704T193616Z.report.json",
        ],
        "next_step": (
            "Retry project-wide Codex review after provider usage resets; "
            "meanwhile use Hermes triage and Nanobot reports as proposal-first inputs."
        ),
        "mixed_home_relative": True,
    },


    {
        "id": "agentic-control-plane-map",
        "state": "accepted_repo_only",
        "title": "Agentic OS control-plane map for Nanobot/Hermes/Codex surfaces",
        "evidence_paths": [
            "docs/spec-kit/35-agentic-os-control-plane-map.md",
            "docs/acceptance/index.md",
            "src/obslayer/project_docs_lag_audit.py",
            "out/reports/nanobot-all-reports-aggregate-20260705.md",
        ],
        "next_step": "Use as the canonical cross-link surface for future Nanobot docs-lag findings.",
    },
    {
        "id": "semantic-indexing-manifest",
        "state": "ready_for_operator_review",
        "title": "Semantic/indexing manifest chain for Graphify-derived proposals",
        "evidence_paths": [
            "docs/spec-kit/29-semantic-proposal-workflow.md",
            "docs/spec-kit/36-current-evidence-index.md",
            "docs/acceptance/index.md",
            "src/obslayer/semantic_manifest.py",
            "tools/obsidian_semantic_manifest.py",
            "tests/test_semantic_manifest.py",
            "out/reports/semantic-manifests/manual/semantic-manifest.json",
            "out/reports/semantic-manifests/manual/REPORT.md",
        ],
        "next_step": (
            "Use as the terminal semantic/indexing review evidence; "
            "live vault application remains a separate explicit approval step."
        ),
    },
    {
        "id": "codex-native-runtime",
        "state": "review_ready",
        "title": "Codex native Hermes runner, schemas, and Nanobot/Codex role separation",
        "evidence_paths": [
            "docs/spec-kit/33-codex-native-runtime.md",
            "tools/hermes_codex_run.py",
            "schemas/codex_task.v1.json",
            "schemas/codex_report.v1.json",
            "docs/spec-kit/32-codex-hermes-communication-channel.md",
        ],
        "next_step": "Use hermes-codex-run for bounded Codex dispatch; keep Nanobot as scout/recommender only.",
    },
    {
        "id": "codex-hermes-comm-channel",
        "state": "review_ready",
        "title": "Codex internal Hermes communication channel",
        "evidence_paths": [
            "docs/spec-kit/32-codex-hermes-communication-channel.md",
            "tools/codex_hermes_comm.py",
            ".codex-hermes/docs/ROLE_POLICY.json",
        ],
        "next_step": "Use for task-scoped Codex implementation/review; no cron without explicit approval.",
        "mixed_home_relative": True,
    },
    {
        "id": "nanobot-internal-comm-channel",
        "state": "review_ready",
        "title": "Nanobot internal Hermes communication channel",
        "evidence_paths": [
            ".nanobot-hermes/comm/hermes-inbox/latest.md",
            ".nanobot-hermes/comm/nanobot-inbox/latest.md",
        ],
        "next_step": "Keep watcher local-only and use Nanobot output as second opinion.",
        "home_relative": True,
    },
    {
        "id": "evidence-gateway-generated-indexes",
        "state": "review_ready",
        "title": "Read-only evidence gateway generated Markdown indexes",
        "evidence_paths": [
            "src/obslayer/nanobot_readonly_evidence_gateway.py",
            "tests/test_nanobot_readonly_evidence_gateway.py",
        ],
        "next_step": "Live gateway service restart remains separate explicit approval.",
    },
)


def _resolve_evidence_path(repo_root: Path, rel: str, *, home_relative: bool = False) -> Path:
    if home_relative:
        return Path.home() / rel
    return repo_root / rel


def build_operator_review_queue(
    repo_root: str | Path,
    *,
    created_at: str | None = None,
    candidates: tuple[dict[str, Any], ...] = _DEFAULT_CANDIDATES,
) -> OperatorReviewQueue:
    root = Path(repo_root).expanduser().resolve()
    items: list[OperatorReviewQueueItem] = []
    for candidate in candidates:
        evidence_paths = [str(path) for path in candidate["evidence_paths"]]
        home_relative = bool(candidate.get("home_relative", False))
        mixed_home_relative = bool(candidate.get("mixed_home_relative", False))
        existing: list[str] = []
        missing: list[str] = []
        for rel in evidence_paths:
            resolved = _resolve_evidence_path(
                root,
                rel,
                home_relative=home_relative or (mixed_home_relative and rel.startswith(".")),
            )
            if resolved.exists():
                existing.append(rel)
            else:
                missing.append(rel)
        state = str(candidate["state"])
        if missing and state in {"review_ready", "applied_verified"}:
            state = "held"
        items.append(
            OperatorReviewQueueItem(
                id=str(candidate["id"]),
                state=state,
                title=str(candidate["title"]),
                evidence_paths=evidence_paths,
                existing_evidence_paths=existing,
                missing_evidence_paths=missing,
                live_mutation_authorized=False,
                next_step=str(candidate["next_step"]),
            )
        )
    return OperatorReviewQueue(
        status="ready" if all(not item.missing_evidence_paths for item in items) else "ready-with-held-items",
        mode="operator-review-queue",
        created_at=created_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo_root=str(root),
        item_count=len(items),
        live_mutation_authorized=False,
        approval_manifest_created=False,
        items=items,
    )


def operator_review_queue_to_markdown(queue: OperatorReviewQueue) -> str:
    lines = [
        "# Operator Review Queue",
        "",
        f"Status: `{queue.status}`",
        f"Mode: `{queue.mode}`",
        f"Created UTC: `{queue.created_at}`",
        f"Repo root: `{queue.repo_root}`",
        f"Items: `{queue.item_count}`",
        f"Live mutation authorized: `{queue.live_mutation_authorized}`",
        f"Approval manifest created: `{queue.approval_manifest_created}`",
        "",
        "## Queue items",
        "",
        "| id | state | existing evidence | missing evidence | next step |",
        "|---|---|---:|---:|---|",
    ]
    for item in queue.items:
        next_step = item.next_step.replace("|", "\\|")
        lines.append(
            f"| `{item.id}` | `{item.state}` | {len(item.existing_evidence_paths)} | {len(item.missing_evidence_paths)} | {next_step} |"
        )
    lines.extend(["", "## Details", ""])
    for item in queue.items:
        lines.extend(
            [
                f"### {item.id}",
                "",
                f"Title: {item.title}",
                f"State: `{item.state}`",
                f"Live mutation authorized: `{item.live_mutation_authorized}`",
                "",
                "Evidence:",
            ]
        )
        for path in item.evidence_paths:
            mark = "ok" if path in item.existing_evidence_paths else "missing"
            lines.append(f"- `{mark}` `{path}`")
        lines.append("")
    lines.extend(
        [
            "## Safety boundary",
            "",
            "- This queue is a coordination artifact only.",
            "- Queue state does not authorize live vault mutation.",
            "- Approval manifests, backups, applies, restarts, auth/profile changes, and cron changes "
            "remain separate explicit approval steps.",
            "- Nanobot evidence is a second opinion; Hermes remains acceptance owner.",
            "",
        ]
    )
    return "\n".join(lines)


def write_operator_review_queue(queue: OperatorReviewQueue, out_dir: str | Path) -> dict[str, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    queue_json = target / "queue.json"
    report = target / "REPORT.md"
    queue_json.write_text(json.dumps(queue.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report.write_text(operator_review_queue_to_markdown(queue), encoding="utf-8")
    return {"queue_json": queue_json, "report": report}
