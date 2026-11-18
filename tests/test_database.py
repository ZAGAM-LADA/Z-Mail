from database.db_manager import Database

def test_insert_search_and_deduplicate(tmp_path):
    db = Database(tmp_path / "test.sqlite3")
    raw = b"From: a@example.com\r\nSubject: invoice\r\n\r\ninvoice body"
    item = {
        "message_hash": "abc123", "message_id": "", "sender": "a@example.com",
        "recipient": "", "subject": "invoice", "date_text": "", "body_text": "invoice body",
        "raw_eml": raw, "source_path": "sample.eml", "source_format": "EML", "attachment_count": 0
    }
    assert db.add_message(item) is True
    assert db.add_message(item) is False  # same source is not a second copy
    other_copy = dict(item, source_path="backup/sample.eml")
    assert db.add_message(other_copy) is False
    assert len(db.search("invoice")) == 1
    assert db.counts()["messages"] == 1
    assert db.counts()["duplicates"] == 1
    assert db.counts()["sources"] == 2
    db.close()
