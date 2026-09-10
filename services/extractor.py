import os
import json
import time

from groq import Groq

MODEL = "openai/gpt-oss-120b"
VALID_URGENCY = {"High", "Medium", "Low"}

_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set")
        _client = Groq(api_key=key)
    return _client


PROMPT_TEMPLATE = """You are extracting structured information from a single email.

Sender display name: {sender_display_name}
Sender email address: {sender_email}
Subject line: {subject}

Email body:
---
{body_text}
---

Extract exactly these fields:
- name: full name of the person who wrote this email. Prefer a name in the
  signature/greeting of the body; fall back to the sender display name.
  Empty string if none found.
- phone: a phone number found in the body/signature, written as it appears.
  Empty string if none found.
- subject: cleaned subject line (strip "RE:"/"FW:"/"FWD:" prefixes). If the
  subject metadata is empty, infer a short subject from the body's first line.
- urgency: exactly one of "High", "Medium", "Low", based on explicit urgency
  language, deadlines, and tone. Default to "Medium" if unclear.

Respond with ONLY a JSON object with exactly these four keys: name, phone, subject, urgency.
No other text, no markdown fences."""


class ExtractionError(Exception):
    pass


def _normalize(data: dict, fallback_subject: str) -> dict:
    urgency = data.get("urgency")
    if urgency not in VALID_URGENCY:
        urgency = "Medium"
    return {
        "name": str(data.get("name") or "").strip(),
        "phone": str(data.get("phone") or "").strip(),
        "subject": str(data.get("subject") or fallback_subject or "").strip(),
        "urgency": urgency,
    }


def extract_fields(email_data: dict) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        sender_display_name=email_data.get("sender_display_name") or "(unknown)",
        sender_email=email_data.get("sender_email") or "(unknown)",
        subject=email_data.get("subject") or "(none)",
        body_text=email_data.get("body_text") or "(empty body)",
    )
    client = _get_client()
    last_exc = None
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = resp.choices[0].message.content
            data = json.loads(content)
            return _normalize(data, email_data.get("subject", ""))
        except Exception as exc:
            last_exc = exc
            time.sleep(2 * (attempt + 1))
    raise ExtractionError(
        f"Groq extraction failed for {email_data.get('filename')}: {last_exc}"
    )
