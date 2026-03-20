#!/usr/bin/env python3
"""Compatibility entrypoint for local/dev/Render start commands."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bot import main


if __name__ == "__main__":
    main()
