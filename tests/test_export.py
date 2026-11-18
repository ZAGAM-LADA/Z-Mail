from core.exporter import export_eml, export_attachments

def test_export_eml_without_overwrite(tmp_path):
    row = {
        "id": 4,
        "subject": "Important",
        "raw_eml": b"From: a@example.com\r\nSubject: Important\r\n\r\nBody"
    }
    first = export_eml(row, tmp_path)
    second = export_eml(row, tmp_path)
    assert first.exists() and second.exists()
    assert first != second
    assert first.read_bytes() == row["raw_eml"]

def test_extract_attachment(tmp_path):
    raw = (
        b"From: a@example.com\r\n"
        b"To: b@example.com\r\n"
        b"Subject: Attachment\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: multipart/mixed; boundary=x\r\n\r\n"
        b"--x\r\nContent-Type: text/plain\r\n\r\nBody\r\n"
        b"--x\r\nContent-Type: application/pdf\r\n"
        b"Content-Disposition: attachment; filename=\"proof.pdf\"\r\n"
        b"Content-Transfer-Encoding: base64\r\n\r\nJVBERi0=\r\n--x--\r\n"
    )
    row = {"id": 9, "raw_eml": raw}
    files = export_attachments(row, tmp_path)
    assert len(files) == 1
    assert files[0].name == "proof.pdf"
    assert files[0].read_bytes() == b"%PDF-"
