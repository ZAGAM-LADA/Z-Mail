from pathlib import Path

APP_DIR = Path.home() / ".local" / "share" / "z-mail-recovery"
DATA_DIR = APP_DIR / "data"
EXPORT_DIR = APP_DIR / "exports"
DB_PATH = DATA_DIR / "zmail.sqlite3"
LOG_PATH = APP_DIR / "zmail.log"

def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
