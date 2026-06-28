#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent
    tools_dir = project_root / "tools"
    tool_path = tools_dir / "obsidian_controlled_autonomy.py"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    runpy.run_path(str(tool_path), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
