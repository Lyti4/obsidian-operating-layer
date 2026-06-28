from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

FORBIDDEN_AS_CAPABILITIES = {
    "write-direct",
    "delete-direct",
    "move-direct",
    "merge-direct",
    "patch-direct",
    "execute-live-mutation",
    "secret-read",
}


def test_sample_adapter_records_validate_against_schema_and_safety_contract() -> None:
    repo = Path(__file__).resolve().parents[1]
    schema_path = repo / "docs" / "spec-kit" / "schemas" / "adapter-metadata.schema.json"
    records_dir = repo / "docs" / "spec-kit" / "research" / "sample-adapter-records"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    records = sorted(records_dir.glob("*.json"))

    assert len(records) >= 3

    kinds = set()
    for record_path in records:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        validator.validate(record)
        kinds.add(record["kind"])

        assert record["direct_write_enabled"] is False
        assert record["sandbox_required"] is True
        assert not (set(record["capabilities"]) & FORBIDDEN_AS_CAPABILITIES)
        assert set(record["forbidden_capabilities"]) >= FORBIDDEN_AS_CAPABILITIES
        assert record["verification"]["sandbox_command"]
        assert record["verification"]["expected_outputs"]

    assert {"mcp-server", "rag-engine", "diagram-renderer"}.issubset(kinds)
