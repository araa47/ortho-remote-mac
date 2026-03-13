# Ortho Remote Mac

Control macOS volume and playback with a paired [Ortho Remote](https://teenage.engineering/products/orthoremote).

This project follows a `uv` + `prek` workflow similar to [cookiecutter-python-uv-boilerplate](https://github.com/araa47/cookiecutter-python-uv-boilerplate).

## Requirements

- macOS
- [uv](https://docs.astral.sh/uv/)
- Ortho Remote paired to your Mac ([pairing video](https://youtu.be/KhmEXMWnO_c))

## Quick Start (No Clone)

Run directly from GitHub with `uvx`:

```bash
uvx --from git+https://github.com/araa47/ortho-remote-mac ortho-remote
```

You can also use the shortcut command:

```bash
uvx --from git+https://github.com/araa47/ortho-remote-mac orm
```

## Install As A Local Tool (Recommended If You Use It Often)

Install once:

```bash
uv tool install git+https://github.com/araa47/ortho-remote-mac
```

Run anytime:

```bash
ortho-remote
# or
orm
```

Upgrade later:

```bash
uv tool upgrade ortho-remote-mac
```

## Common Usage

```bash
# Auto-detect MIDI device (prefers names containing "ortho")
orm

# Pick a specific MIDI device
orm --device "ortho remote"

# Debug MIDI events
orm --debug

# Choose volume backend
orm --volume-backend auto
orm --volume-backend soundsource
orm --volume-backend system
```

## Controls

- Turn knob: set volume
- Single click: play/pause (any media app)
- Double click: next track (Spotify)
- Triple click: previous track (Spotify)

## Optional: Rust SoundSource Accelerator

For lower-latency SoundSource planning with `uvx`:

```bash
uvx \
  --from git+https://github.com/araa47/ortho-remote-mac \
  --with 'ortho-remote-rs @ git+https://github.com/araa47/ortho-remote-mac#subdirectory=rust/ortho_remote_rs' \
  orm --volume-backend soundsource
```

## Development Setup

```bash
git clone https://github.com/araa47/ortho-remote-mac.git
cd ortho-remote-mac
direnv allow
```

`direnv allow` runs `uv sync --all-extras --dev` and installs `prek` hooks.

Run checks:

```bash
uv run prek run --all-files
uv run ty check
```

## Troubleshooting

- No MIDI devices: confirm the Ortho Remote is paired and visible in Audio MIDI Setup.
- Play/pause issues: ensure a media app is active.
- Next/previous issues: these actions are Spotify-only.
- Permission prompts: grant Accessibility and (for Spotify control) Automation permissions to your terminal app.
