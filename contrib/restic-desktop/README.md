# Restic Desktop

Desktop GUI for [restic](https://restic.net) on Fedora and GNOME. It wraps the `restic` binary (it does not replace it) and uses `--json` output for operations.

## Features

- Configure repository (local, SFTP, S3, etc.)
- Store password in the GNOME keyring (libsecret)
- Initialize a new repository
- Back up selected folders with a progress bar
- List and verify snapshots
- Restore a snapshot to a target folder

## Requirements (Fedora)

```bash
sudo dnf install restic python3-gobject python3-gobject-devel \
  libadwaita libadwaita-devel python3-pip
pip install --user secretstorage
```

On Fedora 41+, this is usually enough:

```bash
sudo dnf install restic python3-gobject libadwaita python3-secretstorage
```

## Run without installing

From this directory:

```bash
chmod +x restic-desktop
./restic-desktop
```

## Installation

```bash
meson setup build
meson compile -C build
sudo meson install -C build
```

Then launch the app from the activities menu (**Restic Desktop**) or run:

```bash
restic-desktop
```

## Quick start

1. Open **Restic Desktop** and click the settings icon.
2. Enter the repository location (e.g. `/home/YOUR_USER/backups/restic`) and a strong password.
3. If the repository does not exist yet, use **Initialize repository**.
4. Under **Backup**, add folders and click **Start backup**.
5. Under **Snapshots**, review created backups.
6. Under **Restore**, pick a snapshot and a destination folder.

## Configuration and secrets

The app stores settings in `~/.config/restic-desktop/config.json` (repository path and backup folders only). Passwords are stored in the system keyring via libsecret, not in plain text.

**Do not commit** local copies of config files, password files, repository paths, or test backup data into this repository. See `.gitignore` for ignored patterns.

## Architecture

```
┌─────────────────────┐
│  GTK4 / libadwaita  │  ← UI (Python + PyGObject)
└──────────┬──────────┘
           │ subprocess + RESTIC_* env
┌──────────▼──────────┐
│   restic (binary)   │  ← encryption, deduplication, backends
└─────────────────────┘
```

Restic does not expose a Go library API; the supported integration for scripts and GUIs is to run the CLI with `--json`.

## License

BSD 2-Clause (same as restic).
