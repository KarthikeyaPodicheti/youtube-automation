# Automation #2 - Simple Step-by-Step Guide

**New Drive:** https://drive.google.com/drive/folders/1kocgFg0rzsMCtXsrWiOH_oditWshBpbV

Follow each step exactly. Don't skip anything.

---

# PHASE 1: Google Cloud Setup (30 minutes)

## Step 1: Open Google Cloud Console

1. Open browser
2. Go to: https://console.cloud.google.com
3. Sign in with your Google account

## Step 2: Create a New Project

1. Click the project dropdown at the top (shows "Select a project")
2. Click **"NEW PROJECT"**
3. Type project name: `YouTube Automation 2`
4. Click **"CREATE"**
5. Wait 10 seconds for project to be created
6. Click **"SELECT PROJECT"**

## Step 3: Enable YouTube API

1. Click the search bar at top
2. Type: `YouTube Data API`
3. Click **"YouTube Data API v3"** from results
4. Click **"ENABLE"** button
5. Wait for it to finish (shows "API enabled")

## Step 4: Enable Drive API

1. Click the search bar at top again
2. Type: `Google Drive API`
3. Click **"Google Drive API"** from results
4. Click **"ENABLE"** button
5. Wait for it to finish

## Step 5: Create OAuth Credentials

1. In left sidebar, click **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at top
3. Select **"OAuth client ID"**

### If you see "OAuth consent screen" setup:

4a. Select **"External"** for User Type
4b. Click **"CREATE"**

**Fill the form:**
- App name: `YouTube Uploader 2`
- User support email: Your email address
- Developer contact email: Your email address
- Click **"SAVE AND CONTINUE"**
- Scroll down → Click **"SAVE AND CONTINUE"** (skip scopes)
- Click **"ADD USERS"** → Add your email → Click **"SAVE AND CONTINUE"**
- Click **"BACK TO DASHBOARD"**

### Now create OAuth credentials:

5. Application type: Select **"Desktop app"**
6. Name: `youtube-uploader-2`
7. Click **"CREATE"**

## Step 6: Download OAuth File

1. A popup appears with your Client ID
2. Click **"DOWNLOAD JSON"**
3. Save the file as: `client_secret.json`
4. Remember where you saved it (Downloads folder usually)

## Step 7: Create Service Account

1. Go back to **Credentials** page
2. Click **"+ CREATE CREDENTIALS"** → **"Service Account"**
3. Service account name: `drive-access`
4. Click **"CREATE AND CONTINUE"**
5. Skip the role selection → Click **"CONTINUE"**
6. Click **"DONE"**

## Step 8: Download Service Account Key

1. Click on the service account you just created (shows email like `drive-access@...iam.gserviceaccount.com`)
2. Click **"KEYS"** tab
3. Click **"ADD KEY"** → **"Create new key"**
4. Select **"JSON"** format
5. Click **"CREATE"**
6. File downloads automatically
7. Rename it to: `service-account-key.json`

## Step 9: Copy Service Account Email

1. Stay on the service account page
2. Copy the email address (looks like: `drive-access@your-project-123.iam.gserviceaccount.com`)
3. Paste it in a notepad - you need it in Step 10

## Step 10: Share Drive Folder

1. Open new tab: https://drive.google.com/drive/folders/1kocgFg0rzsMCtXsrWiOH_oditWshBpbV
2. Click **"Share"** button (top right)
3. Paste the service account email
4. Select **"Viewer"** permission
5. Click **"Done"**

---

# PHASE 2: Authenticate YouTube (10 minutes)

## Step 1: Open Terminal

**Option A - Using Codespace:**
1. Go to your GitHub Codespace
2. Open terminal

**Option B - Using your computer:**
1. Open Terminal (Mac/Linux) or Command Prompt (Windows)

## Step 2: Create Setup Folder

Run these commands:

```bash
mkdir automation2
cd automation2
```

## Step 3: Move Credential Files

Move both files to this folder:
- `client_secret.json`
- `service-account-key.json`

**On Mac/Linux:**
```bash
mv ~/Downloads/client_secret.json .
mv ~/Downloads/service-account-key.json .
```

**On Windows:**
Copy-paste the files from Downloads to your automation2 folder

## Step 4: Install Python Packages

Run this command:

```bash
pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Wait for installation to complete.

## Step 5: Create Auth Script

Create a file called `auth.py` with this content:

```python
#!/usr/bin/env python3
import os
import pickle
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)

