from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_APPROVAL_PHRASE = "APPROVE OBSIDIAN APPLY"
DEFAULT_MAX_FILES_PER_RUN = 25
DEFAULT_PROJECT_SLUG = "obsidian-operating-layer"
DEFAULT_BACKUP_ROOT = "_Backups/obsidian-operating-layer"
DEFAULT_PROTECTED_RELATIVE = (
    ".obsidian",
    "_Backups",
    "_Archive",
    ".trash",
    "Soul-Vault/Hermes/Soul",
    "Soul-Vault/Soul",
)
DEFAULT_EXCLUDED_DIRS = (
    ".obsidian",
    "_Backups",
    "_Archive",
    ".trash",
)
DEFAULT_DRY_RUN_COMMANDS = (
    "python tools/obsidian_observe.py --vault /home/hermesadmin/Obsidian --out /tmp/obslayer-observe.json",
    "python tools/obsidian_propose.py --observe /tmp/obslayer-observe.json --out-dir /tmp/obslayer-proposal",
    "python tools/obsidian_verify.py --observe /tmp/obslayer-observe.json --proposal /tmp/obslayer-proposal/proposal.json",
    "python tools/obsidian_backfill_report.py --proposal /tmp/obslayer-proposal/proposal.json "
    "--reports-dir /home/hermesadmin/Obsidian/Memory-Vault/Hermes/Reports",
)


class GuardrailError(ValueError):
    """Raised when a command would violate the Obsidian operating rails."""


@dataclass(frozen=True)
class ApprovalManifest:
    approved: bool
    approval_phrase: str
    task_id: str
    approver: str
    reason: str
    vault_root: str
    targets: list[str]
    backup_root: str
    dry_run: bool = False
    require_post_verify: bool = True
    max_files_per_run: int = DEFAULT_MAX_FILES_PER_RUN
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BackupPlan:
    vault_root: str
    backup_root: str
    backup_dir: str
    timestamp: str
    targets: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RunCommands:
    observe: str
    propose: str
    apply: str
    verify: str
    backfill_report: str

    def to_dict(self) -> dict:
        return asdict(self)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")


def load_json(path: str | Path) -> dict:
    data = Path(path).read_text(encoding="utf-8")
    obj = json.loads(data)
    if not isinstance(obj, dict):
        raise GuardrailError(f"Expected JSON object in {path}")
    return obj


