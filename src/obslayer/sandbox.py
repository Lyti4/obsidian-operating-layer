from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from .guardrails import DEFAULT_EXCLUDED_DIRS, GuardrailError, is_protected_relative, normalize_vault_root, utc_stamp


@dataclass(frozen=True)
class SandboxCopyReport:
    source_vault: str
    sandbox_vault: str
    copied_files: int
    copied_dirs: int
    skipped_paths: list[str]
    excluded_roots: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _ensure_under_root(root: Path, candidate: Path) -> None:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise GuardrailError(f"Sandbox target escapes sandbox root: {candidate}") from exc


def _should_exclude(relpath: Path) -> bool:
    if relpath == Path("."):
        return False
    return relpath.parts[0] in DEFAULT_EXCLUDED_DIRS or is_protected_relative(relpath)


def create_sandbox_vault(
    *,
    source_vault: str | Path,
    sandbox_root: str | Path,
    name: str | None = None,
    reset: bool = False,
) -> SandboxCopyReport:
    """Copy a vault into a protected-path-excluding sandbox directory.

    This function only reads the source vault. It writes into sandbox_root/name and
    refuses destructive reset outside sandbox_root.
    """

    source = normalize_vault_root(source_vault)
    root = Path(sandbox_root).expanduser().resolve()
    sandbox_name = name or f"vault-{utc_stamp()}"
    if Path(sandbox_name).is_absolute() or ".." in Path(sandbox_name).parts:
        raise GuardrailError("Sandbox name must be a relative safe path segment")
    target = (root / sandbox_name).resolve()
    _ensure_under_root(root, target)

    if target == source or source in target.parents:
        raise GuardrailError("Sandbox target must not be inside the source vault")
    if root == source or root in source.parents:
        raise GuardrailError("Sandbox root must not be inside the source vault")

    if target.exists():
        if not reset:
            raise GuardrailError(f"Sandbox target already exists; pass reset to recreate: {target}")
        _ensure_under_root(root, target)
        shutil.rmtree(target)

    copied_files = 0
    copied_dirs = 0
    skipped: list[str] = []
    target.mkdir(parents=True, exist_ok=True)

    for source_path in sorted(source.rglob("*")):
        rel = source_path.relative_to(source)
        if _should_exclude(rel):
            skipped.append(rel.as_posix())
            if source_path.is_dir():
                # rglob will still yield children; they are skipped by their own relpath.
                continue
            continue

        dest = target / rel
        _ensure_under_root(target, dest)
        if source_path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            copied_dirs += 1
        elif source_path.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest)
            copied_files += 1
        else:
            skipped.append(rel.as_posix())

    return SandboxCopyReport(
        source_vault=str(source),
        sandbox_vault=str(target),
        copied_files=copied_files,
        copied_dirs=copied_dirs,
        skipped_paths=skipped,
        excluded_roots=list(DEFAULT_EXCLUDED_DIRS),
    )
