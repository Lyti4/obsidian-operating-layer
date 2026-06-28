from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .guardrails import (
    DEFAULT_APPROVAL_PHRASE,
    GuardrailError,
    canonical_run_commands,
    is_protected_relative,
    normalize_vault_root,
    planned_backup_dir,
    write_json,
)

RISK_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
SEVERITY_TO_RISK = {"info": "info", "low": "low", "medium": "medium", "high": "high", "critical": "critical"}


def _finding_id(finding: dict[str, Any], index: int) -> str:
    raw = finding.get("id") or finding.get("finding_id") or f"finding-{index + 1}"
    return str(raw)


def _finding_risk(finding: dict[str, Any]) -> str:
    raw = str(finding.get("risk") or finding.get("risk_class") or finding.get("severity") or "medium").lower()
    return SEVERITY_TO_RISK.get(raw, "medium")


def _max_risk(risks: Iterable[str]) -> str:
    return max(risks, key=lambda risk: RISK_ORDER.get(risk, RISK_ORDER["medium"]), default="info")


def _target_items(finding: dict[str, Any]) -> list[dict[str, Any]]:
    raw_targets = finding.get("targets")
    if raw_targets is None and "target" in finding:
        raw_targets = [finding["target"]]
    if raw_targets is None:
        raise GuardrailError("Finding must include targets or target")
    if not isinstance(raw_targets, list):
        raise GuardrailError("Finding targets must be a list")
    targets: list[dict[str, Any]] = []
    for raw in raw_targets:
        if not isinstance(raw, dict):
            raise GuardrailError("Each finding target must be an object")
        targets.append(raw)
    return targets


def _normalize_target_path(vault_root: Path, raw_path: Any) -> str:
    if not raw_path:
        raise GuardrailError("Finding target missing path")
    candidate = Path(str(raw_path)).expanduser()
    target_path = candidate.resolve() if candidate.is_absolute() else (vault_root / candidate).resolve()
    try:
        rel = target_path.relative_to(vault_root)
    except ValueError as exc:
        raise GuardrailError(f"Target escapes vault root: {target_path}") from exc
    if is_protected_relative(rel):
        raise GuardrailError(f"Refusing protected path: {rel}")
    return rel.as_posix()


def _normalize_proposal_target(
    *,
    vault_root: Path,
    raw_target: dict[str, Any],
    finding: dict[str, Any],
    finding_id: str,
    risk: str,
) -> dict[str, Any]:
    path = _normalize_target_path(vault_root, raw_target.get("path"))
    if "new_text" not in raw_target:
        raise GuardrailError(f"Finding target missing new_text for {path}")

    new_text = str(raw_target["new_text"])
    old_text = str(raw_target.get("old_text", ""))
    normalized = {
        "path": path,
        "old_text": old_text,
        "new_text": new_text,
        "replacement_mode": str(raw_target.get("replacement_mode", "replace_text")),
        "old_text_sha256": hashlib.sha256(old_text.encode("utf-8")).hexdigest(),
        "finding_id": finding_id,
        "finding_type": str(finding.get("type", "unspecified")),
        "risk": risk,
        "evidence": str(finding.get("evidence", "")),
    }
    if raw_target.get("base_sha256"):
        normalized["base_sha256"] = str(raw_target["base_sha256"])
    return normalized


