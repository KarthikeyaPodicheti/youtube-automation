#!/usr/bin/env python3
"""
Run this script ONCE locally to authenticate with YouTube.
It will open a browser, ask you to log into your YouTube channel account,
and save token.pickle which you'll then upload to GitHub Secrets.

Usage:
    pip install google-auth google-auth-oauthlib google-api-python-client
    python3 generate_token.py
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET = "client_secret.json"
TOKEN_FILE = "token.pickle"

def main():
    if not os.path.exists(CLIENT_SECRET):
        print(f"❌ '{CLIENT_SECRET}' not found!")
        print("Download it from Google Cloud Console:")
        print("  APIs & Services → Credentials → OAuth 2.0 Client IDs → Download JSON")
        print(f"  Rename it to '{CLIENT_SECRET}' and place it in this folder.")
        return

    print("🌐 Opening browser for YouTube authentication...")
    print("   ⚠️  Make sure to log in with the correct YouTube channel account!\n")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

    print(f"\n✅ token.pickle saved successfully!")

    # Verify it works
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    response = youtube.channels().list(part="snippet", mine=True).execute()
    if response.get("items"):
        channel_name = response["items"][0]["snippet"]["title"]
        print(f"✅ Authenticated as channel: '{channel_name}'")
    else:
        print("⚠️  Authenticated but no YouTube channel found for this account.")

    print("\n📋 Next steps:")
    print("   1. Run this command to get the base64 encoded token:")
    print("      base64 -i token.pickle | pbcopy    (Mac - copies to clipboard)")
    print("   2. Go to your GitHub repo → Settings → Secrets → Actions")
    print("   3. Add a secret named GOOGLE_TOKEN and paste the base64 value")

if __name__ == "__main__":
    main()
