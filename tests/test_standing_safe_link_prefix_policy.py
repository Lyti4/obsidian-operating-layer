from __future__ import annotations

import json
import subprocess
import sys

import pytest

from obslayer.standing_safe_link_prefix_policy import (
    classify_link_prefix_candidate,
    classify_source_relpath,
    load_standing_safe_link_prefix_policy,
    validate_standing_safe_link_prefix_policy,
)

EXISTING_TARGETS = {"Memory-Vault/Hermes/Inbox.md", "Memory-Vault/Hermes/Alias Target.md"}


def test_allows_normal_memory_vault_note_with_existing_target() -> None:
    result = classify_link_prefix_candidate(
        source_relpath="Memory-Vault/Notes/source.md",
        link="[[Hermes/Inbox]]",
        existing_target_relpaths=EXISTING_TARGETS,
    )

    assert result.allowed is True
    assert result.reason_code == "allowed"
    assert result.target_relpath == "Memory-Vault/Hermes/Inbox.md"
    assert result.rewritten_link == "[[Memory-Vault/Hermes/Inbox]]"
    assert result.live_mutation_authorized is False


@pytest.mark.parametrize(
    "source_relpath,reason_code",
    [
        ("Memory-Vault/Hermes/Reports/link-report.md", "excluded_generated_report_surface"),
        ("Memory-Vault/Reports/link-report.md", "excluded_generated_report_surface"),
    ],
)
def test_blocks_reports(source_relpath: str, reason_code: str) -> None:
    result = classify_link_prefix_candidate(
        source_relpath=source_relpath,
        link="[[Hermes/Inbox]]",
        existing_target_relpaths=EXISTING_TARGETS,
    )

    assert result.allowed is False
    assert result.reason_code == reason_code


@pytest.mark.parametrize(
    "source_relpath,reason_code",
    [
        ("Memory-Vault/_Backups/source.md", "excluded_protected_path"),
        ("Memory-Vault/_Archive/source.md", "excluded_protected_path"),
        ("Memory-Vault/.trash/source.md", "excluded_protected_path"),
        ("Memory-Vault/.obsidian/source.md", "excluded_protected_path"),
    ],
)
def test_blocks_protected_paths(source_relpath: str, reason_code: str) -> None:
    result = classify_source_relpath(source_relpath)

    assert result.allowed is False
    assert result.reason_code == reason_code


def test_blocks_soul_paths() -> None:
    result = classify_link_prefix_candidate(
        source_relpath="Memory-Vault/Soul/Identity.md",
        link="[[Hermes/Inbox]]",
        existing_target_relpaths=EXISTING_TARGETS,
    )

    assert result.allowed is False
    assert result.reason_code == "excluded_soul_path"


def test_blocks_missing_target() -> None:
    result = classify_link_prefix_candidate(
        source_relpath="Memory-Vault/Notes/source.md",
        link="[[Hermes/Missing]]",
        existing_target_relpaths=EXISTING_TARGETS,
    )

    assert result.allowed is False
    assert result.reason_code == "missing_target"
    assert result.target_relpath == "Memory-Vault/Hermes/Missing.md"


def test_preserves_alias() -> None:
    result = classify_link_prefix_candidate(
        source_relpath="Memory-Vault/Notes/source.md",
        link="[[Hermes/Alias Target|keep this label]]",
        existing_target_relpaths=EXISTING_TARGETS,
    )

    assert result.allowed is True
    assert result.rewritten_link == "[[Memory-Vault/Hermes/Alias Target|keep this label]]"


def test_policy_authority_remains_false() -> None:
    policy = load_standing_safe_link_prefix_policy()
    validation = validate_standing_safe_link_prefix_policy(policy)

    assert validation["valid"] is True
    assert validation["live_mutation_authorized"] is False
    assert validation["approval_authority"] == "none"


def test_cli_classifies_fixture_without_scanning_vault() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "tools/obsidian_standing_safe_link_prefix_policy.py",
            "--source-relpath",
            "Memory-Vault/Notes/source.md",
            "--link",
            "[[Hermes/Inbox]]",
            "--existing-target",
            "Memory-Vault/Hermes/Inbox.md",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["classification"]["allowed"] is True
    assert payload["classification"]["live_mutation_authorized"] is False


def test_package_exports_policy_helpers() -> None:
    import obslayer

    result = obslayer.classify_link_prefix_candidate(
        source_relpath="Memory-Vault/Notes/source.md",
        link="[[Hermes/Inbox]]",
        existing_target_relpaths=EXISTING_TARGETS,
    )

    assert result.allowed is True
    assert obslayer.validate_standing_safe_link_prefix_policy is validate_standing_safe_link_prefix_policy
