#!/usr/bin/env python3
"""
Run this script ONCE locally to authenticate with YouTube AND Google Drive.
It will open a browser, ask you to log into your YouTube channel account,
and save token.pickle which you'll then upload to GitHub Secrets.

Usage:
    source /tmp/env/bin/activate
    python3 generate_token.py
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Both scopes — Drive read + YouTube upload (must match upload_scheduled.py)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.readonly",
]

CLIENT_SECRET = "client_secret.json"
TOKEN_FILE = "token.pickle"

def main():
    if not os.path.exists(CLIENT_SECRET):
        print(f"❌ '{CLIENT_SECRET}' not found!")
        print("Download it from Google Cloud Console:")
        print("  APIs & Services → Credentials → OAuth 2.0 Client IDs → Download JSON")
        print(f"  Rename it to '{CLIENT_SECRET}' and place it in this folder.")
        return

    print("🌐 Opening browser for Google authentication (YouTube + Drive)...")
    print("   ⚠️  Log in with the Google account that OWNS your YouTube channel!\n")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

    print(f"\n✅ token.pickle saved successfully!")
    print(f"   Scopes granted: YouTube upload + Drive read\n")

    # Verify YouTube
    try:
        youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
        response = youtube.channels().list(part="snippet", mine=True).execute()
        if response.get("items"):
            channel_name = response["items"][0]["snippet"]["title"]
            print(f"✅ YouTube channel: '{channel_name}'")
        else:
            print("⚠️  No YouTube channel found for this account.")
    except Exception as e:
        print(f"⚠️  YouTube check failed: {e}")

    # Verify Drive
    try:
        drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        result = drive.files().list(
            q=f"'1kocgFg0rzsMCtXsrWiOH_oditWshBpbV' in parents and trashed = false",
            pageSize=5,
            fields="files(name)"
        ).execute()
        files = result.get("files", [])
        print(f"✅ Drive folder accessible — {len(files)} file(s) visible")
        if files:
            for f in files[:3]:
                print(f"   → {f['name']}")
    except Exception as e:
        print(f"⚠️  Drive check failed: {e}")
        print("   Make sure you shared the Drive folder with your Google account!")

    print("\n📋 Next steps:")
    print("   1. Run this to encode token.pickle:")
    print("      python3 -c \"import base64; open('/tmp/google_token_b64.txt','w').write(base64.b64encode(open('token.pickle','rb').read()).decode())\"")
    print("   2. Open /tmp/google_token_b64.txt, select all, copy")
    print("   3. Paste as GitHub Secret: GOOGLE_TOKEN")
    print("      github.com/KarthikeyaPodicheti/youtube-automation/settings/secrets/actions")

if __name__ == "__main__":
    main()
