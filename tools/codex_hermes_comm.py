#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

HOME = Path('/home/hermesadmin')
REPO = HOME / 'work' / 'obsidian-operating-layer'
COMM = HOME / '.codex-hermes' / 'comm'
CODEX_INBOX = COMM / 'codex-inbox'       # Hermes -> Codex
HERMES_INBOX = COMM / 'hermes-inbox'     # Codex -> Hermes
STATE_DIR = COMM / 'state'
PROCESSING_DIR = COMM / 'processing'
DONE_DIR = COMM / 'done'
FAILED_DIR = COMM / 'failed'
PROCESSED_PATH = STATE_DIR / 'processed.json'
ROLE_POLICY = HOME / '.codex-hermes' / 'docs' / 'ROLE_POLICY.json'

SECRET_PATTERNS = [
    (re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]+=*"), 'Bearer [REDACTED]'),
    (re.compile(r"(access_token|refresh_token|id_token|api_key|secret)([\"'\s:=]+)([^\s\"']+)", re.I), r'\1\2[REDACTED]'),
    (re.compile(r"sk-[A-Za-z0-9_-]{16,}"), 'sk-[REDACTED]'),
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"), 'gh[REDACTED]'),
]
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def safe_id(value: str | None, fallback: str) -> str:
    candidate = value or fallback
    if not SAFE_ID.fullmatch(candidate):
        raise ValueError("id must match [A-Za-z0-9][A-Za-z0-9._-]{0,127}")
    return candidate


def safe_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise ValueError(f"refusing to write through symlink: {path}")
    tmp = path.with_name(f".{path.name}.{stamp()}.tmp")
    tmp.write_text(text, encoding='utf-8')
    tmp.replace(path)


def sanitize(text: object) -> str:
    value = str(text)
    for pattern, repl in SECRET_PATTERNS:
        value = pattern.sub(repl, value)
    return value


def stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def ensure_dirs() -> None:
    for path in [CODEX_INBOX, HERMES_INBOX, STATE_DIR, PROCESSING_DIR, DONE_DIR, FAILED_DIR, ROLE_POLICY.parent]:
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path} must contain a JSON object')
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    safe_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + '\n')


def digest(path: Path) -> str:
    h = hashlib.sha256()
    h.update(str(path).encode('utf-8'))
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def load_state() -> dict[str, Any]:
    ensure_dirs()
    if PROCESSED_PATH.exists():
        try:
            data = load_json(PROCESSED_PATH)
            data.setdefault('processed', {})
            return data
        except Exception:
            pass
    return {'version': 1, 'processed': {}}


def save_state(state: dict[str, Any]) -> None:
    tmp = PROCESSED_PATH.with_suffix('.json.tmp')
    write_json(tmp, state)
    tmp.replace(PROCESSED_PATH)


def default_rights(task_type: str) -> dict[str, Any]:
    review_only = task_type in {'review', 'audit', 'plan-review'}
    return {
        'repo_read': True,
        'repo_write': not review_only,
        'repo_write_boundary': (
            'Only inside /home/hermesadmin/work/obsidian-operating-layer '
            'and only files needed for the task.'
            if not review_only
            else 'Forbidden for review-only task.'
        ),
        'live_vault_mutation': False,
        'auth_profile_mutation': False,
        'service_restart_deploy_cron_network': False,
        'secrets_policy': 'Do not print/store secrets. Redact tokens/cookies/private keys/env values.',
        'approval_required_for': [
            'live vault mutation',
            'auth/profile changes',
            'service restart/deploy/cron/network exposure',
            'public posting',
            'paid actions',
        ],
    }


