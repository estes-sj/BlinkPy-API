import os
from datetime import timedelta

TIMEDELTA = timedelta(hours=int(os.getenv("TIMEDELTA", 6)))
CREDFILE  = "./credentials.json"
MEDIA_DIR = "./media"
LAST_IMAGE_FILENAME = "last_snap.jpg"
