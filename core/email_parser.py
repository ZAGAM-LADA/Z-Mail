import hashlib
from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser

def decode_header_value(value) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(str(value))))
    except Exception:
        return str(value)

def parse_message(raw: bytes, source_path: str, source_format: str) -> dict:
    """Parse one RFC 5322/MIME message without writing to its source."""
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    bodies = []
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart():
                continue
            payload = part.get_payload(decode=True) or b""
            filename = part.get_filename()
            disposition = part.get_content_disposition()
            if filename or disposition == "attachment":
                attachments.append({
                    "filename": decode_header_value(filename or "attachment.bin"),
                    "content_type": part.get_content_type(),
                    "payload": payload,
                })
            elif part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                try:
                    bodies.append(payload.decode(charset, errors="replace"))
                except LookupError:
                    bodies.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                bodies.append(payload.decode(charset, errors="replace"))
            except LookupError:
                bodies.append(payload.decode("utf-8", errors="replace"))

    return {
        "message_hash": hashlib.sha256(raw).hexdigest(),
        "message_id": str(msg.get("Message-ID", "") or ""),
        "sender": decode_header_value(msg.get("From", "")),
        "recipient": decode_header_value(msg.get("To", "")),
        "subject": decode_header_value(msg.get("Subject", "")),
        "date_text": str(msg.get("Date", "") or ""),
        "body_text": "\n".join(bodies),
        "raw_eml": raw,
        "source_path": str(source_path),
        "source_format": source_format,
        "attachment_count": len(attachments),
        "attachments": attachments,
    }
