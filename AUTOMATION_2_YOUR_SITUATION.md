# Automation #2 - YOUR Situation (Simplest Path)

**Your Current State:**
- ✅ You have CarCrash automation running
- ✅ You have Google Cloud project already set up
- ✅ You have OAuth credentials already created
- ✅ You have Service Account already created
- ✅ You have YouTube token already working
- ✅ You have the new Drive folder: `1kocgFg0rzsMCtXsrWiOH_oditWshBpbV`
- ❌ No new YouTube channel needed (will use existing one)
- ❌ No new email needed
- ❌ No new Google Cloud setup needed

**What You Need To Do:**
Just create a NEW GitHub repo with the same credentials but pointing to the new Drive folder.

**Time Required:** 20 minutes total

---

# STEP 1: Get Your Existing Credentials (5 minutes)

## Option A: From Your Computer/Codespace

If you still have the credential files from Automation #1:

1. Find these 3 files:
   - `client_secret.json`
   - `service-account-key.json`
   - `token.pickle`

2. They might be in:
   - Your Downloads folder
   - Your Codespace workspace
   - Wherever you saved them during CarCrash setup

## Option B: Download from GitHub (If files are lost)

Your CarCrash repo has the token.pickle committed. The other 2 you need to find locally.

If you can't find them, tell me and I'll help you recover.

---

# STEP 2: Encode The 3 Files (5 minutes)

Open terminal and navigate to where your credential files are:

```bash
cd /path/to/your/credentials
```

## Encode File 1:

```bash
base64 -w 0 client_secret.json
```

- Copy the ENTIRE output (long string)
- Save it somewhere (notepad, text file, etc.)
- Label it: "CLIENT_SECRET"

## Encode File 2:

```bash
base64 -w 0 service-account-key.json
```

- Copy the ENTIRE output
- Save it
- Label it: "SERVICE_ACCOUNT"

## Encode File 3:

```bash
base64 -w 0 token.pickle
```

- Copy the ENTIRE output
- Save it
- Label it: "YOUTUBE_TOKEN"

**You now have 3 base64 strings saved.**

---

# STEP 3: Create New GitHub Repository (3 minutes)

1. Go to: https://github.com/new

2. Fill in:
   - **Repository name:** `youtube-automation-2` (or any name you want)
   - **Description:** (optional, can leave empty)
   - **Public** or **Private:** Your choice
   - **Uncheck** "Add a README file"
   - **Uncheck** "Add .gitignore"
   - **Uncheck** "Choose a license"

3. Click **"Create repository"**

---

# STEP 4: Add The 3 Secrets (5 minutes)

1. In your new repo, click **"Settings"** tab (top menu)

2. In left sidebar, click **"Secrets and variables"** → **"Actions"**

3. Click **"New repository secret"** button

## Add Secret 1:

- **Name:** `GOOGLE_CLIENT_SECRET`
- **Value:** Paste the CLIENT_SECRET base64 string
- Click **"Add secret"**

## Add Secret 2:

- Click **"New repository secret"** again
- **Name:** `GOOGLE_SERVICE_ACCOUNT`
- **Value:** Paste the SERVICE_ACCOUNT base64 string
- Click **"Add secret"**

## Add Secret 3:

- Click **"New repository secret"** again
- **Name:** `YOUTUBE_TOKEN`
- **Value:** Paste the YOUTUBE_TOKEN base64 string
- Click **"Add secret"**

**Done! All 3 secrets added.**

---

# STEP 5: Create Workflow File (5 minutes)

## 5.1: Create the folder structure

1. In your GitHub repo (main page), click **"Add file"** → **"Create new file"**

2. In the filename box, type EXACTLY this:
   ```
   .github/workflows/youtube-uploads.yml
   ```
   
   (GitHub will automatically create the .github/workflows folders)

3. Paste this ENTIRE content:

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

4. Scroll down and click **"Commit changes"**

---

# STEP 6: Create Upload Script (5 minutes)

