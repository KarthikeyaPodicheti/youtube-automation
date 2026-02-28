#!/usr/bin/env python3
"""
🚜 FARMERLIFE2.0 YouTube Automation
Uploads random videos from Drive to FARMERLIFE2.0 YouTube channel
"""

import os
import json
import pickle
import random
import sys
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# FARMERLIFE2.0 Configuration
DRIVE_FOLDER_ID = '1kocgFg0rzsMCtXsrWiOH_oditWshBpbV'  # Your Drive folder
PROCESSED_LOG = 'processed_videos.json'
TOKEN_FILE = 'token.pickle' 
SERVICE_ACCOUNT = 'service-account-key.json'

# FARMERLIFE2.0 Video Titles (customize for your farming content)
TITLES = [
    "This Farming Technique Will SHOCK You! 🚜",
    "You Won't Believe What Happened on the Farm!",
    "The Truth About Modern Farming Nobody Tells You",
    "I Tried This Farm Hack For 30 Days...",
    "What Happens Next Will Change Everything",
    "They Didn't Want You To See This Farm Secret",
    "This Is Why Small Farms Are Failing",
    "The Hidden Truth About Farm Life",
    "I Can't Believe This Farming Method Worked",
    "This Will Transform Your Farm Forever",
    "The Future of Farming is HERE! 🌾",
    "Farm Life Reality Check - Raw Truth",
    "This Farming Innovation is INSANE",
    "Why I Quit My Job to Start Farming",
    "The Dark Side of Industrial Agriculture",
]

def get_youtube_creds():
    """Load YouTube API credentials from token.pickle"""
    with open(TOKEN_FILE, 'rb') as f:
        return pickle.load(f)

def get_drive_creds():
    """Load Drive API credentials from service account"""
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )

def get_unprocessed_videos(drive):
    """Get list of videos not yet uploaded"""
    processed = set()
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r') as f:
            processed = set(json.load(f))
    
    videos = []
    page_token = None
    
    while True:
        response = drive.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and trashed = false",
            fields='nextPageToken, files(id, name, mimeType, shortcutDetails)',
            pageToken=page_token,
            pageSize=100
        ).execute()
        
        for f in response.get('files', []):
            # Handle shortcuts to videos (common in shared Drive folders)
            if f['mimeType'] == 'application/vnd.google-apps.shortcut':
                if 'shortcutDetails' in f:
                    real_id = f['shortcutDetails']['targetId']
                    videos.append({'id': f['id'], 'real_id': real_id, 'name': f['name']})
            # Handle direct video files
            elif f['mimeType'].startswith('video/'):
                videos.append({'id': f['id'], 'real_id': f['id'], 'name': f['name']})
        
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    
    unprocessed = [v for v in videos if v['id'] not in processed]
    return unprocessed, processed

def download_video(drive, video_id, name):
    """Download video from Drive to temporary file"""
    # Clean filename for local storage
    clean_name = "".join(c for c in name if c.isalnum() or c in '._-').rstrip()
    if not clean_name.endswith('.mp4'):
        clean_name += '.mp4'
    
    local_path = f"/tmp/farmerlife_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{clean_name}"
    
    request = drive.files().get_media(fileId=video_id)
    
    with open(local_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    
    return local_path

def upload_video():
    """Main upload function"""
    print(f"\n{'='*70}")
    print(f"🚜 FARMERLIFE2.0 YOUTUBE UPLOAD")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*70}\n")
    
    print("[1/5] 🔧 Initializing APIs...")
    youtube_creds = get_youtube_creds()
    youtube = build('youtube', 'v3', credentials=youtube_creds, cache_discovery=False)
    
    drive_creds = get_drive_creds()
    drive = build('drive', 'v3', credentials=drive_creds)
    print("  ✅ APIs ready")
    
    print("\n[2/5] 📁 Checking Drive for farming videos...")
    unprocessed, processed = get_unprocessed_videos(drive)
    
    if not unprocessed:
        print("  ❌ No unprocessed videos found in Drive folder!")
        print(f"  📂 Folder: https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}")
        return False
    
    print(f"  ✅ {len(unprocessed)} unprocessed videos available")
    print(f"  📊 {len(processed)} videos already uploaded")
    
    # Randomly select video
    video = random.choice(unprocessed)
    print(f"\n[3/5] 🎯 Selected: {video['name']}")
    
    print("\n[4/5] ⬇️ Downloading from Drive...")
    local_path = download_video(drive, video['real_id'], video['name'])
    size_mb = os.path.getsize(local_path) / (1024*1024)
    print(f"  ✅ Downloaded: {size_mb:.1f} MB")
    
    print("\n[5/5] ⬆️ Uploading to FARMERLIFE2.0...")
    
    # Generate title with sequential number
    title = random.choice(TITLES) + f" #{len(processed)+1}"
    
    # Farming-focused description
    description = f"""🚜 Welcome to FARMERLIFE2.0! 

Join our farming community for the latest agricultural insights, sustainable farming practices, and real farm life experiences.

🌾 What you'll get:
• Practical farming tips and techniques
• Equipment reviews and recommendations  
• Sustainable agriculture methods
• Real stories from the field

Subscribe for daily farming content! 🔔

#Farming #Agriculture #FarmLife #Sustainable #FARMERLIFE2.0"""
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': [
                'farming', 'agriculture', 'farmlife', 'sustainable', 
                'farmers', 'crops', 'rural', 'food', 'harvest',
                'tractor', 'equipment', 'organic', 'homestead'
            ],
            'categoryId': '26',  # Howto & Style
        },
        'status': {
            'privacyStatus': 'public',
            'madeForKids': False
        }
    }
    
    media = MediaFileUpload(local_path, mimetype='video/mp4', resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"  📤 Upload progress: {progress}%")
    
    video_id = response['id']
    
    # Update processed videos log
    processed.add(video['id'])
    with open(PROCESSED_LOG, 'w') as f:
        json.dump(list(processed), f)
    
    # Update upload history
    history = []
    if os.path.exists('upload_history.json'):
        with open('upload_history.json', 'r') as f:
            history = json.load(f)
    
    history.append({
        'timestamp': datetime.now().isoformat(),
        'title': title,
        'video_id': video_id,
        'drive_file': video['name'],
        'file_size_mb': round(size_mb, 1)
    })
    
    with open('upload_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    # Update daily upload count
    today = datetime.now().strftime('%Y-%m-%d')
    daily_count = {'date': today, 'count': 0}
    
    if os.path.exists('daily_upload_count.json'):
        with open('daily_upload_count.json', 'r') as f:
            daily_count = json.load(f)
    
    if daily_count.get('date') != today:
        daily_count = {'date': today, 'count': 0}
    
    daily_count['count'] += 1
    
    with open('daily_upload_count.json', 'w') as f:
        json.dump(daily_count, f, indent=2)
    
    # Clean up temporary file
    os.remove(local_path)
    
    print(f"\n{'='*70}")
    print(f"🎉 SUCCESS! Video uploaded to FARMERLIFE2.0")
    print(f"📺 Title: {title}")
    print(f"🔗 URL: https://youtu.be/{video_id}")
    print(f"📊 Today's uploads: {daily_count['count']}")
    print(f"🎬 Remaining videos: {len(unprocessed)-1}")
    print(f"💾 File size: {size_mb:.1f} MB")
    print(f"{'='*70}\n")
    
    return True

if __name__ == '__main__':
    try:
        success = upload_video()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)