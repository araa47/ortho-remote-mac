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

## Run Automatically At Login (macOS launchd)

If you want `orm` always ready in the background, run it with a user `LaunchAgent`.

1) Install the tool once (recommended for `launchd`):

```bash
uv tool install git+https://github.com/araa47/ortho-remote-mac
```

2) Create `~/Library/LaunchAgents/com.user.ortho-remote-mac.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.ortho-remote-mac</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USER/.local/bin/orm</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USER</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/YOUR_USER/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USER/Library/Logs/ortho-remote-mac.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USER/Library/Logs/ortho-remote-mac.log</string>
</dict>
</plist>
```

Replace `YOUR_USER` with your macOS username.

3) Load and start it:

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.user.ortho-remote-mac.plist"
launchctl kickstart -k "gui/$(id -u)/com.user.ortho-remote-mac"
```

4) Verify status:

```bash
launchctl print "gui/$(id -u)/com.user.ortho-remote-mac"
```

5) View logs:

```bash
tail -f "$HOME/Library/Logs/ortho-remote-mac.log"
```

Stop/unload later:

```bash
launchctl bootout "gui/$(id -u)" "com.user.ortho-remote-mac"
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
