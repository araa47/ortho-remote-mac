# Ortho Remote Mac

This is a simply python script that is able to pair to the [Ortho Remote](https://teenage.engineering/products/orthoremote) sold by [Teenage.engineering](https://teenage.engineering) , and when run can control yous macs volume when paired.

# Current Features

[x] Is able to pair with Ortho Remote

[x] Is able to detect control_change signals to control channel 0 (gets values 0 - 127 from turning the knob)

[x] Uses the control_change signals to adjust mac volume

[ ] Safe shutdown (ctr+c shuts app properly)

[ ] Play/Pause support without too permissive key controls


# Design Decisons

- Since midi messages come in faster compared to how fast I can adjust the volume, a queue is used, and volume adjustments are done in a different thread


# Installation

1) Simply clone the repository

2) Install deps (make sure you have poetry and python)

```
poetry install
```

3) Now pair your ortho remote to your mac, simply follow the instructions [here](https://youtu.be/KhmEXMWnO_c)

4) Once successfully paired simply run

```
poetry run python3 app.py
```

The script currently assumes you only have 1 bluetooth midi device, and will use this as the device, if this is not the case you might want to modify the code slightly to select the correct device. Simply change the midi device number in the following code

```
handle_midi_messages(midi_devices[0])
```
