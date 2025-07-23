import asyncio
from aiohttp import ClientSession
from pathlib import Path
from .config import Config
from .helpers import get_since_iso
from blinkpy.blinkpy import Blink, BlinkSyncModule
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load
from typing import Iterable, Dict, List, Any
from datetime import datetime, timedelta
from shutil import copy2

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
    blink.auth = Auth(await json_load(Config.CREDFILE), session=session)
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
    path = Path(Config.MEDIA_DIR)/camera_name
    path.mkdir(exist_ok=True, parents=True)
    await camera.image_to_file(str(path/Config.LAST_IMAGE_FILENAME))
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
        path = Path(Config.MEDIA_DIR)/name
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

async def download_clips_index_and_sort(
    names: Iterable[str],
    since_iso: str
) -> Dict[str, List[str]]:
    """
    Downloads new Blink clips into a central index, sorts into date folders,
    and maintains a 'latest' folder based on time or count settings
    since the given ISO8601 timestamp.

    The /.idx directory stores empty files that match the filename of a sorted
    video file.

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
            already in the /.idx directory.

    Raises:
        HTTPException:
            If Blink returns a 404 or other error when targeting a specific camera.
    """
    blink, session = await start_blink()
    await blink.refresh()

    base = Path(Config.MEDIA_DIR)
    idx_path = base / ".idx"
    latest_path = base / "latest"
    idx_path.mkdir(parents=True, exist_ok=True)
    latest_path.mkdir(parents=True, exist_ok=True)

    results: Dict[str, List[str]] = {}

    for name in names:
        cam_base = base / name if name != "all" else base
        cam_base.mkdir(parents=True, exist_ok=True)

        before = {f.name for f in idx_path.iterdir() if f.is_file()}
        kwargs = {"since": since_iso, "delay": 2}
        if name != "all":
            kwargs["camera"] = name

        await blink.download_videos(str(idx_path), **kwargs)

        after = {f.name for f in idx_path.iterdir() if f.is_file()}
        new_files = sorted(after - before)
        results[name] = []

        for fname in new_files:
            src = idx_path / fname
            mtime = datetime.fromtimestamp(src.stat().st_mtime)
            target_folder = cam_base / str(mtime.year) / f"{mtime.month:02d}" / f"{mtime.day:02d}"
            target_folder.mkdir(parents=True, exist_ok=True)

            dst = target_folder / fname
            src.rename(dst)
            (idx_path / fname).touch()
            results[name].append(str(dst))

            # Copy to 'latest' folder
            # Use copies instead of symlinks due to media servers like Plex not supporting them
            copy_dst = latest_path / fname
            copy2(dst, copy_dst)

    # Prune 'latest' folder
    files = sorted(
        [f for f in latest_path.iterdir() if f.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if Config.RECENTS_HOURS > 0:
        window = timedelta(hours=Config.RECENTS_HOURS)
        cutoff = datetime.now() - window
        for f in files:
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
    else:
        for f in files[Config.RECENTS_TOTAL:]:
            f.unlink()

    await session.close()
    return results

async def download_sync_clips_index_and_sort(
    names: Iterable[str],
    since_iso: str
) -> Dict[str, List[str]]:
    """
    Uses the Blink Sync Module API to download new clips into a central index,
    sort them into date folders, and maintain a 'latest' folder based on
    time or count settings since the given ISO8601 timestamp.

    Args:
        names: An iterable of camera names to target, or ['all'] to process every camera.
        since_iso: An ISO8601 timestamp; only clips created at or after this time are fetched.

    Returns:
        A mapping from each camera name (or 'all') to a list of filesystem paths
        of the clips that were just downloaded.
    """
    # Initialize blink session
    blink, session = await start_blink()
    await blink.start()
    await blink.setup_post_verify()

    # Use the network's first sync module
    if not blink.sync:
        raise RuntimeError("No Sync Modules found")
    net_name = next(iter(blink.sync))
    sync: BlinkSyncModule = blink.sync[net_name]

    # Prepare folders
    base        = Path(Config.MEDIA_DIR)
    idx_path    = base / ".idx"
    latest_path = base / "latest"
    idx_path.mkdir(parents=True, exist_ok=True)
    latest_path.mkdir(parents=True, exist_ok=True)

    results: Dict[str, List[str]] = {n: [] for n in names}

    # Refresh sync module manifest until ready
    sync._local_storage["manifest"].clear()
    while True:
        await sync.refresh()
        if sync.local_storage_manifest_ready:
            break
        await asyncio.sleep(1)

    # Filter the manifest of what to download
    since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
    manifest = sync._local_storage["manifest"]

    for cam_name in names:
        # Track existing index files to detect new ones
        before = {p.name for p in idx_path.iterdir() if p.is_file()}

        items = [
            item for item in manifest
            if item.created_at >= since_dt
            and (cam_name == "all" or item.name == cam_name)
        ]

        # Download each clip
        for item in items:
            # Build filename and idx path
            filename = f"{item.name}_{item.created_at.isoformat().replace(':','_')}.mp4"
            idx_file = idx_path / filename

            # Skip if we've already downloaded this clip
            if idx_file.exists():
                continue

            await item.prepare_download(blink)
            await item.download_video(blink, str(idx_file))

            # Intentional throttle when working the API
            await asyncio.sleep(2)

        # Determine the new files
        after    = {p.name for p in idx_path.iterdir() if p.is_file()}
        new_files = sorted(after - before)

        # Copy the file to the appropriate sorted folder
        # and create the placeholder idx file
        for fname in new_files:
            src = idx_path / fname
            mtime = datetime.fromtimestamp(src.stat().st_mtime)
            datedir = base / (cam_name if cam_name!="all" else "") \
                       / str(mtime.year) / f"{mtime.month:02d}" / f"{mtime.day:02d}"
            datedir.mkdir(parents=True, exist_ok=True)

            dst = datedir / fname
            src.rename(dst)

            # Touch to create an empty file with the file name
            # (This acts as a placeholder in the unsorted directory)
            (idx_path / fname).touch()

            # Copy the new files into latest
            copy2(dst, latest_path / fname)

            results[cam_name].append(str(dst))

    # Prune the /latest folder using RECENTS_HOURS or RECENTS_TOTAL
    all_latest = sorted(
        [f for f in latest_path.iterdir() if f.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if Config.RECENTS_HOURS > 0:
        cutoff = datetime.now() - timedelta(hours=Config.RECENTS_HOURS)
        for f in all_latest:
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
    else:
        for f in all_latest[Config.RECENTS_TOTAL:]:
            f.unlink()

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
