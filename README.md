# Email Parser

Local web app that reads a folder of `.eml`/`.msg` emails, extracts four columns
(Name, Phone, Subject, Urgency) using the Groq API, and lets you download the
result as an Excel file.

## Setup

1. Get a free Groq API key at https://console.groq.com (no credit card required).
2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and paste in your key (a `.env` with a key is already
   set up in this project if you provided one during setup).
4. Start the server:
   ```
   python app.py
   ```
5. Open http://127.0.0.1:5000 in your browser.

## Usage

1. Enter the absolute path to the folder containing your `.eml`/`.msg` files, or click
   **Browse...** to pick it with a native folder dialog.
2. Click **Run**. A progress bar shows how many of the emails found have been
   processed; the results table fills in as each one finishes.
3. Once processing completes, click **Download Excel** to save the generated
   `parsed_emails.xlsx` (header row `Name | Phone | Subject | Urgency`, one row per
   successfully parsed email).

Each run parses every `.eml`/`.msg` file currently in the folder and produces a fresh,
complete file — there's no dedup/append step, so re-running always gives you an
up-to-date report of everything in the folder.

## Known limitations

- Emails that fail extraction (e.g. transient API errors) are reported as `error` in
  the results table and excluded from the downloaded file rather than blocking the rest
  of the batch.
- Only one parsing run can be in progress at a time.
- The generated file is held in server memory until the next run starts, so download it
  before starting a new run if you want to keep it.
