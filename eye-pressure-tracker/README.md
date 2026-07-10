# Eye Pressure Tracker

A tiny mobile-friendly web app: take a photo of the tonometer display, an AI
reads the numbers, you confirm/fix them, and it saves the reading and emails
an updated Excel spreadsheet.

Columns tracked: **Date, Time, Pressure Left, Pressure Right**.

## How it works

1. Open the site on a phone, tap "Take a Photo," snap a photo of the device.
2. Claude (Anthropic's AI) reads the date/time/left/right pressure off the photo.
3. A confirmation screen shows the extracted values so any misread digit can
   be fixed by hand before saving.
4. On save, the reading is added to a small database and the full history is
   emailed as an `.xlsx` attachment to the recipient address. You can also
   download the spreadsheet directly at any time from `/history`.

## One-time setup

You need three things before deploying:

### 1. Anthropic API key (reads the photo)
- Go to https://console.anthropic.com/ , sign up, and create an API key.
- Add a small amount of credit (each photo read costs a fraction of a cent).

### 2. Gmail App Password (sends the email)
- Use a Gmail account you're comfortable having the app send from.
- Go to https://myaccount.google.com/apppasswords (requires 2-Step
  Verification to be turned on for that Google account).
- Create an app password named e.g. "Eye Pressure Tracker" — it gives you a
  16-character code. That code is `GMAIL_APP_PASSWORD`, not the account's
  normal login password.

### 3. Recipient email
Defaults to `sunmaggie.wl@gmail.com`. Change via the `RECIPIENT_EMAIL`
environment variable if needed.

## Deploying to Render.com

1. Push this repo to GitHub (already done if you're reading this from the
   repo).
2. Go to https://dashboard.render.com/ → **New** → **Blueprint**, and point
   it at this repository. Render will read `render.yaml` and set up:
   - A web service on the **Starter** plan (needed for the persistent disk
     that stores readings — without it, readings would be lost whenever the
     service restarts).
   - A 1 GB persistent disk mounted at `/var/data` for the SQLite database.
3. When prompted, fill in the environment variables Render marks as
   secret:
   - `ANTHROPIC_API_KEY`
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`
4. Deploy. Render will give you a URL like
   `https://eye-pressure-tracker.onrender.com` — bookmark that on your mom's
   phone (Add to Home Screen) so it opens like an app.

## Running locally (optional, for testing)

```bash
cd eye-pressure-tracker
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your API key / Gmail app password
python app.py
```

Visit http://localhost:5000

## Notes

- If the AI can't read a value (blurry photo, glare, etc.) it leaves that
  field blank and the confirmation screen lets you type it in — nothing is
  ever saved without a chance to review it first.
- If sending the email fails for any reason (e.g. bad credentials), the
  reading is still saved, and a "Download Spreadsheet" button is shown as a
  fallback.
- All past readings are always viewable at `/history` and downloadable at
  `/download`.