if not creds or not creds.valid:
    flow = Flow.from_client_secrets_file('client_secret.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
    print('\nOPEN THIS URL:\n')
    print(auth_url)
    print('\n')
    code = input('Paste code here: ')
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open('token.pickle', 'wb') as f:
        pickle.dump(creds, f)
    print('Token saved!')

youtube = build('youtube', 'v3', credentials=creds)
channel = youtube.channels().list(part='snippet', mine=True).execute()
print('\nConnected to:', channel['items'][0]['snippet']['title'])
```

## Step 6: Run Authentication

```bash
python3 auth.py
```

## Step 7: Authorize YouTube

1. A URL appears in terminal
2. Copy the entire URL
3. Paste in browser
4. **Sign in with your NEW YouTube channel account** (NOT the CarCrash one!)
5. Click **"Allow"** for permissions
6. Copy the authorization code shown
7. Paste it in terminal
8. Press Enter

## Step 8: Verify

You should see: `Connected to: [Your Channel Name]`

**Success!** You now have `token.pickle` file.

---

# PHASE 3: GitHub Setup (15 minutes)

## Step 1: Create New Repository

1. Go to: https://github.com/new
2. Repository name: `youtube-automation-2`
3. **Uncheck** "Add a README file"
4. Click **"Create repository"**

## Step 2: Encode Files (Base64)

In your terminal (in automation2 folder):

```bash
# Encode client_secret.json
base64 -w 0 client_secret.json
```

1. Copy the entire output (long string of characters)
2. Paste in notepad - label it "CLIENT_SECRET"

```bash
# Encode service-account-key.json
base64 -w 0 service-account-key.json
```

1. Copy the output
2. Paste in notepad - label it "SERVICE_ACCOUNT"

```bash
# Encode token.pickle
base64 -w 0 token.pickle
```

1. Copy the output
2. Paste in notepad - label it "YOUTUBE_TOKEN"

## Step 3: Add GitHub Secrets

1. Go to your new GitHub repo
2. Click **"Settings"** tab
3. Click **"Secrets and variables"** → **"Actions"**
4. Click **"New repository secret"**

### Add Secret 1:
- **Name:** `GOOGLE_CLIENT_SECRET`
- **Value:** Paste the CLIENT_SECRET base64 string
- Click **"Add secret"**

### Add Secret 2:
- Click **"New repository secret"**
- **Name:** `GOOGLE_SERVICE_ACCOUNT`
- **Value:** Paste the SERVICE_ACCOUNT base64 string
- Click **"Add secret"**

### Add Secret 3:
- Click **"New repository secret"**
- **Name:** `YOUTUBE_TOKEN`
- **Value:** Paste the YOUTUBE_TOKEN base64 string
- Click **"Add secret"**

---

# PHASE 4: Upload Files to GitHub (10 minutes)

## Step 1: Create Workflow File

1. In your GitHub repo, click **"Add file"** → **"Create new file"**
2. Filename: `.github/workflows/youtube-uploads.yml`
3. Paste this content:

```yaml
name: YouTube Auto Upload

permissions:
  contents: write

on:
  schedule:
    - cron: '0 5 * * *'
    - cron: '30 8 * * *'
    - cron: '0 16 * * *'
  workflow_dispatch:

jobs:
  upload-video:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client httplib2
    - name: Create credentials
      run: |
        python3 << 'EOF'
        import base64, os
        with open('client_secret.json', 'wb') as f:
            f.write(base64.b64decode(os.environ['GOOGLE_CLIENT_SECRET']))
        with open('service-account-key.json', 'wb') as f:
            f.write(base64.b64decode(os.environ['GOOGLE_SERVICE_ACCOUNT']))
        EOF
      env:
        GOOGLE_CLIENT_SECRET: ${{ secrets.GOOGLE_CLIENT_SECRET }}
        GOOGLE_SERVICE_ACCOUNT: ${{ secrets.GOOGLE_SERVICE_ACCOUNT }}
    - run: python upload_scheduled.py
    - name: Commit token
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add processed_videos.json upload_history.json daily_upload_count.json token.pickle || true
        git diff --cached --quiet || git commit -m "Update token [skip ci]"
        git push || true
```

4. Click **"Commit changes"**

## Step 2: Create Upload Script

1. Click **"Add file"** → **"Create new file"**
2. Filename: `upload_scheduled.py`
3. Paste this content:

```python
#!/usr/bin/env python3
import os, json, pickle, random, sys
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

DRIVE_FOLDER_ID = '1kocgFg0rzsMCtXsrWiOH_oditWshBpbV'
PROCESSED_LOG = 'processed_videos.json'
TOKEN_FILE = 'token.pickle'
SERVICE_ACCOUNT = 'service-account-key.json'

TITLES = [
    "You Won't Believe THIS! 😱",
    "This Changes Everything!",
    "The Truth Nobody Tells You",
    "What Happens Next Is INSANE",
    "They Didn't Want You To See This",
]

def get_youtube_creds():
    with open(TOKEN_FILE, 'rb') as f:
        return pickle.load(f)

def get_drive_creds():
    return service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT, scopes=['https://www.googleapis.com/auth/drive.readonly'])

