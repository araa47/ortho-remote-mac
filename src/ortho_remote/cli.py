"""CLI for ortho remote controller."""

import logging
import os
import signal
import sys
import threading
import time
from enum import Enum
from typing import Optional

import mido
import osascript
import Quartz
import typer

from ortho_remote.backends.soundsource import (
    SOUNDSOURCE_SOURCES_PLIST,
    set_volume_precise,
    sync_with_soundsource,
)
from ortho_remote.backends.system import set_system_volume

logger = logging.getLogger(__name__)

running = True
volume_backend = "system"
pending_volume_value: int | None = None
volume_condition = threading.Condition()

last_click_time = 0
click_count = 0
DOUBLE_CLICK_THRESHOLD = 0.3


def set_volume(value):
    """Set volume to exact level (0-100)."""
    start_time = time.time()
    target_volume = int(value * 100 / 127)

    if volume_backend == "soundsource":
        set_volume_precise(target_volume, logger=logger)
    else:
        set_system_volume(target_volume)

    end_time = time.time()
    logger.info(
        f"🔊 Volume set to {target_volume}% via {volume_backend} ({end_time - start_time:.3f}s)"
    )


def configure_volume_backend(mode):
    """Resolve requested volume backend."""
    if mode == "system":
        return "system"

    has_soundsource = os.path.exists(SOUNDSOURCE_SOURCES_PLIST)
    if not has_soundsource:
        if mode == "soundsource":
            logger.error(
                f"❌ SoundSource backend requested but plist not found: {SOUNDSOURCE_SOURCES_PLIST}"
            )
            sys.exit(1)
        return "system"

    try:
        current = sync_with_soundsource()
        logger.info(f"🎚️  SoundSource detected (current output volume: {current}%)")
        return "soundsource"
    except Exception as exc:
        if mode == "soundsource":
            logger.error(f"❌ Could not initialize SoundSource volume backend: {exc}")
            sys.exit(1)
        logger.warning(
            f"⚠️  SoundSource detected but unavailable, falling back to system volume: {exc}"
        )
        return "system"