def create_task(args: argparse.Namespace) -> Path:
    ensure_dirs()
    created = stamp()
    task_id = safe_id(args.id, f'codex-task-{created}')
    task_type = args.type
    scope = args.scope or str(REPO)
    scope_text = sanitize(scope)
    rights = default_rights(task_type)
    if args.review_only:
        rights = default_rights('review')
    payload = {
        'schema': 'codex_task.v1',
        'task_id': task_id,
        'id': task_id,
        'created_at': created,
        'from': 'hermes',
        'to': 'codex',
        'channel': 'codex-hermes-internal-server',
        'mode': task_type,
        'type': task_type,
        'repo': str(REPO),
        'objective': sanitize(args.instructions.splitlines()[0] if args.instructions else task_type),
        'scope': {
            'allowed_paths': [scope_text],
            'forbidden_paths': ['.env', '.env.*', '.obsidian', '_Backups', '_Archive', '.trash'],
        },
        'scope_text': scope_text,
        'role_policy': str(ROLE_POLICY),
        'rights': rights,
        'instructions': [sanitize(args.instructions)],
        'verification': {
            'required': ['git diff --check'],
            'if_code_changed': ['make verify'],
        },
        'outputs': {
            'json_report': f'~/.codex-hermes/comm/hermes-inbox/{task_id}.report.json',
            'markdown_report': f'out/reports/codex/{task_id}.md',
        },
        'deliverables': [
            'Write codex_report.v1 JSON to ~/.codex-hermes/comm/hermes-inbox/<task_id>.report.json.',
            'Optionally write Markdown to out/reports/codex/<task_id>.md.',
            'Include status, summary, changed_files, tests, blockers, and exact commands run.',
            'Do not claim success unless tests/verification actually ran.',
        ],
        'acceptance_owner': 'Hermes',
        'safety': 'Bounded Codex task packet. No live vault/auth/service/cron/network mutation without explicit user approval.',
    }
    json_path = CODEX_INBOX / f'{task_id}.json'
    md_path = CODEX_INBOX / f'{task_id}.md'
    write_json(json_path, payload)
    safe_write_text(
        md_path,
        f"# Hermes -> Codex task {task_id}\n\n"
        f"Type: `{task_type}`\n\nScope: `{scope_text}`\n\n"
        f"Role policy: `{ROLE_POLICY}`\n\n"
        "## Rights\n\n"
        + '\n'.join(f'- `{k}`: `{v}`' for k, v in rights.items())
        + "\n\n## Instructions\n\n"
        + sanitize(args.instructions)
        + "\n\n## Deliverables\n\n"
        + '\n'.join(f'- {x}' for x in payload['deliverables'])
        + "\n"
    )
    safe_write_text(CODEX_INBOX / 'latest.json', json_path.read_text(encoding='utf-8'))
    safe_write_text(CODEX_INBOX / 'latest.md', md_path.read_text(encoding='utf-8'))
    print(json.dumps({'status': 'ok', 'task_id': task_id, 'json': str(json_path), 'md': str(md_path)}, ensure_ascii=False))
    return json_path


def classify_report(payload: dict[str, Any]) -> tuple[str, list[str]]:
    status = sanitize(payload.get('status', 'unknown')).lower()
    blockers = payload.get('blockers') or []
    changed = payload.get('changed_files') or []
    tests = payload.get('tests') or []
    if blockers or status in {'blocked', 'failed', 'error'}:
        action = 'ack_blocked_or_failed'
        reply = [
            'ACK: Hermes heard Codex blocker/failure report.',
            'Codex: do not broaden scope or mutate gated surfaces. Wait for Hermes triage or provide one smaller proposal-only next step.',
        ]
    elif changed:
        action = 'ack_changes_pending_hermes_verification'
        reply = [
            'ACK: Hermes heard Codex implementation report.',
            'Hermes will verify changed files and tests before accepting. Codex must not apply outside the dispatched repo scope.',
        ]
    elif tests:
        action = 'ack_review_or_test_report'
        reply = [
            'ACK: Hermes heard Codex review/test report.',
            'Codex: keep further output evidence-backed and scoped to the task packet.',
        ]
    else:
        action = 'ack_report_received'
        reply = [
            'ACK: Hermes heard Codex report.',
            'Codex: include changed_files/tests/blockers in the next report if any action was taken.',
        ]
    return action, reply


