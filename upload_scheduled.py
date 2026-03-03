#!/usr/bin/env python3
"""
YouTube Automation Upload Script
Fetches a random unprocessed video from Google Drive and uploads it to YouTube.
Uses:
 - Service Account JSON  → for Drive access (read videos)
 - token.pickle (OAuth)  → for YouTube upload (must be pre-generated locally)
"""

import os
import json
import pickle
import random
import sys
from datetime import datetime
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DRIVE_FOLDER_ID = "1kocgFg0rzsMCtXsrWiOH_oditWshBpbV"   # Your Google Drive folder
PROCESSED_LOG   = "processed_videos.json"
TOKEN_FILE      = "token.pickle"
SERVICE_ACCOUNT = "google_service_account.json"   # already committed to repo

SCOPES_YOUTUBE = ["https://www.googleapis.com/auth/youtube.upload"]

TITLES = [
    "What Happens Next Will Surprise You! 😲",
    "A Magical Story You Can't Miss! 🪄",
    "This Tale Will Touch Your Heart ❤️",
    "When the Unexpected Happens... 🌟",
    "A Fascinating Story for Everyone! 🎬",
    "You Won't Believe THIS Happened! 😱",
    "The Truth Nobody Tells You 🤔",
    "This Will Blow Your Mind 🤯",
    "A Story That Will Change Your Life 💫",
    "Watch This Before It's Gone! ⚡",
]

DESCRIPTION = """
Experience the magic of Hindi short stories. These tales are captivating,
filled with life lessons, and spark joy and imagination.
Subscribe for daily uploads! 🔔

#HindiStories #Animation #ShortStories #KidsContent #MagicalTales
"""

TAGS = ["Hindi animation", "short stories", "magical tales", "family content", "kids friendly", "Hindi"]

# ─── CREDENTIALS ───────────────────────────────────────────────────────────────

def get_youtube_credentials():
    """
    Load YouTube OAuth credentials from token.pickle.
    Auto-refreshes if expired. Never opens a browser (safe for CI).
    """
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError(
            f"'{TOKEN_FILE}' not found!\n"
            "Generate it locally first (run this script locally once to authenticate),\n"
            "then base64-encode it and add it as the GOOGLE_TOKEN GitHub Secret."
        )

    # token.pickle can be either a real pickle file OR a JSON string (from creds.to_json())
    try:
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    except Exception:
        # Fallback: treat as JSON (our new format)
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES_YOUTUBE)

    if creds.expired and creds.refresh_token:
        print("🔄 YouTube token expired — refreshing...")
        creds.refresh(Request())
        # Save refreshed token back so the workflow can commit it
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        print("✅ Token refreshed and saved.")
    elif not creds.valid:
        raise RuntimeError(
            "YouTube credentials are invalid and cannot be refreshed automatically.\n"
            "Please re-authenticate locally, re-encode the token, and update the GOOGLE_TOKEN secret."
        )

    return creds


def get_drive_credentials():
    """Service Account credentials for reading Google Drive."""
    if not os.path.exists(SERVICE_ACCOUNT):
        raise RuntimeError(
            f"'{SERVICE_ACCOUNT}' not found!\n"
            "Add the GOOGLE_SERVICE_ACCOUNT secret (base64-encoded service-account-key.json)."
        )
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )


# ─── DRIVE ─────────────────────────────────────────────────────────────────────

def get_unprocessed_videos(drive):
    """List all video files in Drive folder that haven't been uploaded yet."""
    processed = set()
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, "r") as f:
            processed = set(json.load(f))

    videos = []
    page_token = None

    while True:
        response = drive.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, mimeType, shortcutDetails)",
            pageToken=page_token,
            pageSize=100
        ).execute()

        for file in response.get("files", []):
            if file["mimeType"] == "application/vnd.google-apps.shortcut":
                if "shortcutDetails" in file:
                    real_id = file["shortcutDetails"]["targetId"]
                    videos.append({"id": file["id"], "real_id": real_id, "name": file["name"]})
            elif file["mimeType"].startswith("video/"):
                videos.append({"id": file["id"], "real_id": file["id"], "name": file["name"]})

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    unprocessed = [v for v in videos if v["id"] not in processed]
    return unprocessed, processed


