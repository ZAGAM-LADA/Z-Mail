import json
from datetime import datetime, timezone
from pathlib import Path

def write_json_report(db, destination, root_path):
    report = {
        "product": "Z-MAIL RECOVERY — Premium Edition",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "investigated_root": str(root_path),
        "statistics": db.counts(),
        "messages": [dict(row) for row in db.message_metadata()],
        "duplicate_copies": [dict(row) for row in db.duplicate_metadata()],
        "limitations": [
            "Only messages found in accessible sources are included.",
            "Permanently deleted Gmail server messages cannot be fetched by this local scanner.",
            "Deleted-file/raw-disk recovery is not implemented in this build."
        ]
    }
    Path(destination).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return destination
