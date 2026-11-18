import mailbox
from email.message import EmailMessage
from core.local_scanner import scan_folder, looks_like_mbox
from database.db_manager import Database

def test_extensionless_mbox_discovery(tmp_path):
    folder = tmp_path / "profile" / "Mail" / "Local Folders"
    folder.mkdir(parents=True)
    mailbox_path = folder / "Inbox"
    box = mailbox.mbox(str(mailbox_path))
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "owner@example.com"
    message["Subject"] = "Archived message"
    message.set_content("This is a local archive message.")
    box.add(message)
    box.flush()
    box.close()

    assert looks_like_mbox(mailbox_path)
    db = Database(tmp_path / "test.sqlite3")
    files_seen, added, errors = scan_folder(tmp_path / "profile", db)
    assert files_seen == 1
    assert added == 1
    assert errors == 0
    assert len(db.search("Archived message")) == 1
    db.close()
