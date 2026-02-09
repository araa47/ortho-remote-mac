# Ortho Remote Mac

This is a simply python script that is able to pair to the [Ortho Remote](https://teenage.engineering/products/orthoremote) sold by [Teenage.engineering](https://teenage.engineering) , and when run can control yous macs volume when paired.

# Current Features

[x] Is able to pair with Ortho Remote

[x] Is able to detect control_change signals to control channel 0 (gets values 0 - 127 from turning the knob)

[x] Uses the control_change signals to adjust mac volume

[x] Safe shutdown (ctr+c shuts app properly)

[x] Play/Pause support using native media keys (works with any media player)

[x] Next/Previous track with double-click and triple-click


# Design Decisions

- Since MIDI messages come in faster than volume can be adjusted, a queue is used and volume adjustments are done in a separate thread
- **Volume control** defaults to `SoundSource` output volume when available (falls back to `osascript` system volume)
- **Play/pause** uses `pyobjc-framework-Quartz` to send native macOS media key events (F8)
  - Works system-wide with **any** media player (Music, Spotify, Chrome, Safari, YouTube, etc.)
  - **Note:** macOS will prompt for accessibility permissions on first run - make sure to allow them!
- **Next/Previous track** uses AppleScript to control Spotify directly
  - Currently only works with Spotify (not other media players)
  - More reliable than media keys on modern macOS

# Prerequisites

- **macOS** (required - this app uses macOS-specific APIs)
- **[uv](https://docs.astral.sh/uv/)** - Modern Python package manager (installation instructions below)
- **[direnv](https://direnv.net/)** (optional) - For development only, auto-loads environment when entering directory

# Installation

## Quick Start (Recommended)

The easiest way to run ortho-remote-mac is with `uvx` (no cloning required):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Pair your Ortho Remote to your Mac (follow instructions: https://youtu.be/KhmEXMWnO_c)

# Run directly from GitHub
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote
```

That's it! Turn your knob to control volume, press buttons to play/pause.

# Usage

## Basic Usage

**If you installed with `uvx` (Quick Start):**

```bash
# Run with auto-detection (prefers devices with "ortho" in the name)
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote

# Specify a specific device by name
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote --device "ortho remote"

# Enable debug logging to see all MIDI messages
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote --debug

# Force SoundSource volume backend
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote --volume-backend soundsource

# Force macOS system volume backend
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote --volume-backend system

# Show help
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote --help
```

**If you cloned the repo (Development Installation):**

```bash
# Run with auto-detection
ortho-remote

# Specify a specific device by name
ortho-remote --device "ortho remote"

# Enable debug logging
ortho-remote --debug

# Force SoundSource volume backend
ortho-remote --volume-backend soundsource

# Force macOS system volume backend
ortho-remote --volume-backend system

# Show help
ortho-remote --help
```

## Controls

- **Volume Control**: Turn the knob (control change on channel 1) to adjust Mac volume
- **Play/Pause**: Single-click any button to toggle play/pause (works with any media player)
- **Next Track**: Double-click any button to skip to the next track (**Spotify only**)
- **Previous Track**: Triple-click any button to go back to the previous track (**Spotify only**)

The app will automatically detect and prefer MIDI devices with "ortho" in their name. If you have multiple MIDI devices, it will list them on startup.

Volume backend behavior:
- `auto` (default): use SoundSource output volume if SoundSource is installed, otherwise use macOS system volume
- `soundsource`: require and control SoundSource output volume
- `system`: control macOS system output volume directly

**Note:** Next/Previous track controls currently only work with Spotify. Play/pause works with all media players (Spotify, Music, Chrome, Safari, etc.).

## Supported Media Players

The play/pause functionality works with **any media player** that responds to macOS media keys, including:
- **Music app** (Apple Music)
- **Spotify**
- **Chrome/Safari** (YouTube, any streaming site)
- **VLC, QuickTime Player, and other media players**
- **Browser-based players** (SoundCloud, Netflix, etc.)

Simply have any media playing, then press any button on your Ortho Remote to toggle play/pause!

# Configuration

## Device Selection

The app automatically detects and prefers MIDI devices with "ortho" in their name. If you have multiple MIDI devices:

1. **Run the app to see available devices:**
   ```bash
   # With uvx:
   uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote

   # Or if cloned:
   ortho-remote
   ```
   This will list all available MIDI devices.

2. **Specify a device by name:**
   ```bash
   # With uvx:
   uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote --device "ortho remote"

   # Or if cloned:
   ortho-remote --device "ortho remote"
   # partial name match also works
   ortho-remote --device "ortho"
   ```

## Debug Mode

To see all MIDI messages and detailed logging:

```bash
# With uvx:
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote --debug

# Or if cloned:
ortho-remote --debug
```

This is useful for troubleshooting or understanding what MIDI messages your device sends.

# Development Installation

If you want to contribute or modify the code:

1) Clone the repository

```bash
git clone https://github.com/araa47/ortho-remote-mac.git
cd ortho-remote-mac
```

2) Install uv and direnv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install direnv (macOS)
brew install direnv
```

3) Configure direnv

Add direnv hook to your shell config (`~/.zshrc` for zsh or `~/.bashrc` for bash):

```bash
eval "$(direnv hook zsh)"  # for zsh
# OR
eval "$(direnv hook bash)"  # for bash
```

Restart your shell or run `source ~/.zshrc` (or `~/.bashrc`).

4) Allow direnv and install dependencies

```bash
direnv allow
```

5) Pair your Ortho Remote

Follow the instructions [here](https://youtu.be/KhmEXMWnO_c) to pair your Ortho Remote to your Mac.

6) Run the app

```bash
ortho-remote
# or
python app.py
```

# Troubleshooting

**"No MIDI devices found"**: Make sure your Ortho Remote is paired via Bluetooth and appears in Audio MIDI Setup.

**Play/pause not working**: Ensure you have a media player running (Spotify, Music, Chrome with YouTube, etc.)

**Next/Previous track not working**: Make sure Spotify is running and playing. These controls only work with Spotify. You may also need to grant automation permissions in **System Settings > Privacy & Security > Automation > Terminal > Spotify**.

**Permission errors**: The first time you run the app, macOS will ask for **Accessibility permissions** to send media key events. Go to **System Settings > Privacy & Security > Accessibility** and enable the permission for your Terminal or iTerm2.

**SoundSource volume not changing**: Run with `--volume-backend soundsource` and make sure SoundSource is installed/running and your output device (for example Fiio R7) is selected in SoundSource.
