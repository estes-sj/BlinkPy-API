import asyncio
from aiohttp import ClientSession
from pathlib import Path
from .config import CREDFILE, MEDIA_DIR, LAST_IMAGE_FILENAME
from .helpers import get_since_iso
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load
from typing import Iterable, Dict, List, Any

async def start_blink():
    """
    Initializes and starts a Blink session using credentials from disk.

    This function:
      1. Creates an aiohttp ClientSession.
      2. Loads credentials from the configured CREDFILE.
      3. Authenticates and starts the Blink object.
      4. Returns both the Blink instance and the underlying HTTP session.

    Returns:
        Tuple[Blink, ClientSession]:
            - The authenticated Blink client, ready for API calls.
            - The aiohttp ClientSession used by Blink (needed for cleanup).

    Raises:
        FileNotFoundError:
            If the credentials file cannot be found or opened.
        JSONDecodeError:
            If the credentials file is not valid JSON.
        BlinkAuthError:
            If authentication with Blink fails.
        BlinkLoginError:
            If starting the Blink session fails for other reasons.
    """
    session = ClientSession()
    blink   = Blink(session=session)
    blink.auth = Auth(await json_load(CREDFILE), session=session)
    await blink.start()
    return blink, session

async def capture_image(camera_name: str) -> Path:
    """    
    Uses blinkpy to request a new image for the specified camera and write it to disk.

    Includes two 5-second delays to ensure Blink updates properly.

    Args:
        camera_name (str): The name of the Blink camera to capture from.

    Returns:
        pathlib.Path: Full path to the saved image file.

    Raises:
        HTTPException(404): If the specified camera is not found.
    """
    blink, session = await start_blink()
    await blink.refresh();
    await asyncio.sleep(5)

    camera = blink.cameras.get(camera_name) or (_cleanup(session), abort(404))
    await camera.snap_picture();
    await asyncio.sleep(5)
    
    await blink.refresh(force=True)
    path = Path(MEDIA_DIR)/camera_name
    path.mkdir(exist_ok=True, parents=True)
    await camera.image_to_file(str(path/LAST_IMAGE_FILENAME))
    await session.close()

async def download_clips(
    names: Iterable[str],
    since_iso: str
) -> Dict[str, List[str]]:
    """
    Uses blinkpy to download video clips from the specified cameras since
    the given ISO8601 timestamp.  

    Includes a 2-second pause between each clip download to avoid overwhelming
    the Blink service.

    Args:
        names (Iterable[str]):
            An iterable of camera names to target, or a single element `"all"`
            to download from every camera in the account.
        since_iso (str):
            An ISO8601-formatted timestamp (e.g. `"2025-06-01T12:00:00Z"`).  
            Only clips created at or after this time will be fetched.

    Returns:
        Dict[str, List[str]]:
            A mapping from each camera name (or `"all"`) to a list of filesystem
            paths (as strings) of the clips that were just downloaded.  
            Newly added files are those present after the call that were not
            already in the directory.

    Raises:
        HTTPException:
            If Blink returns a 404 or other error when targeting a specific camera.
    """
    blink, session = await start_blink()
    await blink.refresh()
    # expand “all” etc...
    results = {}
    for name in names:
        path = Path(MEDIA_DIR)/name
        path.mkdir(exist_ok=True, parents=True)
        before = {f.name for f in path.iterdir() if f.is_file()}
        # prepare common kwargs
        kwargs = {
            "since": since_iso,
            "delay": 2,
        }
        # only pass camera= when targeting a specific camera
        if name != "all":
            kwargs["camera"] = name

        # call with positional path, then the rest
        await blink.download_videos(str(path), **kwargs)
        after = {f.name for f in path.iterdir() if f.is_file()}
        results[name] = [str(path/f) for f in sorted(after - before)]
    await session.close()
    return results

async def list_cameras() -> List[Dict[str, Any]]:
    """
    Retrieves a list of all Blink cameras and returns their attribute dictionaries.

    Connects to the Blink service, refreshes the camera list, then closes the session.

    Returns:
        List[Dict[str, Any]]: A list where each entry is the `.attributes` dict of a Blink camera.

    Raises:
        HTTPException:
            If the Blink API returns an error during refresh or retrieval.
    """
    blink, session = await start_blink()
    await blink.refresh()
    cams = [cam.attributes for cam in blink.cameras.values()]
    await session.close()
    return cams