def write_json(path: str | Path, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_vault_root(vault_root: str | Path) -> Path:
    root = Path(vault_root).expanduser().resolve()
    if not root.exists():
        raise GuardrailError(f"Vault root does not exist: {root}")
    if not root.is_dir():
        raise GuardrailError(f"Vault root is not a directory: {root}")
    return root


def relpath_under_root(root: Path, candidate: str | Path) -> Path:
    path = Path(candidate).expanduser().resolve()
    try:
        rel = path.relative_to(root)
    except ValueError as exc:
        raise GuardrailError(f"Target escapes vault root: {path}") from exc
    return rel


def is_protected_relative(relpath: Path | str) -> bool:
    rel = Path(relpath).as_posix()
    if rel.startswith("./"):
        rel = rel[2:]
    return any(rel == protected or rel.startswith(protected + "/") for protected in DEFAULT_PROTECTED_RELATIVE)


def validate_targets(vault_root: str | Path, targets: Sequence[str | Path]) -> list[Path]:
    root = normalize_vault_root(vault_root)
    normalized: list[Path] = []
    for raw in targets:
        rel = relpath_under_root(root, raw)
        if is_protected_relative(rel):
            raise GuardrailError(f"Refusing protected path: {rel}")
        normalized.append(rel)
    return normalized


def planned_backup_dir(vault_root: str | Path, timestamp: str | None = None) -> Path:
    root = normalize_vault_root(vault_root)
    ts = timestamp or utc_stamp()
    return root / DEFAULT_BACKUP_ROOT / ts


def canonical_workspace_layout() -> list[str]:
    return [
        "AGENTS.md",
        "README.md",
        "config/roles.yaml",
        "manifests/approval_manifest.example.json",
        "src/obslayer/guardrails.py",
        "tools/obsidian_observe.py",
        "tools/obsidian_propose.py",
        "tools/obsidian_apply.py",
        "tools/obsidian_verify.py",
        "tools/obsidian_backfill_report.py",
        "tests/conftest.py",
        "tests/test_guardrails.py",
        "tests/test_standing_safe_link_prefix_policy.py",
        "tools/obsidian_standing_safe_link_prefix_policy.py",
        "src/obslayer/standing_safe_link_prefix_policy.py",
        "src/obslayer/policies/standing-safe-link-prefix-hygiene.policy.json",
        "policies/standing-safe-link-prefix-hygiene.policy.json",
    ]


def canonical_run_commands() -> RunCommands:
    return RunCommands(
        observe=DEFAULT_DRY_RUN_COMMANDS[0],
        propose=DEFAULT_DRY_RUN_COMMANDS[1],
        apply=(
            "python tools/obsidian_apply.py --proposal /tmp/obslayer-proposal/proposal.json "
            "--approval-manifest /tmp/obslayer-approval.json --apply"
        ),
        verify=DEFAULT_DRY_RUN_COMMANDS[2],
        backfill_report=DEFAULT_DRY_RUN_COMMANDS[3],
    )


def build_approval_manifest(
    *,
    task_id: str,
    approver: str,
    reason: str,
    vault_root: str,
    targets: Sequence[str],
    backup_root: str | None = None,
    dry_run: bool = False,
    require_post_verify: bool = True,
    max_files_per_run: int = DEFAULT_MAX_FILES_PER_RUN,
    approval_phrase: str = DEFAULT_APPROVAL_PHRASE,
    created_at: str | None = None,
) -> ApprovalManifest:
    if not task_id:
        raise GuardrailError("approval manifest requires task_id")
    if not approver:
        raise GuardrailError("approval manifest requires approver")
    if not reason:
        raise GuardrailError("approval manifest requires reason")
    if not targets:
        raise GuardrailError("approval manifest requires at least one target")
    validate_targets(vault_root, targets)
    return ApprovalManifest(
        approved=True,
        approval_phrase=approval_phrase,
        task_id=task_id,
        approver=approver,
        reason=reason,
        vault_root=str(normalize_vault_root(vault_root)),
        targets=[str(Path(t)) for t in targets],
        backup_root=backup_root or DEFAULT_BACKUP_ROOT,
        dry_run=dry_run,
        require_post_verify=require_post_verify,
        max_files_per_run=max_files_per_run,
        created_at=created_at or utc_stamp(),
    )


def validate_approval_manifest(manifest: dict) -> ApprovalManifest:
    required = ["approved", "approval_phrase", "task_id", "approver", "reason", "vault_root", "targets", "backup_root"]
    missing = [field for field in required if field not in manifest]
    if missing:
        raise GuardrailError(f"Approval manifest missing fields: {', '.join(missing)}")
    if manifest["approval_phrase"] != DEFAULT_APPROVAL_PHRASE:
        raise GuardrailError("Approval phrase mismatch")
    if manifest["approved"] is not True:
        raise GuardrailError("Approval manifest must set approved=true")
    if manifest.get("dry_run", False) is True:
        raise GuardrailError("Approval manifest cannot authorize live apply while dry_run=true")
    if manifest.get("require_post_verify", True) is not True:
        raise GuardrailError("Approval manifest must require post-apply verification")
    if not isinstance(manifest["targets"], list) or not manifest["targets"]:
        raise GuardrailError("Approval manifest targets must be a non-empty list")
    backup_root = Path(str(manifest["backup_root"]))
    if backup_root.is_absolute() or ".." in backup_root.parts:
        raise GuardrailError("Approval manifest backup_root must stay inside the vault")
    if backup_root.as_posix() != DEFAULT_BACKUP_ROOT:
        raise GuardrailError("Approval manifest backup_root must use _Backups/obsidian-operating-layer")

    vault_root = normalize_vault_root(manifest["vault_root"])
    validate_targets(vault_root, manifest["targets"])
    max_files = int(manifest.get("max_files_per_run", DEFAULT_MAX_FILES_PER_RUN))
    if max_files <= 0:
        raise GuardrailError("max_files_per_run must be positive")

    return ApprovalManifest(
        approved=True,
        approval_phrase=manifest["approval_phrase"],
        task_id=manifest["task_id"],
        approver=manifest["approver"],
        reason=manifest["reason"],
        vault_root=str(vault_root),
        targets=[str(t) for t in manifest["targets"]],
        backup_root=manifest["backup_root"],
        dry_run=bool(manifest.get("dry_run", False)),
        require_post_verify=bool(manifest.get("require_post_verify", True)),
        max_files_per_run=max_files,
        created_at=str(manifest.get("created_at", "")),
    )


def manifest_backup_plan(manifest: ApprovalManifest, timestamp: str | None = None) -> BackupPlan:
    ts = timestamp or utc_stamp()
    backup_dir = normalize_vault_root(manifest.vault_root) / manifest.backup_root / ts
    return BackupPlan(
        vault_root=manifest.vault_root,
        backup_root=manifest.backup_root,
        backup_dir=str(backup_dir),
        timestamp=ts,
        targets=list(manifest.targets),
    )


def parse_paths(values: Iterable[str]) -> list[str]:
    return [str(Path(value).expanduser()) for value in values]
