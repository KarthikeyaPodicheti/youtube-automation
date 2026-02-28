# Automation #2 Setup Guide

**Goal:** Create a second YouTube automation exactly like CarCrash, but for a new channel with new Drive content.

**New Drive Folder:** `1kocgFg0rzsMCtXsrWiOH_oditWshBpbV`

---

## Phase 1: Google Cloud Setup (30 min)

### Step 1.1: Create/Reuse Google Cloud Project

1. Go to https://console.cloud.google.com
2. Either:
   - **Reuse existing project** (if CarCrash project has quota remaining), OR
   - **Create new project:** Click project dropdown → "NEW PROJECT" → Name it (e.g., "YouTube Automation 2")

### Step 1.2: Enable Required APIs

1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search and enable these APIs:
   - ☑️ **YouTube Data API v3**
   - ☑️ **Google Drive API**

### Step 1.3: Create OAuth 2.0 Credentials (for YouTube uploads)

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, configure **OAuth consent screen**:
   - User Type: **External**
   - App name: (e.g., "YouTube Uploader 2")
   - User support email: Your email
   - Developer contact: Your email
   - Click **SAVE AND CONTINUE**
   - Scopes: Skip (no changes needed)
   - Test users: Add your Google account email
   - Click **SAVE AND CONTINUE** → **BACK TO DASHBOARD**
4. Now create OAuth credentials:
   - Application type: **Desktop app**
   - Name: `youtube-uploader-2`
   - Click **CREATE**
5. Download the JSON file → Save as `client_secret_2.json`

### Step 1.4: Create Service Account (for Drive access)

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **Service Account**
3. Fill in:
   - Service account name: `drive-access-2`
   - Description: `Access Drive folder for automation 2`
   - Click **CREATE AND CONTINUE**
4. Skip role assignment → Click **CONTINUE** → **DONE**
5. Click on the newly created service account email
6. Go to **KEYS** tab
7. Click **ADD KEY** → **Create new key**
8. Select **JSON** format → Click **CREATE**
9. Download the JSON file → Save as `service-account-key-2.json`

### Step 1.5: Share Drive Folder with Service Account

1. Copy the service account email (looks like: `drive-access-2@your-project.iam.gserviceaccount.com`)
2. Go to your Drive folder: https://drive.google.com/drive/folders/1kocgFg0rzsMCtXsrWiOH_oditWshBpbV
3. Click **Share** button
4. Paste the service account email
5. Set permission to **Viewer** (read-only is enough)
6. Click **Done**

---

## Phase 2: YouTube Authentication (10 min)

### Step 2.1: Prepare Authentication Script

1. Create a new folder on your local machine/Codespace:
   ```bash
   mkdir ~/automation2-setup
   cd ~/automation2-setup
   ```

2. Copy `client_secret_2.json` to this folder

3. Create `authenticate_youtube_2.py`:
   ```python
   #!/usr/bin/env python3
   import os
   import pickle
   from google_auth_oauthlib.flow import Flow
   from google.auth.transport.requests import Request
   from googleapiclient.discovery import build

   SCOPES = [
       'https://www.googleapis.com/auth/youtube.upload',
       'https://www.googleapis.com/auth/youtube.readonly',
       'https://www.googleapis.com/auth/youtube.force-ssl'
   ]

   CLIENT_SECRETS_FILE = 'client_secret_2.json'
   TOKEN_FILE = 'token_2.pickle'

   def main():
       creds = None
       
       if os.path.exists(TOKEN_FILE):
           with open(TOKEN_FILE, 'rb') as token:
               creds = pickle.load(token)
       
       if not creds or not creds.valid:
           if creds and creds.expired and creds.refresh_token:
               creds.refresh(Request())
           else:
               flow = Flow.from_client_secrets_file(
                   CLIENT_SECRETS_FILE, SCOPES,
                   redirect_uri='urn:ietf:wg:oauth:2.0:oob'
               )
               
               auth_url, _ = flow.authorization_url(
                   access_type='offline',
                   include_granted_scopes='true',
                   prompt='consent'
               )
               
               print("\n*** OPEN THIS URL IN BROWSER ***")
               print(auth_url)
               print("\n" + "="*70)
               
               code = input("\nPaste authorization code: ").strip()
               flow.fetch_token(code=code)
               creds = flow.credentials
               
               with open(TOKEN_FILE, 'wb') as token:
                   pickle.dump(creds, token)
               print("✓ Token saved!")
       
       # Test connection
       youtube = build('youtube', 'v3', credentials=creds, cache_discovery=False)
       response = youtube.channels().list(part='snippet,statistics', mine=True).execute()
       
       if response['items']:
           channel = response['items'][0]
           print(f"\n✓ SUCCESS! Channel: {channel['snippet']['title']}")
       else:
           print("\n✗ No channel found!")

   if __name__ == '__main__':
       main()
   ```