def download_video(drive, video_id, name):
    """Download a video file from Drive to /tmp."""
    clean_name = "".join(c for c in name if c.isalnum() or c in "._-").rstrip()
    if not clean_name.endswith(".mp4"):
        clean_name += ".mp4"

    local_path = f"/tmp/upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{clean_name}"

    request = drive.files().get_media(fileId=video_id)
    with open(local_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"  Download progress: {int(status.progress() * 100)}%")

    return local_path


# ─── YOUTUBE ───────────────────────────────────────────────────────────────────

def upload_to_youtube(youtube, local_path, title):
    """Upload a local video file to YouTube."""
    body = {
        "snippet": {
            "title": title,
            "description": DESCRIPTION,
            "tags": TAGS,
            "categoryId": "24",  # Entertainment
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False,
        }
    }

    media = MediaFileUpload(local_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload progress: {int(status.progress() * 100)}%")

    return response["id"]


# ─── TRACKING ──────────────────────────────────────────────────────────────────

def update_tracking(video_id, title, processed, video_file_id):
    """Update processed_videos.json, upload_history.json, and daily_upload_count.json."""
    processed.add(video_file_id)
    with open(PROCESSED_LOG, "w") as f:
        json.dump(list(processed), f)

    history = []
    if os.path.exists("upload_history.json"):
        with open("upload_history.json", "r") as f:
            history = json.load(f)
    history.append({
        "timestamp": datetime.now().isoformat(),
        "title": title,
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}"
    })
    with open("upload_history.json", "w") as f:
        json.dump(history, f, indent=2)

    today = datetime.now().strftime("%Y-%m-%d")
    daily = {"date": today, "count": 0}
    if os.path.exists("daily_upload_count.json"):
        with open("daily_upload_count.json", "r") as f:
            daily = json.load(f)
    if daily.get("date") != today:
        daily = {"date": today, "count": 0}
    daily["count"] += 1
    with open("daily_upload_count.json", "w") as f:
        json.dump(daily, f, indent=2)

    return daily["count"]


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"🚜 YOUTUBE UPLOAD — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")
    print(f"{'='*60}\n")

    print("[1/5] Initializing APIs...")
    yt_creds    = get_youtube_credentials()
    drive_creds = get_drive_credentials()
    youtube = build("youtube", "v3", credentials=yt_creds,    cache_discovery=False)
    drive   = build("drive",   "v3", credentials=drive_creds, cache_discovery=False)
    print("  ✅ APIs ready\n")

    print("[2/5] Scanning Drive for unprocessed videos...")
    unprocessed, processed = get_unprocessed_videos(drive)
    if not unprocessed:
        print("  ⚠️  No new videos to upload. Add more videos to the Drive folder.")
        sys.exit(0)
    print(f"  ✅ {len(unprocessed)} unprocessed videos found\n")

    video = random.choice(unprocessed)
    print(f"[3/5] Selected: {video['name']}\n")

    print("[4/5] Downloading from Drive...")
    local_path = download_video(drive, video["real_id"], video["name"])
    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"  ✅ Downloaded: {size_mb:.1f} MB\n")

    print("[5/5] Uploading to YouTube...")
    title    = random.choice(TITLES)
    video_id = upload_to_youtube(youtube, local_path, title)
    os.remove(local_path)   # Clean up temp file

    daily_count = update_tracking(video_id, title, processed, video["id"])

    print(f"\n{'='*60}")
    print(f"✅ SUCCESS!")
    print(f"   Video : {title}")
    print(f"   URL   : https://youtu.be/{video_id}")
    print(f"   Today : {daily_count} upload(s)")
    print(f"   Left  : {len(unprocessed) - 1} videos remaining")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
