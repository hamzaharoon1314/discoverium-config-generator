from dataclasses import dataclass

@dataclass
class ApkInfo:
    asset_name: str
    app_name: str
    package_id: str
    version_name: str
    sha256: str
    size_bytes: int
    download_url: str
    play_store_url: str
    icon_filename: str = ""