### Step 2.2: Install Dependencies

```bash
pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Step 2.3: Run Authentication

```bash
python3 authenticate_youtube_2.py
```

1. Copy the URL shown
2. Open in browser
3. **Sign in with the NEW YouTube channel account** (not the CarCrash one!)
4. Grant permissions
5. Copy the authorization code
6. Paste it in the terminal
7. Verify it shows the correct channel name

**Result:** `token_2.pickle` file created

---

## Phase 3: GitHub Repo Setup (15 min)

### Step 3.1: Create New GitHub Repository

1. Go to https://github.com/new
2. Repository name: `youtube-automation-2` (or your channel name)
3. Description: (optional)
4. Visibility: **Public** (or Private if you prefer)
5. **DO NOT** initialize with README/.gitignore
6. Click **Create repository**

### Step 3.2: Encode Credentials

Run these commands in your `automation2-setup` folder:

```bash
cd ~/automation2-setup

# Encode client_secret_2.json
base64 -w 0 client_secret_2.json
# Copy output → Save somewhere safe

# Encode service-account-key-2.json
base64 -w 0 service-account-key-2.json
# Copy output → Save somewhere safe

# Encode token_2.pickle
base64 -w 0 token_2.pickle
# Copy output → Save somewhere safe
```

### Step 3.3: Add GitHub Secrets

1. Go to your new GitHub repo
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these 3 secrets:

| Secret Name | Value |
|-------------|-------|
| `GOOGLE_CLIENT_SECRET` | (base64 of client_secret_2.json) |
| `GOOGLE_SERVICE_ACCOUNT` | (base64 of service-account-key-2.json) |
| `YOUTUBE_TOKEN` | (base64 of token_2.pickle) |

---

## Phase 4: Upload Workflow Files (10 min)

### Step 4.1: Create Directory Structure

```bash
cd ~/automation2-setup
mkdir -p .github/workflows
```

### Step 4.2: Create Workflow File

Create `.github/workflows/youtube-uploads.yml`:

```yaml
name: YouTube Auto Upload

permissions:
  contents: write

on:
  schedule:
    # 3 uploads per day at 10:30 AM, 2:00 PM, and 9:30 PM IST
    - cron: '0 5 * * *'
    - cron: '30 8 * * *'
    - cron: '0 16 * * *'
  workflow_dispatch:

jobs:
  upload-video:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client httplib2

    - name: Create credential files from secrets
      run: |
        python3 << 'EOF'
        import base64
        import os

        client_secret = os.environ['GOOGLE_CLIENT_SECRET'].strip()
        with open('client_secret.json', 'wb') as f:
            f.write(base64.b64decode(client_secret))

        service_account = os.environ['GOOGLE_SERVICE_ACCOUNT'].strip()
        with open('service-account-key.json', 'wb') as f:
            f.write(base64.b64decode(service_account))

        print("Credentials created successfully")
        EOF
      env:
        GOOGLE_CLIENT_SECRET: ${{ secrets.GOOGLE_CLIENT_SECRET }}
        GOOGLE_SERVICE_ACCOUNT: ${{ secrets.GOOGLE_SERVICE_ACCOUNT }}

    - name: Run upload script
      run: python upload_scheduled.py

    - name: Update tracking and commit refreshed token
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add processed_videos.json upload_history.json daily_upload_count.json token.pickle || true
        git diff --cached --quiet || git commit -m "Update upload tracking and refresh token [skip ci]"
        git push || true
