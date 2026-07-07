from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Iterable

POLICY_FILENAME = "standing-safe-link-prefix-hygiene.policy.json"
_REPO_POLICY_PATH = Path(__file__).resolve().parents[2] / "policies" / POLICY_FILENAME
_LINK_RE = re.compile(r"^\[\[Hermes/([^\]|]+)(\|[^\]]+)?\]\]$")
_PROTECTED_PARTS = {".obsidian", "_Backups", "_Archive", ".trash", "Duplicates", "Redirects"}
_REPORT_PARTS = {"Reports", "reports", "generated", "evidence"}


@dataclass(frozen=True)
class PolicyValidation:
    valid: bool
    policy_id: str
    live_mutation_authorized: bool
    approval_authority: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClassificationResult:
    allowed: bool
    reason_code: str
    source_relpath: str | None = None
    link: str | None = None
    target_relpath: str | None = None
    rewritten_link: str | None = None
    live_mutation_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_relpath(relpath: str) -> str:
    return relpath.replace("\\", "/").strip("/")


def _path_parts(relpath: str) -> tuple[str, ...]:
    return tuple(part for part in _normalize_relpath(relpath).split("/") if part)


def load_standing_safe_link_prefix_policy(policy_path: str | Path | None = None) -> dict[str, Any]:
    """Load policy JSON from an explicit path, repo root, or package data.

    This function reads only policy artifacts. It does not inspect a vault and
    cannot grant live mutation authority.
    """

    if policy_path is not None:
        policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
    elif _REPO_POLICY_PATH.exists():
        policy = json.loads(_REPO_POLICY_PATH.read_text(encoding="utf-8"))
    else:
        package_policy = resources.files("obslayer.policies").joinpath(POLICY_FILENAME)
        policy = json.loads(package_policy.read_text(encoding="utf-8"))
    validate_standing_safe_link_prefix_policy(policy)
    return policy


def validate_standing_safe_link_prefix_policy(policy: dict[str, Any]) -> dict[str, Any]:
    required = (
        "schema",
        "policy_id",
        "status",
        "allowed_pattern",
        "required_gates",
        "not_approved_for",
        "default_limits",
    )
    missing = [key for key in required if key not in policy]
    if missing:
        raise ValueError(f"standing safe link-prefix policy missing required keys: {missing}")

    allowed_pattern = policy["allowed_pattern"]
    if allowed_pattern.get("from_regex") != r"\[\[Hermes/([^\]|]+)(\|[^\]]+)?\]\]":
        raise ValueError("standing safe link-prefix policy has unexpected from_regex")
    if allowed_pattern.get("to_template") != "[[Memory-Vault/Hermes/{title}{alias}]]":
        raise ValueError("standing safe link-prefix policy has unexpected to_template")
    if allowed_pattern.get("target_must_exist_template") != "Memory-Vault/Hermes/{title}.md":
        raise ValueError("standing safe link-prefix policy has unexpected target_must_exist_template")

    forbidden = set(policy["not_approved_for"])
    for expected in ("creates", "deletes", "renames", "moves", "missing-target link creation"):
        if expected not in forbidden:
            raise ValueError(f"standing safe link-prefix policy must not approve {expected}")

    validation = PolicyValidation(
        valid=True,
        policy_id=str(policy["policy_id"]),
        live_mutation_authorized=False,
        approval_authority="none",
    )
    return validation.to_dict()


def classify_source_relpath(source_relpath: str) -> ClassificationResult:
    source = _normalize_relpath(source_relpath)
    parts = _path_parts(source)

    if not source.endswith(".md"):
        return ClassificationResult(False, "excluded_non_markdown_source", source_relpath=source)
    if not parts or parts[0] != "Memory-Vault":
        return ClassificationResult(False, "excluded_non_memory_vault_source", source_relpath=source)
    if any(part in _PROTECTED_PARTS for part in parts):
        return ClassificationResult(False, "excluded_protected_path", source_relpath=source)
    if "Soul" in parts:
        return ClassificationResult(False, "excluded_soul_path", source_relpath=source)
    if any(part in _REPORT_PARTS for part in parts):
        return ClassificationResult(False, "excluded_generated_report_surface", source_relpath=source)
    return ClassificationResult(True, "allowed", source_relpath=source)


def classify_link_prefix_candidate(
    *,
    source_relpath: str,
    link: str,
    existing_target_relpaths: Iterable[str],
) -> ClassificationResult:
    source_result = classify_source_relpath(source_relpath)
    if not source_result.allowed:
        return ClassificationResult(
            False,
            source_result.reason_code,
            source_relpath=source_result.source_relpath,
            link=link,
        )

    match = _LINK_RE.match(link)
    if not match:
        return ClassificationResult(False, "excluded_link_pattern", source_relpath=source_result.source_relpath, link=link)

    title = match.group(1)
    alias = match.group(2) or ""
    target_relpath = f"Memory-Vault/Hermes/{title}.md"
    existing_targets = {_normalize_relpath(path) for path in existing_target_relpaths}
    if target_relpath not in existing_targets:
        return ClassificationResult(
            False,
            "missing_target",
            source_relpath=source_result.source_relpath,
            link=link,
            target_relpath=target_relpath,
        )

    return ClassificationResult(
        True,
        "allowed",
        source_relpath=source_result.source_relpath,
        link=link,
        target_relpath=target_relpath,
        rewritten_link=f"[[Memory-Vault/Hermes/{title}{alias}]]",
    )