def get_unprocessed_videos(drive):
    processed = set()
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r') as f:
            processed = set(json.load(f))
    videos = []
    page_token = None
    while True:
        response = drive.files().list(q=f"'{DRIVE_FOLDER_ID}' in parents and trashed = false", fields='nextPageToken, files(id, name, mimeType)', pageToken=page_token).execute()
        for f in response.get('files', []):
            if f['mimeType'].startswith('video/'):
                videos.append({'id': f['id'], 'name': f['name']})
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return [v for v in videos if v['id'] not in processed], processed

def download_video(drive, video_id, name):
    path = f"/tmp/upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    request = drive.files().get_media(fileId=video_id)
    with open(path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return path

def upload_video():
    print("Starting upload...")
    youtube_creds = get_youtube_creds()
    youtube = build('youtube', 'v3', credentials=youtube_creds)
    drive_creds = get_drive_creds()
    drive = build('drive', 'v3', credentials=drive_creds)
    
    unprocessed, processed = get_unprocessed_videos(drive)
    if not unprocessed:
        print("No videos!")
        return False
    
    video = random.choice(unprocessed)
    print(f"Selected: {video['name']}")
    
    path = download_video(drive, video['id'], video['name'])
    title = random.choice(TITLES) + f" #{len(processed)+1}"
    
    body = {
        'snippet': {'title': title, 'description': 'Watch till the end!', 'tags': ['viral'], 'categoryId': '22'},
        'status': {'privacyStatus': 'public', 'madeForKids': False}
    }
    
    media = MediaFileUpload(path, mimetype='video/mp4', resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
    
    processed.add(video['id'])
    with open(PROCESSED_LOG, 'w') as f:
        json.dump(list(processed), f)
    
    os.remove(path)
    print(f"SUCCESS! https://youtu.be/{response['id']}")
    return True

if __name__ == '__main__':
    try:
        upload_video()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
```

4. Click **"Commit changes"**

## Step 3: Initialize Tracking Files

1. Click **"Add file"** → **"Create new file"**
2. Filename: `processed_videos.json`
3. Content: `[]`
4. Click **"Commit changes"**

1. Click **"Add file"** → **"Create new file"**
2. Filename: `upload_history.json`
3. Content: `[]`
4. Click **"Commit changes"**

1. Click **"Add file"** → **"Create new file"**
2. Filename: `daily_upload_count.json`
3. Content: `{"date": "2026-02-28", "count": 0}`
4. Click **"Commit changes"**

---

# PHASE 5: Test (5 minutes)

## Step 1: Run Manual Test

1. Go to your GitHub repo
2. Click **"Actions"** tab
3. Click **"YouTube Auto Upload"** workflow
4. Click **"Run workflow"** dropdown
5. Click **"Run workflow"** button

## Step 2: Wait

1. Wait 2-5 minutes
2. Watch the job run (green check = success, red X = failed)

## Step 3: Verify

1. Click on the job
2. Check logs for "SUCCESS!" message
3. Go to your YouTube channel
4. Verify video is uploaded

---

# PHASE 6: Done!

## Your Schedule

| Time (IST) | Upload |
|------------|--------|
| 10:30 AM | Morning |
| 2:00 PM | Afternoon |
| 9:30 PM | Evening |

## What Happens Now

- GitHub Actions runs automatically 3x/day
- Picks random video from Drive
- Uploads to YouTube
- Tracks what's already uploaded
- No duplicates

## If Something Breaks

| Problem | Fix |
|---------|-----|
| "No videos" | Check Drive folder has videos |
| "Token expired" | Re-run Phase 2, update YOUTUBE_TOKEN secret |
| "Access denied" | Re-check Phase 1 Step 10 (share Drive with service account) |

---

**DONE! Your automation is live.** 🚀
