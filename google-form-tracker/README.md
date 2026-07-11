# Eye Pressure Tracker (Google Forms version)

No hosting, no API keys, no passwords to manage. Everything runs inside a
Google account you already have, using Google Forms, Sheets, and Apps
Script (all free).

Columns tracked: **Date, Time, Pressure Left, Pressure Right** (plus an
optional photo attached to each submission as a backup record).

## How it works

1. Your mom opens a bookmarked Google Form link on her phone.
2. She fills in Date, Time, Left pressure, Right pressure, and attaches a
   photo of the device reading (for the record).
3. Submitting the form adds a row to a Google Sheet automatically.
4. A script (running under your mom's own Google account) fires on every
   submission, rebuilds a clean 4-column spreadsheet, and emails it as an
   `.xlsx` attachment.

Total setup time: about 10 minutes, done once.

## Setup

### 1. Create the form

1. Go to https://forms.google.com and create a new form, e.g. titled
   "Dad's Eye Pressure".
2. Add these questions, in this order, with these **exact titles**:
   - **Date** — question type "Date"
   - **Time** — question type "Time"
   - **Pressure Left** — question type "Short answer", with response
     validation set to "Number"
   - **Pressure Right** — question type "Short answer", with response
     validation set to "Number"
   - **Photo** — question type "File upload" (allow image files, max 1
     file). Google will note this requires respondents to sign in with a
     Google account — that's fine since it'll just be your mom's account.

### 2. Link it to a spreadsheet

1. In the form editor, go to the **Responses** tab.
2. Click the green Sheets icon ("Create Spreadsheet") and create a new
   spreadsheet. This is where every submission will land as a row.

### 3. Add the script

1. Open the spreadsheet you just created.
2. Go to **Extensions → Apps Script**.
3. Delete any placeholder code in `Code.gs` and paste in the contents of
   this folder's `Code.gs` file.
4. Check that `RECIPIENT_EMAIL` is the address that should receive the
   spreadsheet (currently set to `sunmaggie.wl@gmail.com`).
5. Check that `RESPONSES_SHEET_NAME` matches the actual tab name at the
   bottom of your spreadsheet (Google usually names it `Form Responses 1`
   — if yours differs, update the constant).
6. Save the script (the floppy disk icon or Ctrl/Cmd+S).

### 4. Authorize and test

1. In the Apps Script toolbar, select the function `testSendNow` from the
   dropdown next to the Run button, and click **Run**.
2. Google will ask you to authorize the script — click through **Review
   permissions → (choose your account) → Advanced → Go to (project name,
   unsafe) → Allow**. This warning appears because it's your own
   unpublished script; it's expected and safe.
3. Check that the recipient email received a test spreadsheet.

### 5. Set the trigger so it runs automatically

1. In the Apps Script editor, click the clock icon ("Triggers") in the
   left sidebar.
2. Click **+ Add Trigger**.
3. Set: function = `onFormSubmit`, event source = "From spreadsheet",
   event type = "On form submit". Save.

### 6. Give your mom the link

1. Back in the Form editor, click **Send**, choose the link icon, and
   optionally check "Shorten URL".
2. Send that link to her, and have her add it to her phone's home screen
   (in her browser's share/menu, look for "Add to Home Screen") so it
   opens like an app with one tap.

## Notes

- Every submission is still saved in the Google Sheet itself, viewable
  anytime — the emailed Excel file is just a convenient copy.
- If a submission is missing a value, the emailed spreadsheet will just
  have a blank cell for that column; nothing blocks the email from
  sending.
- To change who receives the email later, edit `RECIPIENT_EMAIL` in the
  script and save.