```

### Step 4.3: Create Upload Script

Create `upload_scheduled.py`:

```python
#!/usr/bin/env python3
"""
Scheduled upload script - picks random unprocessed video from Drive and uploads to YouTube.
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

# Config
DRIVE_FOLDER_ID = '1kocgFg0rzsMCtXsrWiOH_oditWshBpbV'  # NEW DRIVE FOLDER
PROCESSED_LOG = 'processed_videos.json'
TOKEN_FILE = 'token.pickle'
SERVICE_ACCOUNT = 'service-account-key.json'

TITLES = [
    # TODO: CUSTOMIZE THESE FOR YOUR NICHE
    "You Won't Believe THIS Happened! 😱",
    "This Changes Everything!",
    "The Truth Nobody Tells You",
    "I Tried This For 30 Days...",
    "What Happens Next Is INSANE",
    "They Didn't Want You To See This",
    "This Is Why You're Failing",
    "The Secret They're Hiding",
    "I Can't Believe This Worked",
    "This Will Blow Your Mind",
]

def get_youtube_creds():
    with open(TOKEN_FILE, 'rb') as f:
        return pickle.load(f)

def get_drive_creds():
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )

def get_unprocessed_videos(drive):
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
            if f['mimeType'] == 'application/vnd.google-apps.shortcut':
                if 'shortcutDetails' in f:
                    real_id = f['shortcutDetails']['targetId']
                    videos.append({'id': f['id'], 'real_id': real_id, 'name': f['name']})
            elif f['mimeType'].startswith('video/'):
                videos.append({'id': f['id'], 'real_id': f['id'], 'name': f['name']})
        
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    
    unprocessed = [v for v in videos if v['id'] not in processed]
    return unprocessed, processed

def download_video(drive, video_id, name):
    clean_name = "".join(c for c in name if c.isalnum() or c in '._-').rstrip()
    if not clean_name.endswith('.mp4'):
        clean_name += '.mp4'
    
    local_path = f"/tmp/upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{clean_name}"
    
    request = drive.files().get_media(fileId=video_id)
    
    with open(local_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    
    return local_path

def upload_video():
    print(f"\n{'='*60}")
    print(f"YOUTUBE UPLOAD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    print("[1/5] Initializing APIs...")
    youtube_creds = get_youtube_creds()
    youtube = build('youtube', 'v3', credentials=youtube_creds, cache_discovery=False)
    
    drive_creds = get_drive_creds()
    drive = build('drive', 'v3', credentials=drive_creds)
    print("  ✓ APIs ready")
    
    print("\n[2/5] Checking Drive for new videos...")
    unprocessed, processed = get_unprocessed_videos(drive)
    
    if not unprocessed:
        print("  ✗ No new videos available!")
        return False
    
    print(f"  ✓ {len(unprocessed)} unprocessed videos available")
    
    video = random.choice(unprocessed)
    print(f"\n[3/5] Selected: {video['name']}")
    
    print("\n[4/5] Downloading from Drive...")
    local_path = download_video(drive, video['real_id'], video['name'])
    size_mb = os.path.getsize(local_path) / (1024*1024)
    print(f"  ✓ Downloaded: {size_mb:.1f} MB")
    
    print("\n[5/5] Uploading to YouTube...")
    title = random.choice(TITLES) + f" #{len(processed)+1}"
    
    body = {
        'snippet': {
            'title': title,
            'description': f"Watch till the end!\n\n#Shorts #Viral #Trending",
            'tags': ['viral', 'trending', 'shorts'],
            'categoryId': '22',
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
            print(f"  Upload progress: {int(status.progress() * 100)}%")
    
    video_id = response['id']
    
    processed.add(video['id'])
    with open(PROCESSED_LOG, 'w') as f:
        json.dump(list(processed), f)
    
    history = []
    if os.path.exists('upload_history.json'):
        with open('upload_history.json', 'r') as f:
            history = json.load(f)
    
    history.append({
        'timestamp': datetime.now().isoformat(),
        'title': title,
        'video_id': video_id
    })
    
    with open('upload_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    daily_count = {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0}
    if os.path.exists('daily_upload_count.json'):
        with open('daily_upload_count.json', 'r') as f:
            daily_count = json.load(f)
    
    if daily_count.get('date') != datetime.now().strftime('%Y-%m-%d'):
        daily_count = {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0}
    
    daily_count['count'] += 1
    
    with open('daily_upload_count.json', 'w') as f:
        json.dump(daily_count, f, indent=2)
    
    os.remove(local_path)
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS!")
    print(f"   Video: {title}")
    print(f"   URL: https://youtu.be/{video_id}")
    print(f"   Today's uploads: {daily_count['count']}")
    print(f"   Remaining: {len(unprocessed)-1} videos")
    print(f"{'='*60}\n")
    
    return True

if __name__ == '__main__':
    try:
        success = upload_video()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### Step 4.4: Initialize Git and Push

```bash
cd ~/automation2-setup

git init
git add .
git commit -m "Initial YouTube automation setup"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/youtube-automation-2.git
git push -u origin main
```

---

## Phase 5: Test (5 min)

### Step 5.1: Manual Test Run

1. Go to your GitHub repo → **Actions** tab
2. Click **YouTube Auto Upload** workflow
3. Click **Run workflow** → **Run workflow** button
4. Wait 2-5 minutes for the job to complete
5. Check the logs for success/failure
6. Verify video appears on your new YouTube channel

### Step 5.2: Verify

- ☑️ Video uploaded to correct channel
- ☑️ Title generated correctly
- ☑️ `token.pickle` committed back to repo (check repo files)
- ☑️ `processed_videos.json` created

---

## Phase 6: Monitor

### First Week Checklist

- [ ] Check Actions tab daily for first 3 days
- [ ] Verify 3 uploads/day happening on schedule
- [ ] Watch for any authentication errors
- [ ] Check token refresh is working (token.pickle updates)

### Schedule (IST)

| Upload | Time | Cron (UTC) |
|--------|------|------------|
| Morning | 10:30 AM | `0 5 * * *` |
| Afternoon | 2:00 PM | `30 8 * * *` |
| Evening | 9:30 PM | `0 16 * * *` |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Token expired" | Re-run `authenticate_youtube_2.py`, re-encode token, update secret |
| "Drive access denied" | Verify service account email has Viewer access to Drive folder |
| "No videos available" | Check Drive folder has videos, folder ID is correct |
| "Upload failed" | Check Actions log for specific error, verify YouTube API quota |

---

## Summary Checklist

- [ ] Google Cloud project created
- [ ] YouTube Data API enabled
- [ ] Drive API enabled
- [ ] OAuth credentials created (`client_secret_2.json`)
- [ ] Service account created (`service-account-key-2.json`)
- [ ] Drive folder shared with service account
- [ ] YouTube authentication completed (`token_2.pickle`)
- [ ] GitHub repo created
- [ ] 3 secrets added to GitHub
- [ ] Workflow file created
- [ ] Upload script created (with correct Drive folder ID)
- [ ] Files pushed to GitHub
- [ ] Manual test run successful
- [ ] First video uploaded to YouTube

---

**Estimated Total Time:** 60-70 minutes

**Ready to start? Let me know which phase you're on and I'll help if you get stuck.** 🚀
