#!/usr/bin/env python3
import argparse
import json
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from android_utils import find_aapt, extract_badging, play_store_exists, generate_play_store_url, extract_app_icon

# Local imports
from models import ApkInfo
from utils import sanitize_filename, calculate_sha256
from github_api import normalize_repo, github_session, get_release, download_file
from android_utils import find_aapt, extract_badging, play_store_exists, generate_play_store_url
from generators import generate_discoverium_config, markdown_table

def main() -> int:
    parser = argparse.ArgumentParser(description="Android APK Metadata & Discoverium Config Generator")
    parser.add_argument("--repo", help="GitHub repo in owner/repo format")
    parser.add_argument("--release", default="latest", help="Release tag or latest")
    parser.add_argument("--keep-downloads", action="store_true")
    args = parser.parse_args()

    repo = args.repo or input("Enter GitHub repo (owner/repo or GitHub URL): ").strip()
    try:
        repo = normalize_repo(repo)
    except SystemExit as e:
        print(f"Invalid input: {e}")
        return 1
    
    safe_repo_name = sanitize_filename(repo)
    repo_dir = Path("website/public/data/repos") / safe_repo_name
    discoverium_dir = repo_dir / "discoverium"
    metadata_dir = repo_dir / "metadata"
    markdown_output = repo_dir / "index.md"
    json_output = metadata_dir / "repo.json"

    for directory in [repo_dir, discoverium_dir, metadata_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    token = os.environ.get("GITHUB_TOKEN")
    session = github_session(token)

    print(f"Fetching release data for {repo}...")
    release_data = get_release(session, repo, args.release)
    apk_assets = [a for a in release_data.get("assets", []) if a.get("name", "").lower().endswith(".apk")]

    if not apk_assets:
        print("No APK assets found.")
        return 1

    aapt = find_aapt()
    download_dir = Path("downloads")
    tmp_dir_obj = None

    if args.keep_downloads:
        download_dir.mkdir(parents=True, exist_ok=True)
    else:
        tmp_dir_obj = tempfile.TemporaryDirectory()
        download_dir = Path(tmp_dir_obj.name)

    results = []

    def process_asset(asset):
        asset_name = asset["name"]
        url = asset["browser_download_url"]
        out_path = download_dir / asset_name
        start = time.time()

        print(f"\nDownloading: {asset_name}", flush=True)
        download_file(session, url, out_path)

        print("Extracting metadata...", flush=True)
        app_name, package_id, version_name = extract_badging(aapt, out_path)
        sha256 = calculate_sha256(out_path)
        safe_asset_name = asset_name.replace(".apk", "").replace("/", "_").replace("\\", "_")
        package_id = package_id.strip()

        play_store_url = generate_play_store_url(package_id) if play_store_exists(session, package_id) else ""

        # --- NEW LOGIC: Extract the icon ---
        print("Extracting icon...", flush=True)
        saved_icon_filename = extract_app_icon(aapt, out_path, package_id, icons_dir)

        row_data = ApkInfo(
            asset_name=asset_name, app_name=app_name, package_id=package_id,
            version_name=version_name, sha256=sha256, size_bytes=int(asset.get("size", 0)),
            download_url=url, play_store_url=play_store_url,
            icon_filename=saved_icon_filename
        )        

        discoverium_config = generate_discoverium_config(repo, asset, row_data, apk_assets)
        discoverium_path = discoverium_dir / f"{package_id}__{safe_asset_name}.json"
        discoverium_path.write_text(json.dumps(discoverium_config, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"✓ {package_id} ({(time.time() - start):.2f}s)", flush=True)
        return row_data

    try:
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(process_asset, asset) for asset in sorted(apk_assets, key=lambda x: x["name"].lower())]
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"✗ {e}", flush=True)
    finally:
        if tmp_dir_obj:
            tmp_dir_obj.cleanup()

    results.sort(key=lambda x: x.app_name.lower())
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(markdown_table(results, repo, args.release), encoding="utf-8")

    json_output.write_text(
        json.dumps([{
            "app_name": r.app_name, "asset_name": r.asset_name, "package_id": r.package_id,
            "version_name": r.version_name, "sha256": r.sha256, "play_store_url": r.play_store_url,
            "download_url": r.download_url,
            "icon_filename": r.icon_filename,
            "discoverium_file": f"../discoverium/{r.package_id}__{r.asset_name.replace('.apk', '').replace('/', '_').replace('\\', '_')}.json"
        } for r in results], indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\nMarkdown updated:", markdown_output)
    print("JSON updated:", json_output)

    repo_list_path = Path("website/public/data/repos.json")
    repos_root = Path("website/public/data/repos")
    repos = sorted([p.name for p in repos_root.iterdir() if (p / "index.md").exists()])
    repo_list_path.write_text(json.dumps(repos, indent=2), encoding="utf-8")
    icons_dir = Path("website/public/data/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)

    print("\nDone.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())