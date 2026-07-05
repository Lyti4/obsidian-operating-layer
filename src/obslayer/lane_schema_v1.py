from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from obslayer.archive_shadow_index import build_archive_shadow_index
from obslayer.candidate_scorer_v1 import score_candidate as _score_candidate_v1


@dataclass(frozen=True)
class LaneSchemaPacket:
    mode: str
    status: str
    packet_id: str
    source_actionable_lanes: str
    source_notes_index: str
    source_wikilinks: str
    live_mutation_authorized: bool
    approval_manifest_created: bool
    targets: list[dict[str, Any]]
    approval_classes: list[str]
    forbidden_actions: list[str]
    reason_codes: list[str]
    archive_shadow_index: dict[str, Any]
    candidate_scorer: dict[str, Any]
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _is_archive_record(record: dict[str, Any] | None) -> bool:
    if not record:
        return False
    path = str(record.get("path", ""))
    return bool(
        record.get("protected_or_archive_surface")
        or record.get("top") in {"_Backups", "_Archive", ".trash"}
        or path.startswith(("_Backups/", "_Archive/", ".trash/"))
    )


def score_candidate(
    *,
    link: dict[str, Any],
    notes_by_path: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return _score_candidate_v1(link=link, notes_by_path=notes_by_path)


def _archive_shadow_index(notes: list[dict[str, Any]]) -> dict[str, Any]:
    return build_archive_shadow_index(notes)


def build_lane_schema_packet(
    *,
    actionable_lanes_json: str | Path,
    notes_index_jsonl: str | Path,
    wikilinks_jsonl: str | Path,
    packet_id: str | None = None,
    created_at: str | None = None,
) -> LaneSchemaPacket:
    lanes = _read_json(actionable_lanes_json)
    notes = _read_jsonl(notes_index_jsonl)
    wikilinks = _read_jsonl(wikilinks_jsonl)
    notes_by_path = {str(note.get("path", "")): note for note in notes}

    approval_classes = {"shadow_index_evidence_only"}
    forbidden_actions = {"live_vault_mutation", "approval_manifest_creation"}
    reason_codes = {"archive_shadow_evidence_only"}
    for lane in lanes.get("next_lanes") or []:
        if not isinstance(lane, dict):
            continue
        if lane.get("approval_class"):
            approval_classes.add(str(lane["approval_class"]))
        forbidden_actions.update(str(item) for item in lane.get("forbidden_actions") or [])
        reason_codes.update(str(item) for item in lane.get("reason_codes") or [])

    scored_links = [
        score_candidate(link=link, notes_by_path=notes_by_path)
        for link in wikilinks
        if (link.get("candidates") or [])
    ]
    candidate_scorer = (
        scored_links[0]
        if scored_links
        else score_candidate(link={"source": "", "status": "no_candidates", "candidates": []}, notes_by_path={})
    )

    packet = LaneSchemaPacket(
        mode="lane-schema-v1",
        status="ok",
        packet_id=packet_id or f"lane-schema-v1-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        source_actionable_lanes=str(Path(actionable_lanes_json)),
        source_notes_index=str(Path(notes_index_jsonl)),
        source_wikilinks=str(Path(wikilinks_jsonl)),
        live_mutation_authorized=False,
        approval_manifest_created=False,
        targets=[],
        approval_classes=sorted(approval_classes),
        forbidden_actions=sorted(forbidden_actions),
        reason_codes=sorted(reason_codes),
        archive_shadow_index=_archive_shadow_index(notes),
        candidate_scorer=candidate_scorer,
        created_at=created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    return packet


def lane_schema_packet_to_markdown(packet: LaneSchemaPacket) -> str:
    data = packet.to_dict()
    lines = [
        "# Lane schema v1 packet",
        "",
        f"Packet id: `{packet.packet_id}`",
        f"Created at: `{packet.created_at or 'unknown'}`",
        f"Status: `{packet.status}`",
        "",
        "## Safety",
        "",
        f"- live_mutation_authorized: `{packet.live_mutation_authorized}`",
        f"- approval_manifest_created: `{packet.approval_manifest_created}`",
        f"- targets: `{len(packet.targets)}`",
        "",
        "## Evidence",
        "",
        f"- archive_shadow_entries: `{len(packet.archive_shadow_index.get('entries', []))}`",
        f"- candidate_count: `{len(packet.candidate_scorer.get('candidates', []))}`",
        f"- top_two_gap: `{packet.candidate_scorer.get('top_two_gap', 0)}`",
        "",
        "## Machine Fields",
        "",
    ]
    for key in ("approval_classes", "forbidden_actions", "reason_codes"):
        lines.append(f"- {key}: `{', '.join(data[key])}`")
    lines.append("")
    return "\n".join(lines)


def write_lane_schema_packet(
    *,
    actionable_lanes_json: str | Path,
    notes_index_jsonl: str | Path,
    wikilinks_jsonl: str | Path,
    out_dir: str | Path,
    packet_id: str | None = None,
) -> dict[str, str]:
    packet = build_lane_schema_packet(
        actionable_lanes_json=actionable_lanes_json,
        notes_index_jsonl=notes_index_jsonl,
        wikilinks_jsonl=wikilinks_jsonl,
        packet_id=packet_id,
    )
    packet_dir = Path(out_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_path = packet_dir / "lane-schema-packet.json"
    report_path = packet_dir / "REPORT.md"
    packet_path.write_text(json.dumps(packet.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(lane_schema_packet_to_markdown(packet), encoding="utf-8")
    return {"status": "ok", "packet": str(packet_path), "report": str(report_path)}
