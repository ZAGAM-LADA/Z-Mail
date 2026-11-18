import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    message_hash TEXT NOT NULL UNIQUE,
    message_id TEXT,
    sender TEXT,
    recipient TEXT,
    subject TEXT,
    date_text TEXT,
    body_text TEXT,
    raw_eml BLOB NOT NULL,
    source_path TEXT NOT NULL,
    source_format TEXT NOT NULL,
    attachment_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Extracted',
    discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender);
CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date_text);
CREATE INDEX IF NOT EXISTS idx_messages_source ON messages(source_path);
CREATE TABLE IF NOT EXISTS investigations (
    id INTEGER PRIMARY KEY,
    root_path TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    files_seen INTEGER NOT NULL DEFAULT 0,
    messages_added INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS duplicate_copies (
    id INTEGER PRIMARY KEY,
    message_hash TEXT NOT NULL,
    original_message_id INTEGER NOT NULL,
    duplicate_source_path TEXT NOT NULL,
    duplicate_format TEXT NOT NULL,
    detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_hash, duplicate_source_path)
);
"""

class Database:
    """Small SQLite repository. A lock serializes access from GUI and worker thread."""
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.execute("PRAGMA foreign_keys=ON")
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.executescript(SCHEMA)
            self.conn.commit()

    def close(self):
        with self._lock:
            self.conn.close()

    def add_message(self, item: dict) -> bool:
        with self._lock:
            existing = self.conn.execute(
                "SELECT id, source_path FROM messages WHERE message_hash=?",
                (item["message_hash"],)
            ).fetchone()
            if existing:
                if existing["source_path"] != item["source_path"]:
                    self.conn.execute("""
                        INSERT OR IGNORE INTO duplicate_copies
                        (message_hash, original_message_id, duplicate_source_path, duplicate_format)
                        VALUES(?,?,?,?)
                    """, (
                        item["message_hash"], existing["id"],
                        item["source_path"], item["source_format"]
                    ))
                    self.conn.commit()
                return False
            self.conn.execute("""
                INSERT INTO messages
                (message_hash,message_id,sender,recipient,subject,date_text,body_text,
                 raw_eml,source_path,source_format,attachment_count,status)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                item["message_hash"], item.get("message_id"), item.get("sender"),
                item.get("recipient"), item.get("subject"), item.get("date_text"),
                item.get("body_text"), sqlite3.Binary(item["raw_eml"]),
                item["source_path"], item["source_format"],
                item.get("attachment_count", 0), item.get("status", "Extracted")
            ))
            self.conn.commit()
            return True

    def counts(self) -> dict:
        with self._lock:
            c = self.conn
            return {
                "messages": c.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
                "sources": c.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT source_path AS path FROM messages
                        UNION SELECT duplicate_source_path AS path FROM duplicate_copies
                    )
                """).fetchone()[0],
                "attachments": c.execute("SELECT COALESCE(SUM(attachment_count),0) FROM messages").fetchone()[0],
                "duplicates": c.execute("SELECT COUNT(*) FROM duplicate_copies").fetchone()[0],
            }

    def search(self, query: str = "", limit: int = 500):
        q = f"%{query.strip()}%"
        with self._lock:
            if not query.strip():
                return self.conn.execute(
                    "SELECT * FROM messages ORDER BY discovered_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return self.conn.execute("""
                SELECT * FROM messages
                WHERE sender LIKE ? OR recipient LIKE ? OR subject LIKE ? OR body_text LIKE ?
                ORDER BY discovered_at DESC LIMIT ?
            """, (q, q, q, q, limit)).fetchall()

    def get(self, message_id: int):
        with self._lock:
            return self.conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()

    def message_metadata(self):
        with self._lock:
            return self.conn.execute("""
                SELECT id,sender,recipient,subject,date_text,source_path,source_format,
                       status,attachment_count,message_hash
                FROM messages ORDER BY id
            """).fetchall()

    def duplicate_metadata(self):
        with self._lock:
            return self.conn.execute("""
                SELECT message_hash, original_message_id, duplicate_source_path,
                       duplicate_format, detected_at
                FROM duplicate_copies ORDER BY id
            """).fetchall()
