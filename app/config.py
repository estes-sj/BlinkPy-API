import os
from datetime import timedelta

def get_env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default

class Config:
    CREDFILE = "./credentials.json"
    MEDIA_DIR = "./media"
    LAST_IMAGE_FILENAME = "last_snap.jpg"
    TIMEDELTA = timedelta(hours=int(os.getenv("TIMEDELTA", 6)))
    RECENTS_HOURS = get_env_int("RECENTS_HOURS", 0)
    # Maximum number of videos to keep in 'latest' when RECENTS_HOURS == 0
    RECENTS_TOTAL = get_env_int("RECENTS_TOTAL", 20)