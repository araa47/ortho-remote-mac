"""Compatibility shim for legacy imports."""

# ruff: noqa: E402

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ortho_remote.backends.soundsource import (  # noqa: F401
    SOUNDSOURCE_SOURCES_PLIST,
    get_soundsource_volume,
    set_volume_precise,
    sync_with_soundsource,
)
