"""SoundSource volume backend."""

import os
import plistlib
import time

import Quartz

try:
    from ortho_remote_rs import VolumeCoalescer  # ty: ignore[unresolved-import]
except Exception:
    VolumeCoalescer = None

SOUNDSOURCE_SOURCES_PLIST = os.path.expanduser(
    "~/Library/Application Support/SoundSource/Sources.plist"
)

VOLUME_STEP = 6.25
STEP_DELAY_SECONDS = float(os.getenv("ORTHO_SOUNDSOURCE_STEP_DELAY", "0.03"))
MAX_STEPS_PER_CALL = int(os.getenv("ORTHO_SOUNDSOURCE_MAX_STEPS", "8"))

_cached_volume = None
_last_plist_read = 0
PLIST_CACHE_SECONDS = 1.0
_rust_coalescer = None


def get_soundsource_volume(force_refresh: bool = False) -> int:
    """Read current SoundSource output volume (0-100)."""
    global _cached_volume, _last_plist_read

    current_time = time.time()
    if not force_refresh and _cached_volume is not None:
        if current_time - _last_plist_read < PLIST_CACHE_SECONDS:
            return _cached_volume

    try:
        with open(SOUNDSOURCE_SOURCES_PLIST, "rb") as f:
            plist_data = plistlib.load(f)

        model_items = plist_data.get("modelItems", [])
        for item in model_items:
            if (
                item.get("sourceName") == "Output"
                and item.get("uuid") == "SystemOutputUUID"
            ):
                volume_props = item.get("volumeProperties", {})
                volume_decimal = volume_props.get("volume", 0.5)
                volume = int(volume_decimal * 100)
                _cached_volume = volume
                _last_plist_read = current_time
                return volume
        return 50
    except Exception:
        return _cached_volume if _cached_volume is not None else 50


def send_volume_key(key_type: int) -> None:
    """Send native volume key event (0=up, 1=down)."""
    event_down = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(  # ty: ignore[unresolved-attribute]
        Quartz.NSSystemDefined,  # ty: ignore[unresolved-attribute]
        (0, 0),
        0xA00,
        0,
        0,
        0,
        8,
        (key_type << 16) | (0xA << 8),
        -1,
    )

    event_up = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(  # ty: ignore[unresolved-attribute]
        Quartz.NSSystemDefined,  # ty: ignore[unresolved-attribute]
        (0, 0),
        0xB00,
        0,
        0,
        0,
        8,
        (key_type << 16) | (0xB << 8),
        -1,
    )

    Quartz.CGEventPost(0, event_down.CGEvent())  # ty: ignore[unresolved-attribute]
    Quartz.CGEventPost(0, event_up.CGEvent())  # ty: ignore[unresolved-attribute]


def set_volume_precise(target_volume: int, logger=None) -> None:
    """Set SoundSource output volume to target level (0-100)."""
    global _cached_volume, _rust_coalescer

    target_volume = max(0, min(100, int(target_volume)))
    current = _cached_volume if _cached_volume is not None else get_soundsource_volume()

    if logger:
        logger.debug(f"Current volume: {current}%, Target: {target_volume}%")

    if VolumeCoalescer is not None:
        if _rust_coalescer is None:
            try:
                _rust_coalescer = VolumeCoalescer(
                    current, VOLUME_STEP, MAX_STEPS_PER_CALL
                )
            except Exception:
                _rust_coalescer = None
        if _rust_coalescer is not None:
            _rust_coalescer.reset_current(current)
            _rust_coalescer.update_target(target_volume)
            action = _rust_coalescer.next_action()
            if action is None:
                return
            key_type, steps, estimated = action
            for _ in range(steps):
                send_volume_key(key_type)
                time.sleep(STEP_DELAY_SECONDS)
            _cached_volume = int(estimated)
            if logger:
                logger.debug(
                    f"Rust planner sent {steps} key presses, estimated new volume: {_cached_volume}%"
                )
            return

    diff = target_volume - current
    if abs(diff) < VOLUME_STEP / 2:
        return

    steps = round(abs(diff) / VOLUME_STEP)
    if steps == 0 and abs(diff) >= 1:
        steps = 1
    steps = min(steps, MAX_STEPS_PER_CALL)
    if steps == 0:
        return

    if diff > 0:
        for _ in range(steps):
            send_volume_key(0)
            time.sleep(STEP_DELAY_SECONDS)
            current = min(100, current + VOLUME_STEP)
    else:
        for _ in range(steps):
            send_volume_key(1)
            time.sleep(STEP_DELAY_SECONDS)
            current = max(0, current - VOLUME_STEP)

    _cached_volume = int(current)
    if logger:
        logger.debug(
            f"Sent {steps} key presses, estimated new volume: {_cached_volume}%"
        )


def sync_with_soundsource() -> int:
    """Force-sync cache with current SoundSource volume."""
    global _cached_volume, _last_plist_read, _rust_coalescer
    _cached_volume = None
    _last_plist_read = 0
    _rust_coalescer = None
    return get_soundsource_volume(force_refresh=True)
