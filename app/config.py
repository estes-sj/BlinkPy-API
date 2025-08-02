import os
from datetime import timedelta

def get_env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default

class Config:
    # Set paths within the container
    CREDFILE = "./credentials.json"
    MEDIA_DIR = "./media"

    # Filename of most recent snap for a specified camera
    LAST_IMAGE_FILENAME = os.getenv("LAST_IMAGE_FILENAME", "last_snap.jpg")
    
    # How many past hours to look back for new media
    TIMEDELTA = timedelta(hours=get_env_int("TIMEDELTA_HOURS", 6))
    
    # If > 0, only include videos within the last X hours
    RECENTS_HOURS = get_env_int("RECENTS_HOURS", 0)
    
    # Maximum number of videos to keep in 'latest' when RECENTS_HOURS == 0
    RECENTS_TOTAL = get_env_int("RECENTS_TOTAL", 20)
