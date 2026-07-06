#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass


def _run(cmd: list[str], *, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, input=input_text, text=True, capture_output=True)


@dataclass(frozen=True)
class SwapDrainReport:
    status: str
    before_mem_available_mb: int
    before_swap_total_mb: int
    before_swap_used_mb: int
    after_mem_available_mb: int
    after_swap_total_mb: int
    after_swap_used_mb: int
    min_post_drain_available_mb: int
    actions: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _mem_state() -> tuple[int, int, int]:
    values: dict[str, int] = {}
    with open('/proc/meminfo', encoding='utf-8') as handle:
        for line in handle:
            parts = line.split()
            if len(parts) >= 2 and parts[0].endswith(':'):
                values[parts[0][:-1]] = int(parts[1]) // 1024
    swap_total = values.get('SwapTotal', 0)
    swap_free = values.get('SwapFree', 0)
    return values.get('MemAvailable', 0), swap_total, max(0, swap_total - swap_free)


def _start_swap_units() -> None:
    # zram on this host is not in /etc/fstab, so swapon -a alone does not restore it.
    _run(['sudo', 'swapon', '-a'], check=False)
    units = _run(['systemctl', 'list-units', '--type=service', '--all', '--no-legend'], check=False).stdout
    if 'systemd-zram-setup@zram0.service' in units:
        _run(['sudo', 'systemctl', 'start', 'systemd-zram-setup@zram0.service'], check=False)
    swaps = _run(['systemctl', 'list-units', '--type=swap', '--all', '--no-legend'], check=False).stdout
    if 'dev-zram0.swap' in swaps:
        _run(['sudo', 'systemctl', 'start', 'dev-zram0.swap'], check=False)


def drain_swap(*, min_post_drain_available_mb: int, drop_caches: bool) -> SwapDrainReport:
    actions: list[str] = []
    before_avail, before_total, before_used = _mem_state()
    if before_used == 0:
        return SwapDrainReport(
            'ok-already-empty',
            before_avail,
            before_total,
            before_used,
            before_avail,
            before_total,
            before_used,
            min_post_drain_available_mb,
            actions,
        )

    if drop_caches:
        _run(['sync'])
        _run(['sudo', 'tee', '/proc/sys/vm/drop_caches'], input_text='3\n')
        actions.append('drop_caches')

    avail, _total, used = _mem_state()
    projected_available = avail - used
    if projected_available < min_post_drain_available_mb:
        raise RuntimeError(
            f'Unsafe to drain swap: projected MemAvailable after swapoff is {projected_available}MB '
            f'< {min_post_drain_available_mb}MB (available={avail}MB swap_used={used}MB)'
        )

    swapoff_done = False
    try:
        _run(['sudo', 'swapoff', '-a'])
        swapoff_done = True
        actions.append('swapoff')
    finally:
        if swapoff_done:
            _start_swap_units()
            actions.append('swap_restore')

    after_avail, after_total, after_used = _mem_state()
    if before_total > 0 and after_total <= 0:
        raise RuntimeError('Swap drain left the system without swap configured')
    if after_used > 0:
        raise RuntimeError(f'Swap drain did not clear swap usage: after_swap_used_mb={after_used}')
    return SwapDrainReport(
        'ok',
        before_avail,
        before_total,
        before_used,
        after_avail,
        after_total,
        after_used,
        min_post_drain_available_mb,
        actions,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description='Safely drain used swap before bounded embedding runs, then restore swap/zram.')
    parser.add_argument('--min-post-drain-available-mb', type=int, default=256)
    parser.add_argument('--no-drop-caches', action='store_true')
    args = parser.parse_args()
    report = drain_swap(
        min_post_drain_available_mb=args.min_post_drain_available_mb,
        drop_caches=not args.no_drop_caches,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(2)
