from core.local_scanner import scan_folder
from database.db_manager import Database

def test_scan_eml_folder(tmp_path):
    mail = tmp_path / "mail"
    mail.mkdir()
    (mail / "message.eml").write_bytes(
        b"From: sender@example.com\r\nTo: you@example.com\r\n"
        b"Subject: Local test\r\n\r\nTest body"
    )
    db = Database(tmp_path / "index.sqlite3")
    files, added, errors = scan_folder(mail, db)
    assert files == 1
    assert added == 1
    assert errors == 0
    assert len(db.search("Local test")) == 1
    db.close()