def normalize_findings_to_proposal(*, vault_root: str | Path, findings: list[dict[str, Any]], source_id: str) -> dict[str, Any]:
    root = normalize_vault_root(vault_root)
    if not isinstance(findings, list):
        raise GuardrailError("findings must be a list")

    targets: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    risks: list[str] = []

    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise GuardrailError("Each finding must be an object")
        finding_id = _finding_id(finding, index)
        risk = _finding_risk(finding)
        finding_targets = _target_items(finding)
        normalized_targets = [
            _normalize_proposal_target(
                vault_root=root,
                raw_target=raw_target,
                finding=finding,
                finding_id=finding_id,
                risk=risk,
            )
            for raw_target in finding_targets
        ]
        targets.extend(normalized_targets)
        target_paths = [target["path"] for target in normalized_targets]
        evidence.append(
            {
                "finding_id": finding_id,
                "finding_type": str(finding.get("type", "unspecified")),
                "target_paths": target_paths,
                "evidence": str(finding.get("evidence", "")),
                "risk": risk,
            }
        )
        risks.append(risk)

    backup_dir = planned_backup_dir(root)
    run_commands = canonical_run_commands().to_dict()
    return {
        "vault_root": str(root),
        "source_id": source_id,
        "summary": f"Proposal normalized from {len(findings)} component finding(s).",
        "mode": "dry-run",
        "dry_run_default": True,
        "approval_required": True,
        "approval_phrase": DEFAULT_APPROVAL_PHRASE,
        "backup_plan": {
            "backup_root": str(backup_dir.parent),
            "backup_dir": str(backup_dir),
        },
        "targets": targets,
        "evidence": evidence,
        "risk_class": _max_risk(risks),
        "run_commands": run_commands,
        "next_safe_step": "Review the normalized proposal, then create an approval manifest before any live apply.",
    }


def proposal_target_diff(target: dict[str, Any], *, max_chars: int = 4000) -> str:
    target_path = str(target.get("path", "<missing>"))
    old_text = str(target.get("old_text", ""))
    new_text = str(target.get("new_text", ""))
    diff = "".join(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{target_path}",
            tofile=f"b/{target_path}",
            n=3,
        )
    )
    if not diff:
        diff = "# no textual old_text/new_text diff available\n"
    if len(diff) > max_chars:
        diff = diff[:max_chars].rstrip() + "\n... [diff truncated]\n"
    return diff


def proposal_to_markdown(proposal: dict[str, Any]) -> str:
    lines = [
        "# Obsidian Operating Layer Normalized Proposal",
        "",
        f"- source: `{proposal['source_id']}`",
        f"- vault: `{proposal['vault_root']}`",
        f"- dry-run default: `{proposal['dry_run_default']}`",
        f"- approval required: `{proposal['approval_required']}`",
        f"- risk class: `{proposal['risk_class']}`",
        f"- targets: `{len(proposal['targets'])}`",
        "",
        "## Evidence",
    ]
    for item in proposal["evidence"]:
        paths = ", ".join(f"`{path}`" for path in item["target_paths"])
        lines.append(f"- `{item['finding_id']}` / `{item['risk']}` / {paths} — {item['evidence']}")
    if proposal["targets"]:
        lines.extend(["", "## Proposed diff"])
        for target in proposal["targets"]:
            lines.extend(
                [
                    "",
                    f"### `{target.get('path', '<missing>')}`",
                    "",
                    "```diff",
                    proposal_target_diff(target).rstrip(),
                    "```",
                ]
            )
    lines.extend(
        [
            "",
            "## Next safe step",
            "",
            proposal["next_safe_step"],
            "",
        ]
    )
    return "\n".join(lines)


def write_normalized_proposal(proposal: dict[str, Any], out_dir: str | Path) -> tuple[Path, Path]:
    root = Path(out_dir).expanduser().resolve()
    vault_root = normalize_vault_root(proposal["vault_root"])
    try:
        root.relative_to(vault_root)
    except ValueError:
        pass
    else:
        raise GuardrailError(f"Refusing proposal output inside vault root: {root}")
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "proposal.json"
    markdown_path = root / "proposal.md"
    write_json(json_path, proposal)
    markdown_path.write_text(proposal_to_markdown(proposal), encoding="utf-8")
    return json_path, markdown_path


def load_findings_bundle(path: str | Path) -> tuple[str, list[dict[str, Any]]]:
    payload = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return "component-findings", payload
    if not isinstance(payload, dict):
        raise GuardrailError("Findings JSON must be an object or list")
    raw_findings = payload.get("findings")
    if not isinstance(raw_findings, list):
        raise GuardrailError("Findings JSON object must include a findings list")
    return str(payload.get("source_id") or payload.get("adapter") or "component-findings"), raw_findings
