import os
import re
import shutil
import subprocess
import urllib.parse
import zipfile
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

def extract_app_icon(aapt: str, apk_path: Path, package_id: str, icons_dir: Path) -> str:
    """
    Extracts a web-compatible icon (PNG/WebP) from the APK. 
    Returns the saved filename, or an empty string if failed.
    """
    proc = subprocess.run([aapt, "dump", "badging", str(apk_path)], capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        return ""

    icon_paths = []
    
    # 1. Grab all DPI-specific icons
    matches = re.findall(r"application-icon-\d+:'([^']+)'", proc.stdout)
    icon_paths.extend(matches)

    # 2. Grab the master icon definition
    main_icon = re.search(r"application:.*?icon='([^']+)'", proc.stdout)
    if main_icon:
        icon_paths.append(main_icon.group(1))

    # 3. CRITICAL: Filter out Android XML vectors. Browsers can only read PNG/WebP/JPG
    raster_icons = [p for p in icon_paths if p.lower().endswith(('.png', '.webp', '.jpg'))]
    valid_path = raster_icons[-1] if raster_icons else None

    # 4. AGGRESSIVE FALLBACK: If aapt only gave us XMLs, dig into the ZIP manually
    if not valid_path:
        try:
            with zipfile.ZipFile(apk_path, 'r') as z:
                possibles = [
                    f for f in z.namelist() 
                    if f.lower().endswith(('.png', '.webp')) and 'mipmap' in f and 'ic_launcher' in f
                ]
                if possibles:
                    # Sorting usually puts xxxhdpi (highest quality) at the end
                    valid_path = sorted(possibles)[-1]
        except Exception:
            pass

    if not valid_path:
        return "" # Completely failed to find a raster image

    # 5. Extract and save the file
    try:
        with zipfile.ZipFile(apk_path, 'r') as z:
            data = z.read(valid_path)
            
        ext = valid_path.split('.')[-1].lower()
        filename = f"{package_id}.{ext}"
        
        icons_dir.mkdir(parents=True, exist_ok=True)
        out_file = icons_dir / filename
        out_file.write_bytes(data)
        
        return filename
    except Exception:
        return ""