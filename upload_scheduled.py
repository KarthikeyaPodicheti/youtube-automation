#!/usr/bin/env python3
"""
YouTube Automation Upload Script
Fetches a random unprocessed video from Google Drive and uploads it to YouTube.

Uses ONE OAuth token (token.pickle) for BOTH Drive and YouTube.
No service account needed — eliminates the JWT signature issue entirely.
"""

import os
import json
import pickle
import random
import sys
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DRIVE_FOLDER_ID = "1kocgFg0rzsMCtXsrWiOH_oditWshBpbV"
PROCESSED_LOG   = "processed_videos.json"
TOKEN_FILE      = "token.pickle"

# Both scopes in one token — Drive read + YouTube upload
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.readonly",
]

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

DESCRIPTION = """Experience the magic of Hindi short stories. These tales are captivating,
filled with life lessons, and spark joy and imagination.
Subscribe for daily uploads! 🔔

#HindiStories #Animation #ShortStories #KidsContent #MagicalTales"""

TAGS = ["Hindi animation", "short stories", "magical tales", "family content", "kids friendly", "Hindi"]

# ─── CREDENTIALS ───────────────────────────────────────────────────────────────

def get_credentials():
    """
    Load OAuth credentials from token.pickle.
    Works for BOTH YouTube and Drive — no service account needed.
    Auto-refreshes if expired. Safe for CI/GitHub Actions.
    """
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError(
            f"'{TOKEN_FILE}' not found!\n"
            "Run generate_token.py locally to create it, then add as GOOGLE_TOKEN secret."
        )

    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)

    if creds.expired and creds.refresh_token:
        print("🔄 Token expired — refreshing...")
        creds.refresh(Request())
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        print("✅ Token refreshed and saved.")
    elif not creds.valid:
        raise RuntimeError(
            "Credentials are invalid and cannot be refreshed automatically.\n"
            "Re-run generate_token.py locally, re-encode, and update GOOGLE_TOKEN secret."
        )

    return creds


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
            "categoryId": "24",
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
    """Update processed_videos.json, upload_history.json, daily_upload_count.json."""
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
    daily["count"] = int(daily["count"]) + 1
    with open("daily_upload_count.json", "w") as f:
        json.dump(daily, f, indent=2)

    return daily["count"]


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"🚜 YOUTUBE UPLOAD — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")
    print(f"{'='*60}\n")

    print("[1/5] Initializing APIs...")
    creds   = get_credentials()
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    drive   = build("drive",   "v3", credentials=creds, cache_discovery=False)
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
    os.remove(local_path)

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
