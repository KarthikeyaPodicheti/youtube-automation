# YouTube Automation Process

Follow this step-by-step guide to set up and execute the YouTube Automation Script.

---

### **1. OAuth2 Authentication (Manual Setup)**

Before running the script, ensure that you authenticate manually using Google's OAuth2 flow:

1. Open a terminal in your environment.
2. Run the following command to clear old tokens and start from scratch:

   ```bash
   source /tmp/env/bin/activate && rm -f /tmp/youtube-automation/token.pickle && python3 /tmp/youtube-automation/upload_scheduled.py
   ```

3. When the script runs, it will generate an **authorization URL**. Example output:

   ```text
   === Manual OAuth Flow ===
   1. Open this URL in your browser: https://accounts.google.com/o/oauth2/auth?...
   2. Log in and approve.
   3. Copy the full URL from the browser after redirection to localhost.
   Paste the full redirected URL here:
   ```

4. Open the URL in your browser and log in with the preferred Google account (correct YouTube channel).
5. Copy the full redirected URL (e.g., starting with `http://localhost/?state=...`) from your browser's address bar.
6. Paste the URL into the terminal when the script prompts.

Once authentication is complete, a `token.pickle` file will be saved, and future runs will reuse this token.

---

### **2. Setting Up APIs in Google Cloud Console**

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create an OAuth 2.0 Client ID for a **Desktop App**.
3. Download the `client_secret.json` file and place it at:
   ```
   /tmp/youtube-automation/client_secret.json
   ```
4. Ensure the following APIs are enabled for your project:
   - **YouTube Data API v3**
   - **Google Drive API**

---

### **3. Running the Script**

1. With authentication complete, videos will automatically upload. Simply run:

   ```bash
   source /tmp/env/bin/activate && python3 /tmp/youtube-automation/upload_scheduled.py
   ```

2. The script performs the following:
   - Fetches unprocessed videos from Google Drive.
   - Randomly selects a video.
   - Uploads the video to YouTube with metadata.

---

### **4. Handling OAuth Errors**

If you encounter issues with authentication (e.g., wrong account), simply regenerate the token:

1. Delete the existing token:
   ```bash
   rm -f /tmp/youtube-automation/token.pickle
   ```
2. Rerun the script to start the OAuth flow again.

---

### **5. Notes for Future Automation**

- The `token.pickle` ensures that you don’t need to authenticate manually every time.
- Only re-authenticate if the token expires or you need to switch YouTube accounts.
- To automate new uploads, regularly add videos to the designated Drive folder.

---

### **Output Example**

After a successful run, you should see output like this:

```text
[2/5] Checking Drive for new videos...
✓ 10 unprocessed videos available
[3/5] Selected: example_video.mp4
[4/5] Downloading from Drive...
✓ Downloaded: 12.8 MB
[5/5] Uploading to YouTube...

✅ SUCCESS!
Video: Example Title
URL: https://youtu.be/example_video_id
Today's uploads: 1
Remaining: 9 videos
```

---

### End of Process
