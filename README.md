# Ortho Remote Mac

This is a simply python script that is able to pair to the [Ortho Remote](https://teenage.engineering/products/orthoremote) sold by [Teenage.engineering](https://teenage.engineering) , and when run can control yous macs volume when paired.

# Current Features

[x] Is able to pair with Ortho Remote

[x] Is able to detect control_change signals to control channel 0 (gets values 0 - 127 from turning the knob)

[x] Uses the control_change signals to adjust mac volume

[x] Safe shutdown (ctr+c shuts app properly)

[ ] Play/Pause support without too permissive key controls


# Design Decisions

- Since midi messages come in faster compared to how fast I can adjust the volume, a queue is used, and volume adjustments are done in a different thread


# Installation

1) Simply clone the repository

2) Install uv if you haven't already

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3) Install direnv (macOS)

```bash
brew install direnv
```

Then add direnv hook to your shell config (`~/.zshrc` for zsh or `~/.bashrc` for bash):

```bash
eval "$(direnv hook zsh)"  # for zsh
# OR
eval "$(direnv hook bash)"  # for bash
```

Restart your shell or run `source ~/.zshrc` (or `~/.bashrc`).

4) Allow direnv and install dependencies

Navigate to the project directory and allow direnv (this will automatically install dependencies):

```bash
cd ortho-remote-mac
direnv allow
```

5) Now pair your ortho remote to your mac, simply follow the instructions [here](https://youtu.be/KhmEXMWnO_c)

6) Once successfully paired simply run

```bash
python app.py
```

The script currently assumes you only have 1 bluetooth midi device, and will use this as the device, if this is not the case you might want to modify the code slightly to select the correct device. Simply change the midi device number in the following code

```
handle_midi_messages(midi_devices[0])
```
