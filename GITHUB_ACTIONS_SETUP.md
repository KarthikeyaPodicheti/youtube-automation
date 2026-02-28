# GitHub Actions Setup Guide

## Overview
Switch from Codespace-based uploads to GitHub Actions for free, reliable automation.

## What You Get
- **Free**: 2,000 minutes/month (600+ uploads worth)
- **Reliable**: Runs even when Codespace sleeps
- **No maintenance**: GitHub manages the servers

---

## Step 1: Prepare Your Credentials

### Convert files to base64 (run in your Codespace terminal):

```bash
cd /home/codespace/.openclaw/workspace

# 1. Client Secret (OAuth)
base64 -w 0 client_secret.json
# Copy the output, save it

# 2. Service Account (Drive API)
base64 -w 0 service-account-key.json
# Copy the output, save it

# 3. YouTube Token
base64 -w 0 token.pickle
# Copy the output, save it
```

---

## Step 2: Push Code to GitHub

```bash
cd /home/codespace/.openclaw/workspace
git init  # if not already
git add .
git commit -m "Setup YouTube automation"
git push origin main
```

---

## Step 3: Add GitHub Secrets

1. Go to your GitHub repo
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these 3 secrets:

| Secret Name | Value (base64 from Step 1) |
|-------------|---------------------------|
| `GOOGLE_CLIENT_SECRET` | (base64 of client_secret.json) |
| `GOOGLE_SERVICE_ACCOUNT` | (base64 of service-account-key.json) |
| `YOUTUBE_TOKEN` | (base64 of token.pickle) |

---

## Step 4: Delete Cron Jobs from Codespace

Since you're moving to GitHub Actions, remove the old cron jobs:

```bash
openclaw cron list
openclaw cron remove <job-id>
```

Or I can do this for you.

---

## Step 5: Test

1. Go to **Actions** tab in your GitHub repo
2. Click **YouTube Auto Upload** workflow
3. Click **Run workflow** (manual trigger)
4. Check if video uploads successfully

---

## Schedule

| Time (IST) | Cron (UTC) |
|------------|------------|
| 10:00 AM | `30 4 * * *` |
| 3:00 PM | `30 9 * * *` |

---

## Monitoring

- Check upload status in **Actions** tab
- View logs if uploads fail
- Your Dashboard (localhost) can still track progress when Codespace is running

---

## Cost
- **Free tier**: 2,000 minutes/month
- **Your usage**: ~450 minutes/month (2 uploads/day × 7.5 min × 30 days)
- **Remaining**: 1,550+ minutes for other projects

---

## Troubleshooting

**Upload fails?**
1. Check Actions log for errors
2. Verify secrets are correct
3. Regenerate token.pickle if expired (run auth script again)

**Token expires?**
- YouTube tokens expire after ~1 week without use
- Solution: Manually run auth script locally, re-encode token, update secret

---

## Next Steps

1. Run the base64 commands above
2. Copy the outputs
3. Go to your GitHub repo settings and add the 3 secrets
4. Tell me when done, and I'll remove the old cron jobs
