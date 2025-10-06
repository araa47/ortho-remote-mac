import logging
import queue
import signal
import sys
import threading
import time

import mido
import osascript

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

volume_queue = queue.Queue()
running = True  # Variable to control the execution of the thread


def set_volume(value):
    start_time = time.time()  # Get the current time
    # Map the MIDI value (0-127) to a volume (0-100)
    new_volume = int(value * 100 / 127)
    osascript.run(f"set volume output volume {new_volume}")
    end_time = time.time()  # Get the current time after setting the volume
    logging.info(f"Setting volume took {end_time - start_time} seconds.")


def adjust_volume(value):
    # Remove all existing items in the queue
    while not volume_queue.empty():
        volume_queue.get()

    # Add the new value to the queue
    volume_queue.put(value)


def handle_midi_messages(device_name):
    global running
    with mido.open_input(device_name) as port:
        for msg in port:
            if not running:
                break

            logging.info(msg.type)
            logging.info(msg)

            if msg.type == "control_change" and msg.control == 1:
                adjust_volume(msg.value)


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
    logging.info("\nInterrupted by user. Exiting.")
    # Put sentinel value to wake up volume thread
    volume_queue.put(None)
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    # this will be the list of midi devices
    midi_devices = mido.get_input_names()
    logging.info(f"Available MIDI devices: {midi_devices}")

    selected_device = midi_devices[0]
    logging.info(f"Midi Device: {selected_device} will be auto selected!")

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
        logging.info("Shutdown complete.")


if __name__ == "__main__":
    main()
