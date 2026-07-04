#!/usr/bin/env python3
"""Run the Nanobot read-only evidence gateway."""
from __future__ import annotations

from _bootstrap import SRC  # noqa: F401

from obslayer.nanobot_readonly_evidence_gateway import main

if __name__ == "__main__":
    raise SystemExit(main())
