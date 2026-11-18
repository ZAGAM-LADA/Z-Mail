import os
import re
from pathlib import Path
from .mbox_parser import iter_mbox
from .eml_parser import parse_eml

THUNDERBIRD_ROOTS = (
    Path.home() / ".thunderbird",
    Path.home() / ".mozilla-thunderbird",
)
MBOX_NAMES = {"inbox", "sent", "sent items", "archives", "archive", "drafts",
              "trash", "junk", "all mail", "templates"}

def discover_thunderbird_profiles():
    found = []
    for root in THUNDERBIRD_ROOTS:
        if root.is_dir():
            try:
                found.extend(p for p in root.iterdir()
                             if p.is_dir() and (".default" in p.name or p.name == "default"))
            except OSError:
                pass
    return sorted(set(found))

def looks_like_mbox(path: Path) -> bool:
    """Conservative signature check for extensionless Thunderbird mailbox files."""
    try:
        if path.stat().st_size < 20:
            return False
        with path.open("rb") as handle:
            head = handle.read(8192)
        # MBOX records begin with an envelope separator; a message header follows.
        return bool(re.search(rb"(?m)^From (?:-|[^\r\n]{1,200})\r?\n[!-~]+:", head))
    except (OSError, PermissionError):
        return False

def _is_probable_mbox(path: Path) -> bool:
    low = path.name.lower()
    # Common Thunderbird mailbox files are extensionless (Inbox, Sent, etc.).
    return path.suffix.lower() == ".mbox" or (low in MBOX_NAMES and looks_like_mbox(path)) or (
        path.suffix == "" and looks_like_mbox(path)
    )

def scan_folder(root, db, progress=None, cancelled=None):
    """Scan EML/MBOX files in a selected folder. Files are only read, never changed."""
    root = Path(root).expanduser().resolve()
    files_seen = added = errors = 0

    def onerror(_error):
        nonlocal errors
        errors += 1

    for current, dirs, filenames in os.walk(root, topdown=True, followlinks=False, onerror=onerror):
        if cancelled and cancelled():
            break
        # Do not descend into symlinked directories.
        dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
        for filename in filenames:
            if cancelled and cancelled():
                break
            path = Path(current) / filename
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                if path.suffix.lower() == ".eml":
                    files_seen += 1
                    try:
                        item = parse_eml(path)
                        item.pop("attachments", None)
                        if db.add_message(item):
                            added += 1
                    except Exception:
                        errors += 1
                elif _is_probable_mbox(path):
                    files_seen += 1
                    try:
                        for item in iter_mbox(path):
                            if cancelled and cancelled():
                                break
                            item.pop("attachments", None)
                            if db.add_message(item):
                                added += 1
                    except Exception:
                        errors += 1
                if progress:
                    progress(files_seen, added, errors, str(path))
            except (OSError, PermissionError):
                errors += 1
    return files_seen, added, errors
