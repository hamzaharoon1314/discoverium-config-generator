import hashlib
from pathlib import Path

def sanitize_filename(name: str) -> str:
    return name.replace("/", "__").replace("\\", "__")

def calculate_sha256(path: Path) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()