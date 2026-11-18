import mailbox
from pathlib import Path
from .email_parser import parse_message

def iter_mbox(path: Path):
    """Yield parsed messages one at a time to keep memory use bounded."""
    box = mailbox.mbox(str(path), create=False)
    try:
        for message in box:
            try:
                raw = message.as_bytes(policy=message.policy)
                if raw:
                    yield parse_message(raw, str(path), "MBOX")
            except Exception:
                # A damaged item should not prevent later messages being inspected.
                continue
    finally:
        box.close()
