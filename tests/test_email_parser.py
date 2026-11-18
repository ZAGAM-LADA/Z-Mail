from core.email_parser import parse_message

def test_parse_simple_eml():
    raw = (
        b"From: Alice <alice@example.com>\r\n"
        b"To: Bob <bob@example.com>\r\n"
        b"Subject: Hello\r\n"
        b"Date: Tue, 1 Jan 2024 10:00:00 +0000\r\n\r\n"
        b"Hello world"
    )
    item = parse_message(raw, "sample.eml", "EML")
    assert item["sender"]
    assert item["subject"] == "Hello"
    assert "Hello world" in item["body_text"]
    assert len(item["message_hash"]) == 64

def test_attachment_is_detected():
    raw = (
        b"From: a@example.com\r\n"
        b"To: b@example.com\r\n"
        b"Subject: File\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: multipart/mixed; boundary=x\r\n\r\n"
        b"--x\r\nContent-Type: text/plain\r\n\r\nBody\r\n"
        b"--x\r\nContent-Type: application/pdf\r\n"
        b"Content-Disposition: attachment; filename=\"file.pdf\"\r\n"
        b"Content-Transfer-Encoding: base64\r\n\r\nJVBERi0=\r\n--x--\r\n"
    )
    item = parse_message(raw, "a.eml", "EML")
    assert item["attachment_count"] == 1
