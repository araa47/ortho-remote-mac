"""macOS system volume backend."""

import osascript


def set_system_volume(target_volume: int) -> None:
    """Set macOS system output volume (0-100)."""
    clamped = max(0, min(100, int(target_volume)))
    osascript.run(f"set volume output volume {clamped}")
