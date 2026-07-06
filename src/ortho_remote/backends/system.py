"""macOS system volume backend."""

import subprocess


def set_system_volume(target_volume: int) -> None:
    """Set macOS system output volume (0-100)."""
    clamped = max(0, min(100, int(target_volume)))
    subprocess.run(
        ["osascript", "-e", f"set volume output volume {clamped}"],
        capture_output=True,
        text=True,
    )