def write_ack(source_path: Path, payload: dict[str, Any], source_hash: str) -> Path:
    ensure_dirs()
    created = stamp()
    task_id = sanitize(payload.get('task_id', payload.get('id', 'unknown')))
    action, reply = classify_report(payload)
    ack = {
        'id': f'ack-{created}-{source_hash}',
        'created_at': created,
        'from': 'hermes',
        'to': 'codex',
        'channel': 'codex-hermes-internal-server',
        'ack_for': str(source_path),
        'ack_hash': source_hash,
        'task_id': task_id,
        'action': action,
        'reply': reply,
        'safety': 'Hermes ACK only; no live apply; no user Telegram delivery; rights remain bound by ROLE_POLICY.',
    }
    json_path = CODEX_INBOX / f'{ack["id"]}.json'
    md_path = CODEX_INBOX / f'{ack["id"]}.md'
    write_json(json_path, ack)
    safe_write_text(
        md_path,
        f"# Hermes -> Codex ACK {ack['id']}\n\n"
        f"ACK for: `{source_path}`\n\nAction: `{action}`\n\n"
        + '\n'.join(f'- {line}' for line in reply)
        + "\n\nSafety: Hermes ACK only; rights remain bound by role policy.\n"
    )
    safe_write_text(CODEX_INBOX / 'latest.json', json_path.read_text(encoding='utf-8'))
    safe_write_text(CODEX_INBOX / 'latest.md', md_path.read_text(encoding='utf-8'))
    return json_path


def process_reports(limit: int = 20) -> int:
    ensure_dirs()
    state = load_state()
    processed = state.setdefault('processed', {})
    candidates = sorted(
        [p for p in HERMES_INBOX.glob('*.json') if p.name != 'latest.json'],
        key=lambda p: p.stat().st_mtime,
    )
    new_count = 0
    for path in candidates:
        h = digest(path)
        key = str(path)
        if processed.get(key) == h:
            continue
        try:
            payload = load_json(path)
        except Exception as exc:
            payload = {
                'id': path.stem,
                'from': 'codex',
                'to': 'hermes',
                'task_id': 'unknown',
                'status': 'parse-error',
                'summary': f'Could not parse {path.name}: {type(exc).__name__}: {sanitize(exc)}',
                'changed_files': [],
                'tests': [],
                'blockers': [f'parse-error: {path.name}'],
            }
        ack_path = write_ack(path, payload, h)
        processed[key] = h
        state['last_heard_at'] = stamp()
        state['last_source'] = str(path)
        state['last_ack'] = str(ack_path)
        new_count += 1
        if new_count >= limit:
            break
    save_state(state)
    print(json.dumps({'status': 'ok', 'new_reports': new_count, 'last_ack': state.get('last_ack')}, ensure_ascii=False))
    return 0


def write_report(args: argparse.Namespace) -> Path:
    ensure_dirs()
    created = stamp()
    report_id = safe_id(args.id, f'codex-report-{created}')
    changed = [sanitize(x) for x in args.changed_file]
    tests = [sanitize(x) for x in args.test]
    blockers = [sanitize(x) for x in args.blocker]
    payload = {
        'schema': 'codex_report.v1',
        'id': report_id,
        'created_at': created,
        'from': 'codex',
        'to': 'hermes',
        'channel': 'codex-hermes-internal-server',
        'task_id': sanitize(args.task_id),
        'status': sanitize(args.status),
        'mode': sanitize(args.mode),
        'summary': sanitize(args.summary),
        'changed_files': changed,
        'tests': tests,
        'commands_run': tests,
        'blockers': blockers,
        'verification': {'passed': bool(tests) and not blockers, 'notes': []},
        'safety': 'Codex report only; Hermes must verify before acceptance.',
    }
    task_slug = safe_id(args.task_id, report_id)
    json_path = HERMES_INBOX / f'{task_slug}.report.json'
    md_path = HERMES_INBOX / f'{task_slug}.report.md'
    write_json(json_path, payload)
    safe_write_text(
        md_path,
        f"# Codex -> Hermes report {report_id}\n\n"
        f"Task: `{payload['task_id']}`\n\nStatus: `{payload['status']}`\n\n"
        f"Summary: {payload['summary']}\n\n"
        "## Changed files\n" + ''.join(f"- `{x}`\n" for x in changed)
        + "\n## Tests\n" + ''.join(f"- `{x}`\n" for x in tests)
        + "\n## Blockers\n" + ''.join(f"- `{x}`\n" for x in blockers)
        + "\nSafety: Codex report only; Hermes must verify before acceptance.\n"
    )
    safe_write_text(HERMES_INBOX / 'latest.json', json_path.read_text(encoding='utf-8'))
    safe_write_text(HERMES_INBOX / 'latest.md', md_path.read_text(encoding='utf-8'))
    print(json.dumps({'status': 'ok', 'report_id': report_id, 'json': str(json_path), 'md': str(md_path)}, ensure_ascii=False))
    return json_path



