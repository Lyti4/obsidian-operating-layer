from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .guardrails import GuardrailError

DEFAULT_MIN_AVAILABLE_MB = 1024
DEFAULT_MAX_SWAP_USED_MB = 512
DEFAULT_MAX_LOAD_PER_CPU = 1.25
DEFAULT_MAX_SWAP_IO_PAGES_PER_SEC = 20


@dataclass(frozen=True)
class ResourcePreflightReport:
    status: str
    mem_available_mb: int
    swap_total_mb: int
    swap_used_mb: int
    load1: float
    load5: float
    cpu_count: int
    swap_in_pages_per_sec: float
    swap_out_pages_per_sec: float
    thresholds: dict[str, float | int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_meminfo(path: str | Path = "/proc/meminfo") -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(":"):
            values[parts[0][:-1]] = int(parts[1])
    return values


def _read_vmstat(path: str | Path = "/proc/vmstat") -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] in {"pswpin", "pswpout"}:
            values[parts[0]] = int(parts[1])
    return values


def _swap_io_rates(interval_seconds: float) -> tuple[float, float]:
    if interval_seconds <= 0:
        return 0.0, 0.0
    before = _read_vmstat()
    time.sleep(interval_seconds)
    after = _read_vmstat()
    return (
        max(0.0, (after.get("pswpin", 0) - before.get("pswpin", 0)) / interval_seconds),
        max(0.0, (after.get("pswpout", 0) - before.get("pswpout", 0)) / interval_seconds),
    )


def collect_resource_preflight(
    *,
    min_available_mb: int = DEFAULT_MIN_AVAILABLE_MB,
    max_swap_used_mb: int = DEFAULT_MAX_SWAP_USED_MB,
    max_load_per_cpu: float = DEFAULT_MAX_LOAD_PER_CPU,
    max_swap_io_pages_per_sec: int = DEFAULT_MAX_SWAP_IO_PAGES_PER_SEC,
    sample_seconds: float = 1.0,
) -> ResourcePreflightReport:
    meminfo = _read_meminfo()
    mem_available_mb = meminfo.get("MemAvailable", 0) // 1024
    swap_total_mb = meminfo.get("SwapTotal", 0) // 1024
    swap_free_mb = meminfo.get("SwapFree", 0) // 1024
    swap_used_mb = max(0, swap_total_mb - swap_free_mb)
    load1, load5, _load15 = os.getloadavg()
    cpu_count = os.cpu_count() or 1
    swap_in_rate, swap_out_rate = _swap_io_rates(sample_seconds)
    thresholds: dict[str, float | int] = {
        "min_available_mb": min_available_mb,
        "max_swap_used_mb": max_swap_used_mb,
        "max_load_per_cpu": max_load_per_cpu,
        "max_load5": round(cpu_count * max_load_per_cpu, 2),
        "max_swap_io_pages_per_sec": max_swap_io_pages_per_sec,
    }
    report = ResourcePreflightReport(
        status="ok",
        mem_available_mb=mem_available_mb,
        swap_total_mb=swap_total_mb,
        swap_used_mb=swap_used_mb,
        load1=round(load1, 2),
        load5=round(load5, 2),
        cpu_count=cpu_count,
        swap_in_pages_per_sec=round(swap_in_rate, 2),
        swap_out_pages_per_sec=round(swap_out_rate, 2),
        thresholds=thresholds,
    )
    failures: list[str] = []
    if mem_available_mb < min_available_mb:
        failures.append(f"MemAvailable {mem_available_mb}MB < {min_available_mb}MB")
    if swap_used_mb > max_swap_used_mb:
        failures.append(f"SwapUsed {swap_used_mb}MB > {max_swap_used_mb}MB")
    if load5 > cpu_count * max_load_per_cpu:
        failures.append(f"load5 {load5:.2f} > {cpu_count * max_load_per_cpu:.2f}")
    if swap_in_rate > max_swap_io_pages_per_sec or swap_out_rate > max_swap_io_pages_per_sec:
        failures.append(
            f"active swap I/O pswpin={swap_in_rate:.2f}/s pswpout={swap_out_rate:.2f}/s > {max_swap_io_pages_per_sec}/s"
        )
    if failures:
        raise GuardrailError("Resource preflight failed: " + "; ".join(failures))
    return report
