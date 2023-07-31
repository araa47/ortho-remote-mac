import logging
import queue
import signal
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
in_port = None


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
    global in_port
    with mido.open_input(device_name) as in_port:
        for msg in in_port:
            logging.info(msg.type)
            logging.info(msg)

            if not running:
                in_port.close()
                break

            if msg.type == "control_change" and msg.control == 1:
                adjust_volume(msg.value)


def volume_thread_function():
    global running
    while running:
        # Wait for a new item in the queue
        volume_value = volume_queue.get()
        set_volume(volume_value)


def signal_handler(signal, frame):
    global running
    global in_port
    running = False
    logging.info("\nInterrupted by user. Exiting.")
    in_port.close()


def main():
    signal.signal(signal.SIGINT, signal_handler)

    # this will be the list of midi devices
    midi_devices = mido.get_input_names()
    logging.info(f"Available MIDI devices: {midi_devices}")

    selected_device = midi_devices[0]
    logging.info(f"Midi Device: {selected_device} will be auto selected!")

    # Start the volume thread
    volume_thread = threading.Thread(target=volume_thread_function)
    volume_thread.start()

    try:
        handle_midi_messages(selected_device)
    except KeyboardInterrupt:
        signal_handler(None, None)

    # wait for the thread to finish
    volume_thread.join()


if __name__ == "__main__":
    main()
