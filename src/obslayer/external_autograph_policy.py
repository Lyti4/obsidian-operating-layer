from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

POLICY_FILENAME = "external_autograph_policy.v1.json"
_POLICY_PATH = Path(__file__).with_name("policies") / POLICY_FILENAME


@lru_cache(maxsize=1)
def load_external_autograph_policy() -> dict[str, Any]:
    """Load the bundled external-autograph policy artifact.

    The artifact is machine-readable policy metadata distilled from
    `smixs/autograph` and `smixs/agent-second-brain`. It is intentionally
    evidence-only: loading it never grants live vault mutation authority.
    """

    policy = json.loads(_POLICY_PATH.read_text(encoding="utf-8"))
    validate_external_autograph_policy(policy)
    return policy


def validate_external_autograph_policy(policy: dict[str, Any]) -> None:
    required = (
        "policy_id",
        "policy_ref",
        "source_repos",
        "authority",
        "protected_path_denylist",
        "generated_report_noise",
        "forbidden_reason_codes",
        "forbidden_safety_flags",
        "link_resolution_classes",
        "dedup_action_taxonomy",
        "alias_policy_refs",
        "salvage",
        "remaining_link_triage",
    )
    missing = [key for key in required if key not in policy]
    if missing:
        raise ValueError(f"external autograph policy missing required keys: {missing}")

    authority = policy["authority"]
    if authority.get("default_apply_authority") != "none":
        raise ValueError("external autograph policy must default to apply_authority=none")
    if authority.get("live_mutation_authorized") is not False:
        raise ValueError("external autograph policy must not authorize live mutation")
    if authority.get("approved_default") is not False:
        raise ValueError("external autograph policy must default approved=false")

    if not policy["protected_path_denylist"]:
        raise ValueError("external autograph policy protected_path_denylist must not be empty")
    if not policy["generated_report_noise"].get("path_parts"):
        raise ValueError("external autograph policy generated_report_noise.path_parts must not be empty")
    if not policy["generated_report_noise"].get("noise_words"):
        raise ValueError("external autograph policy generated_report_noise.noise_words must not be empty")


def external_policy_source(rule_id: str) -> dict[str, Any]:
    policy = load_external_autograph_policy()
    return {
        "policy_id": policy["policy_id"],
        "rule_id": rule_id,
        "policy_ref": policy["policy_ref"],
        "source_repos": list(policy["source_repos"]),
    }
