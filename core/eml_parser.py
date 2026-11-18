from pathlib import Path
from .email_parser import parse_message

def parse_eml(path: Path) -> dict:
    raw = Path(path).read_bytes()
    return parse_message(raw, str(path), "EML")
