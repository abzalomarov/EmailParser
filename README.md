# Email Parser

Web app that reads `.eml`/`.msg` email files you upload from your browser, extracts
four columns (Name, Phone, Subject, Urgency) using the Groq API, and lets you download
the result as an Excel file. Works both locally and deployed to a host like Vercel,
since all processing happens through your browser upload — the server never needs
access to your local filesystem.

## Setup (local)

1. Get a free Groq API key at https://console.groq.com (no credit card required).
2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and paste in your key.
4. Start the server:
   ```
   python app.py
   ```
5. Open http://127.0.0.1:5000 in your browser.

## Deploying to Vercel

1. Push this repo to GitHub (already done) and import it into Vercel.
2. In the Vercel project's Settings → Environment Variables, add `GROQ_API_KEY` with
   your key. This replaces the local `.env` file, which is not deployed.
3. Vercel picks up `vercel.json`, which routes all requests to `app.py` (a standard
   Flask/WSGI app) via the `@vercel/python` builder.
4. Each email is processed as its own short serverless request (one Groq call), which
   keeps every request well within serverless execution time limits.

## Usage

1. Click the file picker and select one or more `.eml`/`.msg` files.
2. Click **Run**. Each file is uploaded and parsed one at a time; the progress bar and
   results table update as each one finishes.
3. Once done, click **Download Excel** to save `parsed_emails.xlsx` (header row
   `Name | Phone | Subject | Urgency`, one row per successfully parsed email).

## Known limitations

- Emails that fail extraction (e.g. transient API errors) are reported as `error` in
  the results table and excluded from the downloaded file rather than blocking the rest
  of the batch.
- Files are processed sequentially, one request per email — for very large batches this
  is slower than parallel processing, but keeps each request small and serverless-friendly.
