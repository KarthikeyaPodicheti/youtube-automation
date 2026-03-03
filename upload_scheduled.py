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
DRIVE_FOLDER_ID = "1cvoTxqR16D3HdmlKc_RWYoPnNymVt0et"   # Carkrash2026 Drive folder
PROCESSED_LOG   = "processed_videos.json"
TOKEN_FILE      = "token.pickle"

# Both scopes in one token — Drive read + YouTube upload
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.readonly",
]

TITLES = [
    "Speed Bumps vs ALIEN TRACTOR BEAM! �🚗",
    "100 MPH vs CONCRETE WALL! 🧱💥",
    "Can This Car Survive The HUGE Drop? 🚙⬇️",
    "Cars vs Giant Pit! 🕳️🚗",
    "Most Satisfying Car Crashes 💥",
    "Will It Cross The Bridge? 🌉🚗",
    "Mega Ramp Jumps Gone Wrong! 😱🚀",
    "Crushing Cars with Giant Hammer! 🔨💥",
    "High Speed Police Chases! 🚓💨",
    "BeamNG.drive Crashes & Insane Moments! 🎮💥",
    "Dodging 100 Spikes at Max Speed! 🎯🏎️",
    "Can This Truck Pull 100 Cars? 🚛🚙",
    "Cars vs Giant Stairs! 🪜🚗",
    "Train Crash Simulation in BeamNG! 🚂💥",
    "Escaping a Giant Tornado! 🌪️🏎️",
    "Cars Trying to Drive on Ice! 🧊🚙",
    "Can a Tank Stop a Train? 🚂🛡️",
    "Cars vs Water Slides! 💦🎢",
    "Driving Over 100 Speed Bumps! 💥🚙",
    "Giant Bowling with Cars! 🎳🚗",
    "Lava Pit Challenge in BeamNG! 🌋🔥",
    "Cars vs Landmines! 💣💥",
    "Supercars Destroyed in Seconds! 🏎️🔥",
    "What Happens When You Ignore The Stop Sign? 🛑💥",
    "Ultimate Car Destruction Derby! 💥🏎️",
    "Will a Parachute Save This Dropping Car? 🪂⬇️",
    "Impossible Leap Over 100 School Buses! 🚌🚀",
    "Cars Competing in Squid Game! 🦑🟢",
    "Can You Drive with Square Wheels? 🟩🚗",
    "Cars vs Giant Mouse Traps! 🪤🚙",
    "The Most Expensive Mistakes in BeamNG! 💸💥",
    "Cars Completing the Impossible Track! 🏁�",
    "Satisfying Slow-Mo Car Crashes! ⏱️�💥",
    "Driving a Bus Off a Cliff! 🚌📉",
    "Brake Failure on Steep Mountain! ⛰️📉",
    "Cars vs Giant Blender! 🌪️🚗",
    "Will The Suspension Break? 🛠️💥",
    "Can a Mini Cooper Pull a Plane? ✈️🚗",
    "Cars vs Anti-Tank Obstacles! 🚧💥",
    "Traffic Jam Annihilation! 🚦🚙",
    "Monster Truck crushes 50 Cars! 🛻💥",
    "Driving a Couch at 100 MPH! 🛋️💨",
    "Cars vs Giant Dominoes! 🧱🚗",
    "Testing Insane Car Physics! 🧪🚗",
    "Can This Car Drive Upside Down? 🙃🏎️",
    "The Most Dangerous Road in the World! 🛣️⚠️",
    "Zombie Apocalypse Survival Vehicles Test! 🧟‍♂️🚙",
    "Driving Through a Virtual Hurricane! 🌀🚗",
    "Cars vs Lava River! 🌋🛶",
    "Will The Car Float or Sink? 🚤⬇️"
]

DESCRIPTION = """Epic BeamNG Drive car crashes, simulation fails, and brutal destruction! 🚗💥
Are you satisfied watching these high-speed crashes and insane physics simulations?
Hit subscribe for daily satisfying crash shorts and gaming moments! 🔔

#beamng #carcrashes #gaming #shorts #beamngdrive #carfails #simulation #smash #destruction #satisfying #funnycrashes #crashtest"""

TAGS = [
    "beamng", "beamng drive", "car crashes", "gaming", "beamng crashes",
    "car fails", "simulation", "cars", "beamng drive shorts", "smash",
    "destruction", "satisfying crashes", "crash test", "mega ramp",
    "high speed crash", "funny car fails", "video games", "gta5 crashes",
    "insane crashes", "bridge crash", "speed bumps", "police chase", "car smash",
    "car jumping", "car stunts"
]

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
        try:
            with open(PROCESSED_LOG, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    processed = set(data)
        except (json.JSONDecodeError, ValueError):
            pass

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
        try:
            with open("upload_history.json", "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    history = data
        except (json.JSONDecodeError, ValueError):
            pass
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
        try:
            with open("daily_upload_count.json", "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    daily = data
        except (json.JSONDecodeError, ValueError):
            pass
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
