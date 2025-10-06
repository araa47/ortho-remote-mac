import logging
import queue
import signal
import sys
import threading
import time

import click
import mido
import osascript
import Quartz

# Setup logger
logger = logging.getLogger(__name__)

volume_queue = queue.Queue()
running = True  # Variable to control the execution of the thread

# Click tracking for multi-click detection
last_click_time = 0
click_count = 0
DOUBLE_CLICK_THRESHOLD = 0.3  # seconds


def set_volume(value):
    """
    Set system volume to an exact level.
    Uses osascript (not Quartz) because we need precise volume control (0-100),
    whereas Quartz volume keys only increment/decrement in fixed steps.
    """
    start_time = time.time()
    # Map the MIDI value (0-127) to a volume (0-100)
    new_volume = int(value * 100 / 127)
    osascript.run(f"set volume output volume {new_volume}")
    end_time = time.time()
    logger.info(f"🔊 Volume set to {new_volume}% ({end_time - start_time:.3f}s)")


def send_media_key(key_type, key_name):
    """
    Send a media key event using Quartz.
    key_type: The NX_KEYTYPE constant (16=play/pause, 17=next, 18=previous)
    key_name: Human-readable name for logging
    """
    start_time = time.time()

    # Create and post a media key event
    event = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
        Quartz.NSSystemDefined,  # type
        (0, 0),  # location
        0xA00,  # flags
        0,  # timestamp
        0,  # window
        0,  # context
        8,  # subtype (media key)
        (key_type << 16) | (0xA << 8),  # data1
        -1,  # data2
    )

    Quartz.CGEventPost(0, event.CGEvent())

    end_time = time.time()
    logger.info(f"⏯️  {key_name} ({end_time - start_time:.3f}s)")


def play_pause():
    """Toggle play/pause for the active media player."""
    NX_KEYTYPE_PLAY = 16
    send_media_key(NX_KEYTYPE_PLAY, "Play/pause")


def next_track():
    """Skip to the next track (Spotify only)."""
    start_time = time.time()

    try:
        osascript.run('tell application "Spotify" to next track')
        logger.info(f"⏭️  Next track ({time.time() - start_time:.3f}s)")
    except Exception as e:
        logger.warning(f"⚠️  Next track failed: Is Spotify running? ({e})")


def previous_track():
    """Go to the previous track (Spotify only)."""
    start_time = time.time()

    try:
        osascript.run('tell application "Spotify" to previous track')
        logger.info(f"⏮️  Previous track ({time.time() - start_time:.3f}s)")
    except Exception as e:
        logger.warning(f"⚠️  Previous track failed: Is Spotify running? ({e})")


def adjust_volume(value):
    # Remove all existing items in the queue
    while not volume_queue.empty():
        volume_queue.get()

    # Add the new value to the queue
    volume_queue.put(value)


def handle_button_click():
    """
    Handle button clicks with multi-click detection.
    Single click: play/pause
    Double click: next track
    Triple click: previous track
    """
    global last_click_time, click_count

    current_time = time.time()
    time_since_last_click = current_time - last_click_time

    if time_since_last_click < DOUBLE_CLICK_THRESHOLD:
        # This is part of a multi-click
        click_count += 1
    else:
        # New click sequence - execute previous action if any
        if click_count > 0:
            execute_click_action(click_count)
        click_count = 1

    last_click_time = current_time

    # Start a timer to execute the action after threshold
    def delayed_execution():
        time.sleep(DOUBLE_CLICK_THRESHOLD + 0.05)
        global click_count
        if time.time() - last_click_time >= DOUBLE_CLICK_THRESHOLD:
            execute_click_action(click_count)
            click_count = 0

    threading.Thread(target=delayed_execution, daemon=True).start()


def execute_click_action(clicks):
    """Execute the appropriate action based on number of clicks."""
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
    with mido.open_input(device_name) as port:
        for msg in port:
            if not running:
                break

            # Log all MIDI messages at debug level
            logger.debug(f"MIDI Message - Type: {msg.type}, Data: {msg}")

            # Control 1 is typically the modulation wheel - used for volume
            if msg.type == "control_change" and msg.control == 1:
                adjust_volume(msg.value)
            # Note_on messages for button presses with multi-click detection
            elif msg.type == "note_on" and msg.velocity > 0:
                logger.debug(f"Button pressed: note {msg.note}")
                handle_button_click()
            # Control change messages for other buttons
            elif msg.type == "control_change" and msg.control != 1:
                logger.debug(f"Control {msg.control} changed to {msg.value}")
                # Uncomment the next line if your buttons send control_change messages
                # handle_button_click()


def volume_thread_function():
    global running
    while running:
        try:
            # Wait for a new item in the queue with timeout
            volume_value = volume_queue.get(timeout=0.5)
            if volume_value is None:  # Sentinel value to exit
                break
            set_volume(volume_value)
        except queue.Empty:
            # Timeout occurred, check running flag and continue
            continue


def signal_handler(sig, frame):
    global running
    running = False
    logger.info("\n👋 Interrupted by user. Exiting.")
    # Put sentinel value to wake up volume thread
    volume_queue.put(None)
    sys.exit(0)


def select_device(device_name=None):
    """Select the appropriate MIDI device."""
    midi_devices = mido.get_input_names()

    if not midi_devices:
        logger.error("❌ No MIDI devices found!")
        logger.error("Make sure your Ortho Remote is paired via Bluetooth.")
        sys.exit(1)

    logger.info("📱 Available MIDI devices:")
    for i, device in enumerate(midi_devices):
        logger.info(f"  [{i}] {device}")

    # If user specified a device name
    if device_name:
        # Try exact match
        if device_name in midi_devices:
            logger.info(f"✅ Selected device: {device_name}")
            return device_name

        # Try case-insensitive partial match
        for device in midi_devices:
            if device_name.lower() in device.lower():
                logger.info(f"✅ Selected device: {device}")
                return device

        logger.error(f"❌ Device '{device_name}' not found!")
        sys.exit(1)

    # Auto-select: prefer devices with "ortho" in the name
    for device in midi_devices:
        if "ortho" in device.lower():
            logger.info(f"✅ Auto-selected device: {device}")
            return device

    # Fallback to first device
    selected = midi_devices[0]
    logger.info(f"✅ Selected first available device: {selected}")
    return selected


@click.command()
@click.option(
    "--device",
    "-d",
    help="MIDI device name or partial name to use (default: auto-detect 'ortho')",
)
@click.option(
    "--debug", is_flag=True, help="Enable debug logging (shows all MIDI messages)"
)
def main(device, debug):
    """
    Control your Mac volume and media playback with an Ortho Remote.

    Turn the knob to adjust volume, press buttons to play/pause.
    """
    # Setup logging
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

    # Select MIDI device
    selected_device = select_device(device)

    logger.info("=" * 40)
    logger.info("🎵 Ready! Turn knob for volume, press button for play/pause")
    logger.info("Press Ctrl+C to exit")
    logger.info("=" * 40)

    # Start the volume thread as daemon so it doesn't block exit
    volume_thread = threading.Thread(target=volume_thread_function, daemon=True)
    volume_thread.start()

    try:
        handle_midi_messages(selected_device)
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        volume_queue.put(None)  # Wake up volume thread
        volume_thread.join(timeout=2)  # Wait up to 2 seconds for clean shutdown
        logger.info("👋 Shutdown complete.")


if __name__ == "__main__":
    main()
