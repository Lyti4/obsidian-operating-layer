from __future__ import annotations

import pytest

from obslayer import GuardrailError
from obslayer.resource_preflight import collect_resource_preflight


def test_resource_preflight_passes_clean_state(monkeypatch: pytest.MonkeyPatch) -> None:
    from obslayer import resource_preflight as preflight

    monkeypatch.setattr(preflight, "_read_meminfo", lambda: {"MemAvailable": 2_000_000, "SwapTotal": 2_000_000, "SwapFree": 1_900_000})
    monkeypatch.setattr(preflight, "_swap_io_rates", lambda _seconds: (0.0, 0.0))
    monkeypatch.setattr(preflight.os, "getloadavg", lambda: (0.4, 0.5, 0.6))
    monkeypatch.setattr(preflight.os, "cpu_count", lambda: 2)

    report = collect_resource_preflight(sample_seconds=0)

    assert report.status == "ok"
    assert report.mem_available_mb == 1953
    assert report.swap_used_mb == 98


def test_resource_preflight_fails_dirty_swap(monkeypatch: pytest.MonkeyPatch) -> None:
    from obslayer import resource_preflight as preflight

    monkeypatch.setattr(preflight, "_read_meminfo", lambda: {"MemAvailable": 2_000_000, "SwapTotal": 2_000_000, "SwapFree": 500_000})
    monkeypatch.setattr(preflight, "_swap_io_rates", lambda _seconds: (0.0, 0.0))
    monkeypatch.setattr(preflight.os, "getloadavg", lambda: (0.4, 0.5, 0.6))
    monkeypatch.setattr(preflight.os, "cpu_count", lambda: 2)

    with pytest.raises(GuardrailError, match="SwapUsed"):
        collect_resource_preflight(sample_seconds=0)


def test_resource_preflight_fails_active_swap_io(monkeypatch: pytest.MonkeyPatch) -> None:
    from obslayer import resource_preflight as preflight

    monkeypatch.setattr(preflight, "_read_meminfo", lambda: {"MemAvailable": 2_000_000, "SwapTotal": 2_000_000, "SwapFree": 1_900_000})
    monkeypatch.setattr(preflight, "_swap_io_rates", lambda _seconds: (0.0, 25.0))
    monkeypatch.setattr(preflight.os, "getloadavg", lambda: (0.4, 0.5, 0.6))
    monkeypatch.setattr(preflight.os, "cpu_count", lambda: 2)

    with pytest.raises(GuardrailError, match="active swap I/O"):
        collect_resource_preflight(sample_seconds=0)
