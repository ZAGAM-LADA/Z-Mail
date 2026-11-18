from pathlib import Path
import re
from email import policy
from email.parser import BytesParser

def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name or "message").strip("._")
    return (cleaned[:90] or "message")

def export_eml(row, destination: str) -> Path:
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    filename = f"{safe_filename(row['subject'])}_{row['id']}.eml"
    target = dest / filename
    # Avoid overwriting anything even if the same subject/id export already exists.
    counter = 1
    while target.exists():
        target = dest / f"{safe_filename(row['subject'])}_{row['id']}_{counter}.eml"
        counter += 1
    target.write_bytes(bytes(row["raw_eml"]))
    return target

def export_attachments(row, destination: str):
    dest = Path(destination) / f"message_{row['id']}"
    dest.mkdir(parents=True, exist_ok=True)
    msg = BytesParser(policy=policy.default).parsebytes(bytes(row["raw_eml"]))
    written = []
    for index, part in enumerate(msg.walk()):
        if part.is_multipart():
            continue
        filename = part.get_filename()
        if filename or part.get_content_disposition() == "attachment":
            safe = safe_filename(filename or f"attachment_{index}.bin")
            target = dest / safe
            counter = 1
            while target.exists():
                target = dest / f"{counter}_{safe}"
                counter += 1
            target.write_bytes(part.get_payload(decode=True) or b"")
            written.append(target)
    return written
