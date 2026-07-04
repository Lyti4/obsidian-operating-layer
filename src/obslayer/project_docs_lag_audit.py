from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError


@dataclass(frozen=True)
class DocLagCheck:
    name: str
    document: str
    required_markers: list[str]
    status: str
    missing_markers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectDocsLagAudit:
    status: str
    generated_utc: str
    repo: str
    checks: list[DocLagCheck]
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = [check.to_dict() for check in self.checks]
        return payload


DEFAULT_CHECKS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "nanobot_15m_audit_documented",
        "docs/spec-kit/26-nanobot-standing-worker.md",
        ("every 15m", "212b7e8f3c21", "project-state.json"),
    ),
    (
        "nanobot_15m_backlog_documented",
        "docs/spec-kit/24-orchestration-backlog.md",
        ("Nanobot 15-minute audit loop", "every 15m", "project-state.json"),
    ),
    (
        "semantic_review_index_workflow_documented",
        "docs/spec-kit/29-semantic-proposal-workflow.md",
        ("tools/obsidian_semantic_review_index.py", "out/proposals/semantic-review-indexes/", "Review index step"),
    ),
    (
        "semantic_review_index_acceptance_documented",
        "docs/acceptance/index.md",
        ("Semantic targeted proposal/review index", "tools/obsidian_semantic_review_index.py"),
    ),
    (
        "llm_channel_smoke_documented",
        "docs/spec-kit/28-global-headroom-only-llm-channel.md",
        ("docs/spec-kit/schemas/llm-channel.schema.json", "make llm-channel-smoke", "make llm-channel-smoke-live"),
    ),
    (
        "operator_policy_mentions_15m_audit",
        "AGENTS.md",
        ("15 minutes", "212b7e8f3c21", "bounded read-only/proposal-only"),
    ),
)


def run_project_docs_lag_audit(repo: str | Path, *, generated_utc: str | None = None) -> ProjectDocsLagAudit:
    repo_path = Path(repo).expanduser().resolve()
    if not repo_path.is_dir():
        raise GuardrailError(f"Repo path is not a directory: {repo_path}")
    checks: list[DocLagCheck] = []
    findings: list[str] = []
    for name, rel_doc, markers in DEFAULT_CHECKS:
        path = repo_path / rel_doc
        if not path.is_file():
            missing = list(markers)
            findings.append(f"{name}: document missing: {rel_doc}")
            checks.append(DocLagCheck(name, rel_doc, list(markers), "missing-document", missing))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [marker for marker in markers if marker not in text]
        status = "ok" if not missing else "lagging"
        if missing:
            findings.append(f"{name}: missing markers in {rel_doc}: {', '.join(missing)}")
        checks.append(DocLagCheck(name, rel_doc, list(markers), status, missing))
    return ProjectDocsLagAudit(
        status="ok" if not findings else "lagging",
        generated_utc=generated_utc or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        repo=str(repo_path),
        checks=checks,
        findings=findings,
    )


def project_docs_lag_audit_to_markdown(audit: ProjectDocsLagAudit) -> str:
    lines = [
        "# Project Docs Lag Audit",
        "",
        f"Status: `{audit.status}`",
        f"Generated UTC: `{audit.generated_utc}`",
        f"Repo: `{audit.repo}`",
        "",
        "## Checks",
        "",
        "| check | status | document | missing markers |",
        "|---|---|---|---|",
    ]
    for check in audit.checks:
        missing = ", ".join(marker.replace("|", "\\|") for marker in check.missing_markers) or "none"
        lines.append(f"| `{check.name}` | `{check.status}` | `{check.document}` | {missing} |")
    lines.extend(["", "## Findings", ""])
    if audit.findings:
        lines.extend(f"- {finding}" for finding in audit.findings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            (
                "This audit is read-only and checks documentation markers only. "
                "It does not authorize live vault mutation or approval manifests."
            ),
            "",
        ]
    )
    return "\n".join(lines)
