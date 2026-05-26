import os
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path
import requests

PKG_RE = re.compile(r"package:\s+name='([^']+)'")
VERSION_RE = re.compile(r"versionName='([^']+)'")
LABEL_RE = re.compile(r"application-label(?:-[^:]+)?:'([^']+)'")

def find_aapt() -> str:
    env_path = os.environ.get("AAPT_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    for candidate in ("aapt", "aapt.exe"):
        found = shutil.which(candidate)
        if found:
            return found
    raise SystemExit("aapt not found. Install Android build-tools and set AAPT_PATH.")

def extract_badging(aapt: str, apk_path: Path):
    proc = subprocess.run([aapt, "dump", "badging", str(apk_path)], capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    
    stdout = proc.stdout
    pkg_match = PKG_RE.search(stdout)
    if not pkg_match:
        raise RuntimeError("Package ID not found")

    version_match = VERSION_RE.search(stdout)
    label_match = LABEL_RE.search(stdout)

    package_id = pkg_match.group(1)
    version_name = version_match.group(1) if version_match else "Unknown"
    app_name = label_match.group(1) if label_match else apk_path.stem

    return (app_name, package_id, version_name)

def generate_play_store_url(package_id: str) -> str:
    return "https://play.google.com/store/apps/details?id=" + urllib.parse.quote(package_id.strip())

def play_store_exists(session: requests.Session, package_id: str) -> bool:
    url = generate_play_store_url(package_id)
    try:
        r = session.get(url, timeout=15, allow_redirects=True)
        text = r.text.lower()
        return (r.status_code == 200 and "/store/apps/details" in r.url and 
                "item not found" not in text and "requested url was not found" not in text)
    except Exception:
        return False