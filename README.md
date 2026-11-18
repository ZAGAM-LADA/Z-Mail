# Z-MAIL RECOVERY — Premium Edition (Phase 1)

A local-first desktop email investigation application for Linux Mint 22.3 Cinnamon.
This is a functional Phase 1 foundation, not the complete enterprise specification.

## What works in this build

- Native PySide6 desktop UI with premium dark/light themes.
- Live dashboard counts sourced from the local database.
- Read-only recursive discovery of EML and MBOX files.
- Basic Thunderbird profile discovery for common Linux locations.
- Message parsing: headers, sender, recipient, subject, date and plain-text body.
- MIME attachment discovery and extraction on demand.
- SQLite indexing and duplicate detection by SHA-256 of the original message bytes.
- Basic unified search across indexed sender, recipient, subject and body.
- EML export and JSON investigation reports.
- Background scanning with progress updates and safe cancellation.
- Automated tests using synthetic email fixtures.

## Important recovery limitation

Software cannot fetch a message that Google has permanently erased from its servers and that no longer exists in any local copy, archive, backup or other accessible source. Gmail OAuth/API integration is not part of Phase 1. It will be implemented separately using Google's official OAuth 2.0 flow and Gmail API, with the minimum necessary permissions.

This version does not perform raw-disk carving or deleted-file recovery. SSD TRIM, encryption and overwriting may make deleted data unrecoverable.

## Requirements

- Linux Mint 22.3, 64-bit
- Python 3.12+ recommended
- Internet connection for installing dependencies only; local scanning works offline

## Installation

Open Terminal in the extracted project directory:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

To add an application shortcut to the Cinnamon menu, run:
```bash
bash scripts/install_desktop_launcher.sh
```

Do not replace Linux Mint's system Python. If `python3 --version` is below 3.12, use a separate Python 3.12 environment.

## First investigation

1. Launch the application.
2. First choose the included `sample_data/` folder to verify the scanner without touching your personal email.
3. Choose a folder containing a backup, exported messages, or Thunderbird profile.
4. Click **Start Scan**.
5. Open **Advanced Search** to search the messages found.
6. Select a row and use **Export Center** to export the message as EML or extract its attachments.
7. Generate a JSON report from **Reports**.

For Thunderbird, the app detects common profile folders under `~/.thunderbird` and `~/.mozilla-thunderbird`. You can choose the profile folder manually to scan its mailbox files.

## Data locations

Application data i
s stored under:

```text
~/.local/share/z-mail-recovery/
├── data/zmail.sqlite3
└── exports/
```

Original source files are not modified. Emails are indexed into the local SQLite database. Attachments are written only when the user explicitly requests extraction.

## Security and forensic precautions

- Use only accounts and storage you own or are authorized to investigate.
- Source email files are opened read-only.
- Do not write recovered data back to the source drive.
- For important forensic evidence, make a verified working copy and preserve the original device.
- Avoid scanning a live system disk for deleted data if evidence preservation matters.
- The first version does not inspect raw disk sectors.

## Tests

```bash
pytest -q
```

## Known limitations / next phases

- Gmail OAuth/API integration: Phase 2.
- Archive contents in ZIP/TAR: discovery only; extraction is not implemented in this build.
- Raw disk and deleted-file recovery: not implemented.
- PDF reports: not implemented; JSON reports are available.
- Pause/resume: cancellation is implemented; pause/resume is planned.
- Installer/AppImage: not included.
- Search currently uses SQLite `LIKE`; FTS5 can be added in the next iteration.

See `IMPLEMENTATION_STATUS.md` for the exact status of each module.
