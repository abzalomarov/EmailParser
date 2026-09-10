import os
import email
from email import policy
from email.parser import BytesParser

from bs4 import BeautifulSoup
import extract_msg

BODY_CHAR_LIMIT = 6000


def _html_to_text(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(separator=" ")


def _extract_eml_body(msg) -> str:
    plain, html = None, None
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        if part.get_content_disposition() == "attachment":
            continue
        ctype = part.get_content_type()
        if ctype == "text/plain" and plain is None:
            try:
                plain = part.get_content()
            except Exception:
                pass
        elif ctype == "text/html" and html is None:
            try:
                html = part.get_content()
            except Exception:
                pass
    if plain:
        return plain[:BODY_CHAR_LIMIT]
    if html:
        return _html_to_text(html)[:BODY_CHAR_LIMIT]
    return ""


def parse_eml(path: str) -> dict:
    with open(path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    from_name, from_email = email.utils.parseaddr(msg.get("from", ""))
    return {
        "filename": os.path.basename(path),
        "subject": msg.get("subject", "") or "",
        "sender_display_name": from_name,
        "sender_email": from_email,
        "body_text": _extract_eml_body(msg),
        "source_type": "eml",
    }


def parse_msg(path: str) -> dict:
    m = extract_msg.Message(path)
    try:
        body = m.body or ""
        if not body and getattr(m, "htmlBody", None):
            html = m.htmlBody
            if isinstance(html, bytes):
                html = html.decode("utf-8", errors="ignore")
            body = _html_to_text(html)
        sender_email = getattr(m, "senderEmailAddress", "") or ""
        return {
            "filename": os.path.basename(path),
            "subject": m.subject or "",
            "sender_display_name": m.sender or "",
            "sender_email": sender_email,
            "body_text": (body or "")[:BODY_CHAR_LIMIT],
            "source_type": "msg",
        }
    finally:
        m.close()


def parse_email_file(path: str) -> dict:
    if path.lower().endswith(".eml"):
        return parse_eml(path)
    if path.lower().endswith(".msg"):
        return parse_msg(path)
    raise ValueError(f"Unsupported email file type: {path}")
