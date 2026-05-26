import requests
from pathlib import Path
from typing import Optional

def normalize_repo(value: str) -> str:
    value = value.strip().rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
            break
    parts = value.split("/")
    if len(parts) < 2:
        raise SystemExit(f"Cannot parse repo from: {value!r}")
    return f"{parts[0]}/{parts[1]}"

def github_session(token: Optional[str]) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/vnd.github+json"})
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s

def get_release(session: requests.Session, repo: str, release: str):
    if release == "latest":
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        url = f"https://api.github.com/repos/{repo}/releases/tags/{release}"
    
    r = session.get(url, timeout=60)
    r.raise_for_status()
    return r.json()

def download_file(session: requests.Session, url: str, out_path: Path):
    with session.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = downloaded / total * 100
                        print(f"\r{out_path.name}: {downloaded // (1024*1024)}MB / {total // (1024*1024)}MB ({percent:.1f}%)", end="", flush=True)
        print()