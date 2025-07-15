from flask import abort
from datetime import datetime, timezone
from .config import Config

def get_since_iso() -> str:
    """
    Compute an ISO-formatted timestamp representing the cutoff for downloads.

    Subtracts a fixed TIMEDELTA from the current UTC time to determine
    how far back to fetch clips.

    Returns:
        str: An ISO-formatted timestamp (e.g. "2025-07-01T12:34:56.789012+00:00").
    """
    now_utc = datetime.now(timezone.utc)
    return (now_utc - Config.TIMEDELTA).isoformat()

def normalize_camera_names(cams):
    """
    Ensure camera_name input is normalized to a list of strings.

    Accepts either a single string or a list of strings. Raises an error
    if the input is of any other type.

    Args:
        cams (str | list[str]): A camera name or list of camera names.

    Returns:
        list[str]: A list of camera names.

    Raises:
        HTTPException(400): If `cams` is not a string or a list.
    """
    if isinstance(cams, str):
        return [cams]
    if isinstance(cams, list):
        return cams
    abort(400, "'camera_name' must be a string or list of strings")
