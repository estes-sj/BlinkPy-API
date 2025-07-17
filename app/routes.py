import asyncio
from flask import Blueprint, request, jsonify, abort, url_for
from .helpers import get_since_iso, normalize_camera_names
from .blink_service import capture_image, download_clips, download_clips_index_and_sort, download_sync_clips_index_and_sort, list_cameras
from .config import Config

bp = Blueprint("api", __name__)

@bp.route("/get-camera-info", methods=["GET"])
def get_camera_info():
    """
    GET /get-camera-info
    ----------------------
    Retrieve the list of available Blink cameras.
    Returns JSON: {"cameras": [...]}
    """
    try:
        cams = asyncio.run(list_cameras())
        return jsonify(cameras=cams)
    except Exception as e:
        abort(500, str(e))

@bp.route("/snap", methods=["POST"])
def snap_camera():
    """
    POST /snap
    ----------------------
    Trigger a snapshot on the specified camera.
    Expects JSON: {"camera_name": "<name>"}
    Returns JSON: {"url": "<static image URL>"}
    """
    data = request.get_json() or {}
    if "camera_name" not in data:
        abort(400, "Missing 'camera_name'")
    try:
        asyncio.run(capture_image(data["camera_name"]))
    except Exception as e:
        abort(500, str(e))
    url = url_for("static", filename=f"{data['camera_name']}/{Config.LAST_IMAGE_FILENAME}", _external=True)
    return jsonify(url=url)

@bp.route("/download-recent-clips", methods=["POST"])
def download_recent_clips():
    """
    POST /download-recent-clips
    ----------------------
    Download clips from all (or specified) cameras since the last run.
    Expects JSON: {"camera_name": "<name>|all"} (optional)
    Returns JSON: {"since": "<ISO>", "downloaded_clips": [...]}
    """
    data = request.get_json() or {}
    names = normalize_camera_names(data.get("camera_name","all"))
    since_iso = get_since_iso()
    try:
        clips = asyncio.run(download_clips(names, since_iso))
        return jsonify(since=since_iso, downloaded_clips=clips)
    except Exception as e:
        abort(500, str(e))

@bp.route("/download-recent-clips-and-sort", methods=["POST"])
def download_recent_clips_and_sort():
    """
    POST /download-recent-clips-and-sort
    ----------------------
    Download clips from all (or specified) cameras since the last run.
    Sort into subfolders based on the timestamp and update the /latest folder.
    Expects JSON: {"camera_name": "<name>|all"} (optional)
    Returns JSON: {"since": "<ISO>", "downloaded_clips": [...]}
    """
    data = request.get_json() or {}
    names = normalize_camera_names(data.get("camera_name","all"))
    since_iso = get_since_iso()
    try:
        clips = asyncio.run(download_clips_index_and_sort(names, since_iso))
        return jsonify(since=since_iso, downloaded_clips=clips)
    except Exception as e:
        abort(500, str(e))

@bp.route("/download-recent-sync-clips-and-sort", methods=["POST"])
def download_recent_sync_clips_and_sort():
    """
    POST /download-recent-clips-and-sort
    ----------------------
    Download clips from all (or specified) cameras via the sync module since the last run.
    Sort into subfolders based on the timestamp and update the /latest folder.
    Expects JSON: {"camera_name": "<name>|all"} (optional)
    Returns JSON: {"since": "<ISO>", "downloaded_clips": [...]}
    """
    data = request.get_json() or {}
    names = normalize_camera_names(data.get("camera_name","all"))
    since_iso = get_since_iso()
    try:
        clips = asyncio.run(download_sync_clips_index_and_sort(names, since_iso))
        return jsonify(since=since_iso, downloaded_clips=clips)
    except Exception as e:
        abort(500, str(e))

@bp.route("/download-clips-since", methods=["POST"])
def download_clips_since():
    """
    POST /download-clips-since
    ----------------------
    Download clips from all (or specified) cameras since a given timestamp.
    Expects JSON: {"camera_name": "<name>|all", "since": "<ISO>"} (since optional)
    Returns JSON: {"since": "<ISO>", "downloaded_clips": [...]}
    """
    data = request.get_json() or {}
    names = normalize_camera_names(data.get("camera_name","all"))
    since_iso = data.get("since") or get_since_iso()
    try:
        clips = asyncio.run(download_clips(names, since_iso))
        return jsonify(since=since_iso, downloaded_clips=clips)
    except Exception as e:
        abort(500, str(e))

@bp.route("/download-clips-since-and-sort", methods=["POST"])
def download_clips_since_and_sort():
    """
    POST /download-clips-since-and-sort
    ----------------------
    Download clips from all (or specified) cameras since a given timestamp.
    Sort into subfolders based on the timestamp and update the /latest folder.
    Expects JSON: {"camera_name": "<name>|all", "since": "<ISO>"} (since optional)
    Returns JSON: {"since": "<ISO>", "downloaded_clips": [...]}
    """
    data = request.get_json() or {}
    names = normalize_camera_names(data.get("camera_name","all"))
    since_iso = data.get("since") or get_since_iso()
    try:
        clips = asyncio.run(download_clips_index_and_sort(names, since_iso))
        return jsonify(since=since_iso, downloaded_clips=clips)
    except Exception as e:
        abort(500, str(e))

@bp.route("/download-sync-clips-since-and-sort", methods=["POST"])
def download_sync_clips_since_and_sort():
    """
    POST /download-sync-clips-since-and-sort
    ----------------------
    Download clips from all (or specified) cameras via the sync module since the last run.
    Sort into subfolders based on the timestamp and update the /latest folder.
    Expects JSON: {"camera_name": "<name>|all"} (optional)
    Returns JSON: {"since": "<ISO>", "downloaded_clips": [...]}
    """
    data = request.get_json() or {}
    names = normalize_camera_names(data.get("camera_name","all"))
    since_iso = get_since_iso()
    try:
        clips = asyncio.run(download_sync_clips_index_and_sort(names, since_iso))
        return jsonify(since=since_iso, downloaded_clips=clips)
    except Exception as e:
        abort(500, str(e))