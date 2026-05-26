import json
import re
import time

def generate_discoverium_config(repo, asset, row, all_assets):
    primary_name = asset["name"]
    other_assets = [[a["name"], a["browser_download_url"]] for a in all_assets if a["name"] != primary_name]

    config = {
        "id": row.package_id,
        "url": f"https://github.com/{repo}",
        "author": repo.split("/")[0],
        "name": row.app_name,
        "installedVersion": "",
        "latestVersion": "",
        "apkUrls": json.dumps([[primary_name, row.download_url]]),
        "otherAssetUrls": json.dumps(other_assets),
        "preferredApkIndex": 0,
        "additionalSettings": json.dumps({
            "includePrereleases": False,
            "fallbackToOlderReleases": True,
            "filterReleaseTitlesByRegEx": "",
            "filterReleaseNotesByRegEx": "",
            "verifyLatestTag": False,
            "sortMethodChoice": "date",
            "useLatestAssetDateAsReleaseDate": True,
            "releaseTitleAsVersion": False,
            "trackOnly": False,
            "versionExtractionRegEx": "",
            "matchGroupToUse": "",
            "versionDetection": False,
            "releaseDateAsVersion": True,
            "useVersionCodeAsOSVersion": False,
            "apkFilterRegEx": "^" + re.escape(primary_name).replace("\\.apk", ".*\\.apk$"),
            "invertAPKFilter": False,
            "autoApkFilterByArch": True,
            "appName": row.app_name,
            "appAuthor": repo.split("/")[0],
            "shizukuPretendToBeGooglePlay": False,
            "allowInsecure": False,
            "exemptFromBackgroundUpdates": False,
            "skipUpdateNotifications": False,
            "about": "",
            "refreshBeforeDownload": False,
            "dontSortReleasesList": False
        }),
        "lastUpdateCheck": int(time.time() * 1000000),
        "pinned": False,
        "categories": [],
        "releaseDate": None,
        "changeLog": None,
        "overrideSource": None,
        "allowIdChange": False,
    }
    return config

def markdown_table(rows, repo, release):
    lines = [
        f"# Android APK Package ID & Discoverium Config Generator for `{repo}`\n",
        f"Release source: `{release}`\n",
        "| App | Package ID | Asset Filename | Version | Play Store | Config  |",
        "|---|---|---|---|---|---|"
    ]

    for row in rows:
        safe_asset_name = row.asset_name.replace(".apk", "").replace("/", "_").replace("\\", "_")
        safe_display_name = row.asset_name.replace("|", "\\|")
        play_url = f"[Play Store]({row.play_store_url})" if row.play_store_url else "N/A"
        lines.append(
            f"| **{row.app_name}** | {row.package_id} | {safe_display_name} | {row.version_name} | {play_url} | [JSON Config](./discoverium/{row.package_id}__{safe_asset_name}.json) |"
        )

    lines.extend(["\n## SHA256\n"])
    for row in rows:
        lines.extend([f"- **{row.asset_name}**", f"  - `{row.sha256}`"])

    lines.append("\n_Automatically generated from GitHub APK release assets with package IDs, SHA256 hashes, and Discoverium import links._")
    return "\n".join(lines)