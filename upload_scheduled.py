import os
import json
import random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def load_processed_videos():
    if os.path.exists("processed_videos.json"):
        with open("processed_videos.json", "r") as file:
            return json.load(file)
    return []

def save_processed_video(video_id):
    processed_videos = load_processed_videos()
    processed_videos.append(video_id)
    with open("processed_videos.json", "w") as file:
        json.dump(processed_videos, file)

def pick_random_video():
    video_folder = "path_to_drive_videos"
    video_files = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
    processed_videos = load_processed_videos()
    unprocessed_videos = [v for v in video_files if v not in processed_videos]

    if not unprocessed_videos:
        print("No new videos to upload!")
        return None

    return random.choice(unprocessed_videos)

def upload_video(video_path, title, description, tags):
    creds = Credentials.from_authorized_user_file("token.pickle", [
        "https://www.googleapis.com/auth/youtube.upload"])

    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "24"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media_file = MediaFileUpload(video_path)

    youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    ).execute()

    save_processed_video(video_path)

def main():
    titles = [
        "What Happens Next Will Surprise You! 😲",
        "A Magical Story You Can't Miss! 🪄",
        "This Tale Will Touch Your Heart ❤️",
        "When the Unexpected Happens... 🌟",
        "A Fascinating Story for Everyone! 🎬"
    ]

    descriptions = """
    Experience the magic of Hindi short stories. These tales are captivating, filled with life lessons, and spark joy and imagination. Subscribe for daily uploads!
    """

    tags = [
        "Hindi animation", "short stories", "magical tales", "family content", "kids friendly"
    ]

    selected_video = pick_random_video()

    if selected_video:
        upload_video(
            video_path=f"path_to_drive_videos/{selected_video}",
            title=random.choice(titles),
            description=descriptions,
            tags=tags
        )

if __name__ == "__main__":
    main()