import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "site"

# Railway sets these on every deploy; locally they are absent.
ON_RAILWAY = any(os.getenv(k) for k in ("RAILWAY_ENVIRONMENT_NAME", "RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dogeverlasting.db")

# Uploaded photos and film live on a Railway volume. Railway sets
# RAILWAY_VOLUME_MOUNT_PATH when one is attached; without a volume, every
# deploy would wipe a family's uploads.
_volume = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
MEDIA_DIR = Path(os.getenv("MEDIA_DIR") or (Path(_volume) / "media" if _volume else ROOT / "media"))

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "letmein")

MAX_PHOTO_BYTES = 30 * 1024 * 1024
MAX_VIDEO_BYTES = 250 * 1024 * 1024


def check_production_config() -> None:
    """Refuse to start on Railway with settings that would lose data or leave /admin open.

    A failed deploy keeps the previous one live, so this is the safe way to find out.
    """
    if not ON_RAILWAY:
        return
    missing = []
    if not os.getenv("DATABASE_URL"):
        missing.append("DATABASE_URL (add the Postgres plugin)")
    if not (_volume or os.getenv("MEDIA_DIR")):
        missing.append("a volume mounted at /data (uploads would be lost on every deploy)")
    if not os.getenv("ADMIN_PASSWORD"):
        missing.append("ADMIN_PASSWORD")
    if missing:
        raise RuntimeError("Refusing to start on Railway. Missing: " + "; ".join(missing))