1. In your GitHub repo, click **"Add file"** → **"Create new file"**

2. Filename: `upload_scheduled.py`

3. Paste this ENTIRE content (Drive folder ID is already set to YOUR folder):

```python
#!/usr/bin/env python3
import os, json, pickle, random, sys
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# THIS IS YOUR DRIVE FOLDER - Already configured!
DRIVE_FOLDER_ID = '1kocgFg0rzsMCtXsrWiOH_oditWshBpbV'
PROCESSED_LOG = 'processed_videos.json'
TOKEN_FILE = 'token.pickle'
SERVICE_ACCOUNT = 'service-account-key.json'

# Customize these titles for your content
TITLES = [
    "You Won't Believe THIS! 😱",
    "This Changes Everything!",
    "The Truth Nobody Tells You",
    "What Happens Next Is INSANE",
    "They Didn't Want You To See This",
    "This Is Why You're Failing",
    "The Secret They're Hiding",
    "I Can't Believe This Worked",
    "This Will Blow Your Mind",
    "Watch Until The End!",
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
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token
        ).execute()
        
        for f in response.get('files', []):
            if f['mimeType'].startswith('video/'):
                videos.append({'id': f['id'], 'name': f['name']})
        
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    
    unprocessed = [v for v in videos if v['id'] not in processed]
    return unprocessed, processed

def download_video(drive, video_id, name):
    clean_name = "".join(c for c in name if c.isalnum() or c in '._-').rstrip()
    if not clean_name.endswith('.mp4'):
        clean_name += '.mp4'
    
    path = f"/tmp/upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{clean_name}"
    
    request = drive.files().get_media(fileId=video_id)
    
    with open(path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    
    return path

def upload_video():
    print(f"\n{'='*60}")
    print(f"YOUTUBE UPLOAD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    print("[1/4] Initializing APIs...")
    youtube_creds = get_youtube_creds()
    youtube = build('youtube', 'v3', credentials=youtube_creds, cache_discovery=False)
    
    drive_creds = get_drive_creds()
    drive = build('drive', 'v3', credentials=drive_creds)
    print("  ✓ APIs ready")
    
    print("\n[2/4] Checking Drive for videos...")
    unprocessed, processed = get_unprocessed_videos(drive)
    
    if not unprocessed:
        print("  ✗ No videos found in Drive folder!")
        return False
    
    print(f"  ✓ {len(unprocessed)} videos available")
    
    video = random.choice(unprocessed)
    print(f"\n[3/4] Selected: {video['name']}")
    
    print("\n[4/4] Downloading and uploading...")
    path = download_video(drive, video['id'], video['name'])
    size_mb = os.path.getsize(path) / (1024*1024)
    print(f"  ✓ Downloaded: {size_mb:.1f} MB")
    
    title = random.choice(TITLES) + f" #{len(processed)+1}"
    
    body = {
        'snippet': {
            'title': title,
            'description': 'Watch till the end!\n\n#Viral #Trending #Shorts',
            'tags': ['viral', 'trending', 'shorts'],
            'categoryId': '22',
        },
        'status': {
            'privacyStatus': 'public',
            'madeForKids': False
        }
    }
    
    media = MediaFileUpload(path, mimetype='video/mp4', resumable=True)
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
    
    os.remove(path)
    
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

4. Scroll down and click **"Commit changes"**

---

# STEP 7: Create Tracking Files (2 minutes)

## File 1: processed_videos.json

1. Click **"Add file"** → **"Create new file"**
2. Filename: `processed_videos.json`
3. Content (type exactly):
   ```
   []
   ```
4. Click **"Commit changes"**

## File 2: upload_history.json

1. Click **"Add file"** → **"Create new file"**
2. Filename: `upload_history.json`
3. Content:
   ```
   []
   ```
4. Click **"Commit changes"**

## File 3: daily_upload_count.json

1. Click **"Add file"** → **"Create new file"**
2. Filename: `daily_upload_count.json`
3. Content:
   ```
   {"date": "2026-02-28", "count": 0}
   ```
4. Click **"Commit changes"**

---

# STEP 8: Share Drive Folder With Service Account (CRITICAL!) (3 minutes)

**This step is MOST IMPORTANT. Don't skip!**

Your service account needs permission to read the Drive folder.

## Find Your Service Account Email:

**Option A - If you know it from CarCrash setup:**
- It looks like: `something@your-project.iam.gserviceaccount.com`

**Option B - Check your CarCrash repo:**
- If you have `service-account-key.json` locally, open it
- Look for `"client_email"` field
- Copy that email

## Share The Drive Folder:

1. Open: https://drive.google.com/drive/folders/1kocgFg0rzsMCtXsrWiOH_oditWshBpbV

2. Click **"Share"** button (top right)

3. In the text box, paste your service account email

4. Select **"Viewer"** permission (read-only is enough)

5. Click **"Done"**

**DONE! This is the most common failure point. Make sure you did this.**

---

# STEP 9: Test The Automation (5 minutes)

## Run Manual Test:

1. Go to your new GitHub repo

2. Click **"Actions"** tab (top menu)

3. You'll see "YouTube Auto Upload" workflow

4. Click on it

5. Click **"Run workflow"** button (right side)

6. Click **"Run workflow"** again in the popup

## Wait For It To Complete:

1. Wait 2-5 minutes (depends on video size)

2. Refresh the page occasionally

3. When you see a **green checkmark** ✓ = Success

4. If you see **red X** = Failed (click on it to see error)

## Verify Upload:

1. Go to your YouTube channel

2. Check if a new video was uploaded

3. The title will be random from the TITLES list + number

---

# STEP 10: You're Done! (0 minutes)

**Your automation is now LIVE!**

## Schedule (IST):

| Time | What Happens |
|------|--------------|
| 10:30 AM | Uploads 1 video |
| 2:00 PM | Uploads 1 video |
| 9:30 PM | Uploads 1 video |

**Total: 3 videos per day automatically**

## What Happens Now:

- GitHub Actions runs automatically at scheduled times
- Picks a random video from your Drive folder
- Uploads to YOUR YouTube channel
- Remembers what's already uploaded (no duplicates)
- Commits updated tracking files back to repo

---

# Troubleshooting

## Problem: "No videos found in Drive folder!"

**Fix:**
1. Check Drive folder actually has videos
2. Check videos are not in subfolders (must be directly in the folder)
3. Check Drive folder ID is correct in upload_scheduled.py

## Problem: "Access denied" or "Permission denied"

**Fix:**
1. You didn't share Drive folder with service account
2. Go back to STEP 8 and do it properly
3. Make sure you shared with the CORRECT service account email

## Problem: "Token expired"

**Fix:**
1. Your YouTube token needs refresh
2. Go to your CarCrash automation files
3. Copy the fresh `token.pickle` from there
4. Re-encode it: `base64 -w 0 token.pickle`
5. Update the YOUTUBE_TOKEN secret in GitHub

## Problem: Workflow shows red X (failed)

**Fix:**
1. Click on the failed workflow
2. Click on the job
3. Read the error message
4. Tell me the error and I'll help fix it

---

# Summary Checklist

Before you start, make sure you have:

- [ ] Your 3 credential files from CarCrash setup
- [ ] Access to the Drive folder: `1kocgFg0rzsMCtXsrWiOH_oditWshBpbV`
- [ ] GitHub account

After completion:

- [ ] New GitHub repo created
- [ ] 3 secrets added to repo
- [ ] Workflow file created (.github/workflows/youtube-uploads.yml)
- [ ] Upload script created (upload_scheduled.py)
- [ ] 3 tracking files created
- [ ] Drive folder shared with service account
- [ ] Manual test run successful
- [ ] Video uploaded to YouTube

---

**Total Time: 25-30 minutes**

**Start with STEP 1 now. Tell me when you complete each step.** 🚀