def selftest() -> int:
    ensure_dirs()
    policy_ok = ROLE_POLICY.exists()
    required = [CODEX_INBOX, HERMES_INBOX, STATE_DIR, PROCESSING_DIR, DONE_DIR, FAILED_DIR]
    payload = {
        'status': 'ok' if policy_ok and all(p.exists() for p in required) else 'blocked',
        'channel': 'codex-hermes-internal-server',
        'paths': {
            'codex_inbox': str(CODEX_INBOX),
            'hermes_inbox': str(HERMES_INBOX),
            'state_dir': str(STATE_DIR),
            'processing_dir': str(PROCESSING_DIR),
            'done_dir': str(DONE_DIR),
            'failed_dir': str(FAILED_DIR),
            'role_policy': str(ROLE_POLICY),
        },
        'checks': {
            'codex_inbox_exists': CODEX_INBOX.exists(),
            'hermes_inbox_exists': HERMES_INBOX.exists(),
            'state_dir_exists': STATE_DIR.exists(),
            'processing_dir_exists': PROCESSING_DIR.exists(),
            'done_dir_exists': DONE_DIR.exists(),
            'failed_dir_exists': FAILED_DIR.exists(),
            'role_policy_exists': policy_ok,
        },
        'rights_summary': {
            'repo_write': 'task-scoped only',
            'live_vault_mutation': False,
            'auth_profile_mutation': False,
            'service_restart_deploy_cron_network': False,
            'secrets': 'redact/no-print',
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Codex ⇄ Hermes local communication channel helper')
    sub = parser.add_subparsers(dest='cmd', required=True)

    t = sub.add_parser('task', help='Write Hermes -> Codex task packet')
    t.add_argument('--id')
    t.add_argument('--type', default='implementation', choices=['implementation', 'review', 'audit', 'plan-review'])
    t.add_argument('--scope')
    t.add_argument('--instructions', required=True)
    t.add_argument('--review-only', action='store_true')

    r = sub.add_parser('report', help='Write Codex -> Hermes report packet')
    r.add_argument('--id')
    r.add_argument('--task-id', required=True)
    r.add_argument('--status', default='ok')
    r.add_argument('--mode', default='implementation', choices=['implementation', 'review', 'audit', 'plan-review'])
    r.add_argument('--summary', required=True)
    r.add_argument('--changed-file', action='append', default=[])
    r.add_argument('--test', action='append', default=[])
    r.add_argument('--blocker', action='append', default=[])

    w = sub.add_parser('watch', help='Process Codex -> Hermes reports and ACK them')
    w.add_argument('--limit', type=int, default=20)

    sub.add_parser('selftest', help='Check channel paths and rights summary without reading secrets')

    args = parser.parse_args()
    if args.cmd == 'task':
        create_task(args)
        return 0
    if args.cmd == 'report':
        write_report(args)
        return 0
    if args.cmd == 'watch':
        return process_reports(limit=args.limit)
    if args.cmd == 'selftest':
        return selftest()
    raise AssertionError(args.cmd)


if __name__ == '__main__':
    raise SystemExit(main())