def send_media_key(key_type, key_name):
    """Send a media key event using Quartz."""
    start_time = time.time()

    event = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(  # ty: ignore[unresolved-attribute]
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
    Quartz.CGEventPost(0, event.CGEvent())  # ty: ignore[unresolved-attribute]

    end_time = time.time()
    logger.info(f"⏯️  {key_name} ({end_time - start_time:.3f}s)")


def play_pause():
    NX_KEYTYPE_PLAY = 16
    send_media_key(NX_KEYTYPE_PLAY, "Play/pause")


def next_track():
    start_time = time.time()
    try:
        osascript.run('tell application "Spotify" to next track')
        logger.info(f"⏭️  Next track ({time.time() - start_time:.3f}s)")
    except Exception as e:
        logger.warning(f"⚠️  Next track failed: Is Spotify running? ({e})")


def previous_track():
    start_time = time.time()
    try:
        osascript.run('tell application "Spotify" to previous track')
        logger.info(f"⏮️  Previous track ({time.time() - start_time:.3f}s)")
    except Exception as e:
        logger.warning(f"⚠️  Previous track failed: Is Spotify running? ({e})")


def adjust_volume(value):
    global pending_volume_value
    with volume_condition:
        pending_volume_value = value
        volume_condition.notify()


def handle_button_click():
    """Handle button clicks with multi-click detection."""
    global last_click_time, click_count

    current_time = time.time()
    time_since_last_click = current_time - last_click_time

    if time_since_last_click < DOUBLE_CLICK_THRESHOLD:
        click_count += 1
    else:
        if click_count > 0:
            execute_click_action(click_count)
        click_count = 1

    last_click_time = current_time

    def delayed_execution():
        time.sleep(DOUBLE_CLICK_THRESHOLD + 0.05)
        global click_count
        if time.time() - last_click_time >= DOUBLE_CLICK_THRESHOLD:
            execute_click_action(click_count)
            click_count = 0

    threading.Thread(target=delayed_execution, daemon=True).start()


def execute_click_action(clicks):
    if clicks == 1:
        logger.debug("Single click - Play/Pause")
        play_pause()
    elif clicks == 2:
        logger.debug("Double click - Next Track")
        next_track()
    elif clicks >= 3:
        logger.debug("Triple click - Previous Track")
        previous_track()


def handle_midi_messages(device_name):
    global running
    with mido.open_input(device_name) as port:  # ty: ignore[unresolved-attribute]
        for msg in port:
            if not running:
                break

            logger.debug(f"MIDI Message - Type: {msg.type}, Data: {msg}")
            if msg.type == "control_change" and msg.control == 1:
                adjust_volume(msg.value)
            elif msg.type == "note_on" and msg.velocity > 0:
                logger.debug(f"Button pressed: note {msg.note}")
                handle_button_click()
            elif msg.type == "control_change" and msg.control != 1:
                logger.debug(f"Control {msg.control} changed to {msg.value}")


def volume_thread_function():
    global running, pending_volume_value
    while running:
        with volume_condition:
            while running and pending_volume_value is None:
                volume_condition.wait(timeout=0.5)

            if not running and pending_volume_value is None:
                break

            volume_value = pending_volume_value
            pending_volume_value = None

        if volume_value is not None:
            set_volume(volume_value)


def signal_handler(sig, frame):
    global running
    running = False
    logger.info("\n👋 Interrupted by user. Exiting.")
    with volume_condition:
        volume_condition.notify_all()
    sys.exit(0)


def select_device(device_name=None):
    """Select the appropriate MIDI device."""
    midi_devices = mido.get_input_names()  # ty: ignore[unresolved-attribute]

    if not midi_devices:
        logger.error("❌ No MIDI devices found!")
        logger.error("Make sure your Ortho Remote is paired via Bluetooth.")
        sys.exit(1)

    logger.info("📱 Available MIDI devices:")
    for i, device in enumerate(midi_devices):
        logger.info(f"  [{i}] {device}")

    if device_name:
        if device_name in midi_devices:
            logger.info(f"✅ Selected device: {device_name}")
            return device_name
        for device in midi_devices:
            if device_name.lower() in device.lower():
                logger.info(f"✅ Selected device: {device}")
                return device
        logger.error(f"❌ Device '{device_name}' not found!")
        sys.exit(1)

    for device in midi_devices:
        if "ortho" in device.lower():
            logger.info(f"✅ Auto-selected device: {device}")
            return device

    selected = midi_devices[0]
    logger.info(f"✅ Selected first available device: {selected}")
    return selected


class VolumeBackendMode(str, Enum):
    auto = "auto"
    soundsource = "soundsource"
    system = "system"


def start(
    device: Optional[str] = typer.Option(
        None,
        "--device",
        "-d",
        help="MIDI device name or partial name to use (default: auto-detect 'ortho')",
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug logging (shows all MIDI messages)"
    ),
    volume_backend_mode: VolumeBackendMode = typer.Option(
        VolumeBackendMode.auto,
        "--volume-backend",
        help="Volume control target. 'soundsource' controls SoundSource output; 'system' controls macOS system volume.",
        case_sensitive=False,
    ),
):
    """Control your Mac volume and media playback with an Ortho Remote."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format=(
            "%(message)s" if not debug else "%(asctime)s - %(levelname)s - %(message)s"
        ),
    )

    signal.signal(signal.SIGINT, signal_handler)

    logger.info("🎛️  Ortho Remote Mac Controller")
    logger.info("=" * 40)

    global running, volume_backend
    volume_backend = configure_volume_backend(volume_backend_mode.value.lower())
    logger.info(f"🎚️  Using volume backend: {volume_backend}")

    selected_device = select_device(device)

    logger.info("=" * 40)
    logger.info("🎵 Ready! Turn knob for volume, press button for play/pause")
    logger.info("Press Ctrl+C to exit")
    logger.info("=" * 40)

    volume_thread = threading.Thread(target=volume_thread_function, daemon=True)
    volume_thread.start()

    try:
        handle_midi_messages(selected_device)
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        with volume_condition:
            volume_condition.notify_all()
        volume_thread.join(timeout=2)
        logger.info("👋 Shutdown complete.")


def main():
    typer.run(start)
