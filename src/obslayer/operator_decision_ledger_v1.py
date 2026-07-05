from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

BEHAVIOR = "evidence-only"
MODE = "operator-decision-ledger-v1"
DEFAULT_REASON_CODES = ["operator_decision_ledger_evidence_only", "no_live_apply_authorized"]
_DEFAULT_SAFETY_FLAGS = ["evidence_only", "no_live_apply", "operator_review_required"]


@dataclass(frozen=True)
class OperatorDecisionRecord:
    created_at: str
    decision_id: str
    decision_type: str
    actor: str
    reason: str
    evidence_refs: list[Any]
    proposal_refs: list[Any]
    target_refs: list[Any]
    approval_manifest_refs: list[Any]
    safety_flags: list[str]
    behavior: str = BEHAVIOR
    live_mutation_authorized: bool = False
    approval_manifest_created: bool = False
    targets: list[Any] | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data["targets"] is None:
            data["targets"] = []
        if data["metadata"] is None:
            data["metadata"] = {}
        return data


@dataclass(frozen=True)
class OperatorDecisionLedger:
    mode: str
    status: str
    ledger_id: str
    created_at: str
    behavior: str
    live_mutation_authorized: bool
    approval_manifest_created: bool
    targets: list[Any]
    reason_codes: list[str]
    safety_flags: list[str]
    records: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_decision_record(
    record: Mapping[str, Any] | None = None,
    *,
    created_at: str | None = None,
    decision_id: str | None = None,
    decision_type: str | None = None,
    actor: str | None = None,
    reason: str | None = None,
    evidence_refs: Iterable[Any] | None = None,
    proposal_refs: Iterable[Any] | None = None,
    target_refs: Iterable[Any] | None = None,
    approval_manifest_refs: Iterable[Any] | None = None,
    safety_flags: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize one operator decision as inert, JSON-serializable evidence.

    Incoming live-apply/approval flags are intentionally ignored and rewritten to
    false so a ledger record can cite an approval/proposal artifact as data
    without becoming an approval manifest or apply authorization.
    """

    source = dict(record or {})
    normalized_created_at = str(created_at or source.get("created_at") or source.get("timestamp") or utc_timestamp())
    normalized_type = _non_empty(decision_type, source.get("decision_type"), source.get("type"), default="operator-decision")
    normalized_id = _non_empty(
        decision_id,
        source.get("decision_id"),
        source.get("id"),
        default=_default_decision_id(normalized_type, normalized_created_at),
    )

    record_metadata = _normalize_mapping(metadata if metadata is not None else source.get("metadata") or {})
    normalized = OperatorDecisionRecord(
        created_at=normalized_created_at,
        decision_id=normalized_id,
        decision_type=normalized_type,
        actor=_non_empty(actor, source.get("actor"), default="operator"),
        reason=_non_empty(reason, source.get("reason"), default=""),
        evidence_refs=_normalize_refs(evidence_refs if evidence_refs is not None else source.get("evidence_refs") or []),
        proposal_refs=_normalize_refs(proposal_refs if proposal_refs is not None else source.get("proposal_refs") or []),
        target_refs=_normalize_refs(target_refs if target_refs is not None else source.get("target_refs") or []),
        approval_manifest_refs=_normalize_refs(
            approval_manifest_refs if approval_manifest_refs is not None else source.get("approval_manifest_refs") or []
        ),
        safety_flags=_normalize_flags(safety_flags if safety_flags is not None else source.get("safety_flags") or []),
        targets=[],
        metadata=record_metadata,
    ).to_dict()
    return _normalize_mapping(normalized)


def append_decision_record(
    records: Iterable[Mapping[str, Any]],
    record: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Append one normalized record and return a deterministic ledger record list."""

    normalized_records = [normalize_decision_record(existing) for existing in records]
    normalized_records.append(normalize_decision_record(record, **kwargs))
    return _sort_records(normalized_records)


def build_operator_decision_ledger(
    records: Iterable[Mapping[str, Any]],
    *,
    ledger_id: str | None = None,
    created_at: str | None = None,
) -> OperatorDecisionLedger:
    normalized_records = _sort_records(normalize_decision_record(record) for record in records)
    safety_flags = sorted({flag for record in normalized_records for flag in record.get("safety_flags", [])})
    for flag in _DEFAULT_SAFETY_FLAGS:
        if flag not in safety_flags:
            safety_flags.append(flag)
    return OperatorDecisionLedger(
        mode=MODE,
        status="ok",
        ledger_id=ledger_id or f"operator-decision-ledger-v1-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        created_at=created_at or utc_timestamp(),
        behavior=BEHAVIOR,
        live_mutation_authorized=False,
        approval_manifest_created=False,
        targets=[],
        reason_codes=list(DEFAULT_REASON_CODES),
        safety_flags=sorted(safety_flags),
        records=normalized_records,
    )


def serialize_operator_decision_ledger(ledger: OperatorDecisionLedger | Mapping[str, Any]) -> str:
    data = ledger.to_dict() if isinstance(ledger, OperatorDecisionLedger) else _normalize_mapping(ledger)
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def write_operator_decision_ledger(
    records: Iterable[Mapping[str, Any]],
    *,
    out_path: str | Path,
    ledger_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, str]:
    ledger = build_operator_decision_ledger(records, ledger_id=ledger_id, created_at=created_at)
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_operator_decision_ledger(ledger), encoding="utf-8")
    return {"status": "ok", "ledger": str(path)}


def _sort_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda item: (
            str(item.get("created_at", "")),
            str(item.get("decision_id", "")),
            str(item.get("decision_type", "")),
        ),
    )


def _normalize_flags(flags: Iterable[str]) -> list[str]:
    found = {str(flag).strip() for flag in flags if str(flag).strip()}
    found.update(_DEFAULT_SAFETY_FLAGS)
    return sorted(found)


def _normalize_refs(refs: Iterable[Any] | Any) -> list[Any]:
    if refs is None:
        return []
    if isinstance(refs, (str, bytes)) or not isinstance(refs, Iterable):
        refs = [refs]
    normalized = [_normalize_jsonable(ref) for ref in refs]
    return sorted(_dedupe(normalized), key=_stable_key)


def _dedupe(items: Iterable[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for item in items:
        key = _stable_key(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _normalize_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _normalize_jsonable(value[key]) for key in sorted(value, key=str)}


def _normalize_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _normalize_mapping(value)
    if isinstance(value, set):
        return sorted((_normalize_jsonable(item) for item in value), key=_stable_key)
    if isinstance(value, (list, tuple)):
        return [_normalize_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _stable_key(value: Any) -> str:
    return json.dumps(_normalize_jsonable(value), sort_keys=True, separators=(",", ":"))


def _non_empty(*values: Any, default: str) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return default


def _default_decision_id(decision_type: str, created_at: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", decision_type.casefold()).strip("-") or "operator-decision"
    compact_time = re.sub(r"[^0-9TZ]", "", created_at)
    return f"{slug}-{compact_time}"
