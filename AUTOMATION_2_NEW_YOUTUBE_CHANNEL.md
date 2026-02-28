# Automation: New YouTube Channel

**Overview:**
You want to automate videos from the Drive folder `1kocgFg0rzsMCtXsrWiOH_oditWshBpbV`, but for an entirely new YouTube channel. This guide gives you a simple, detailed setup for GitHub Actions automation.

---

## PHASE 1: Prepare New YouTube Channel (15-20 min)

### Step 1: Create a New Google Account / YouTube Channel

1. Open browser.
2. Go to: [Google Sign Up](https://accounts.google.com/signup)
3. Fill out the form to create a new Google account.
   - First and Last Name: (your choice)
   - Username: (unique, like "mynewchannel2026")
   - Password: (secure, save securely)
4. Click "Next" and complete the process.

**Optional:** Verify your new account via phone.

5. Go to: [YouTube](https://www.youtube.com)
6. Log in with your new Google account.
7. Create Channel:
   - Click profile icon (top right) → **Create a channel**.
   - Follow prompts to set up the channel.

---

## PHASE 2: Google Cloud Setup (30 min)

This phase creates all the credentials (OAuth, Service Account) needed for automation.

### Step 2.1: Create New Google Cloud Project

1. Open: [Google Cloud Console](https://console.cloud.google.com/)
2. Click the **Select Project** dropdown (top menu).
3. Click **NEW PROJECT**.
4. Name the project: `YouTube Automation 2`.
5. Click **CREATE**.
6. Wait 10 seconds → Click **Select Project**.

### Step 2.2: Enable Required APIs

1. In the Cloud Console, go to **APIs & Services** → **Library**.
2. Enable these APIs:
   - **YouTube Data API v3** (search "YouTube Data", click "Enable")
   - **Google Drive API** (search "Drive API", click "Enable")

### Step 2.3: Create OAuth 2.0 Credentials for YouTube

1. Go to **APIs & Services → Credentials**.
2. Click **+ CREATE CREDENTIALS** → Select **OAuth client ID**.
3. If prompted, configure the **OAuth consent screen**:
   - User Type: **External**
   - App Name: `Uploader for New YouTube Channel`
   - Save and continue → Skip "Scopes" → Save and back to dashboard.
4. Application Type: **Desktop App**.
5. Name: `YouTubeUploader2`
6. Click **CREATE**.
7. Download the JSON file and rename it to `client_secret.json`.

### Step 2.4: Create Service Account for Drive Access

1. Back in **APIs & Services → Credentials**.
2. Click **+ CREATE CREDENTIALS** → **Service Account**.
3. Fill in:
   - Name: `DriveAccessUploader2`
4. Skip Role Assignment → Click **Done**.
5. Open the new service account.
6. Go to **Keys** → Add Key → Create New Key → Select JSON.
7. Download the key and rename to `service-account-key.json`.

### Step 2.5: Share Drive Folder

1. Open your Drive folder: `https://drive.google.com/drive/folders/1kocgFg0rzsMCtXsrWiOH_oditWshBpbV`
2. Click the **Share** button.
3. Paste the service account email → Select "Viewer."
4. Click **Done**.

---

## PHASE 3: Authenticate YouTube Channel (15 min)

### Step 3.1: Install Python Requirements

On your local PC (or Codespace), install required libraries:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Step 3.2: Run Authentication Script

1. Create a file `authenticate_youtube_2.py` and paste:

```python
#!/usr/bin/env python3
import os
import pickle
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS_FILE = 'client_secret.json'

if __name__ == "__main__":
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES, redirect_uri="urn:ietf:wg:oauth:2.0:oob")
        auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
        print(f"\nOpen this URL to authorize your channel:\n{auth_url}\n")
        code = input("Paste the authorization code here: ")
        flow.fetch_token(code=code)
        creds = flow.credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print("\nAuthentication successful. Token saved as token.pickle.")

    youtube = build('youtube', 'v3', credentials=creds)
    response = youtube.channels().list(part='snippet', mine=True).execute()
    print(f"\nConnected to YouTube channel: {response['items'][0]['snippet']['title']}")
```

2. Run the script:

```bash
python authenticate_youtube_2.py
```

3. Follow the terminal prompts:
   - Open the URL shown.
   - Sign in with your **new YouTube channel.**
   - Approve permissions → Copy the code → Paste it in terminal.
4. Verify it shows your new channel name.

---

## PHASE 4: GitHub Setup (20 min)

### Step 4.1: Create New GitHub Repo

1. Go to: [GitHub New Repo](https://github.com/new)
2. **Repository Name:** `youtube-automation-new`
3. **Description:** Optional.
4. **Public or Private:** Your choice.
5. **Create repository**.

### Step 4.2: Add Secrets to GitHub

1. Go to **Settings → Secrets and Variables → Actions**.
2. Add these secrets:
   - `GOOGLE_CLIENT_SECRET` → Base64 of `client_secret.json`
   - `GOOGLE_SERVICE_ACCOUNT` → Base64 of `service-account-key.json`
   - `YOUTUBE_TOKEN` → Base64 of `token.pickle`

### Step 4.3: Create Workflow

1. Add file `.github/workflows/youtube-uploads.yml`.
2. Paste previous workflow content but use your new folder and project ID.

---

## PHASE 5: Test and Monitor
1. Run a manual workflow.
2. Verify uploads daily.
3. Add tracking files (`processed.json`, history).

Let me know which phase you're on!