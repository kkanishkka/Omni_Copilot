import base64
import email as email_lib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from app.integrations.google_auth import build_credentials
import logging

logger = logging.getLogger(__name__)

# Placeholder/invalid addresses that should NEVER be sent to
_BLOCKED_ADDRESSES = {
    "user@example.com", "example@example.com", "test@test.com",
    "placeholder@email.com", "noreply@example.com",
}


def get_gmail_service(token_data: dict):
    creds = build_credentials(token_data)
    return build("gmail", "v1", credentials=creds)


def _validate_email_address(address: str) -> None:
    """Raise ValueError for obviously invalid/placeholder addresses."""
    addr = address.strip().lower()
    if not addr or "@" not in addr:
        raise ValueError(f"Invalid email address: '{address}'")
    if addr in _BLOCKED_ADDRESSES:
        raise ValueError(
            f"Blocked placeholder address '{address}'. "
            "Please provide a real recipient email address."
        )
    domain = addr.split("@")[-1]
    if domain in ("example.com", "test.com", "placeholder.com"):
        raise ValueError(
            f"'{address}' appears to be a placeholder address. "
            "Please provide the actual recipient's email."
        )


def list_emails(token_data: dict, max_results: int = 5, query: str = "is:unread") -> dict:
    """
    List emails — works for any count 1–20.
    Snippets are truncated to keep the response small enough for Groq.
    """
    # Clamp to safe range
    max_results = max(1, min(int(max_results), 20))

    service = get_gmail_service(token_data)
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    messages = results.get("messages", [])

    emails = []
    for msg in messages[:max_results]:
        try:
            detail = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "From", "Date"]
            ).execute()
            headers = {
                h["name"]: h["value"]
                for h in detail.get("payload", {}).get("headers", [])
            }
            snippet = detail.get("snippet", "")
            # Truncate long snippets to keep context window manageable
            if len(snippet) > 200:
                snippet = snippet[:200] + "…"

            emails.append({
                "id": msg["id"],
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": snippet,
            })
        except Exception as e:
            logger.warning(f"Failed to fetch email {msg['id']}: {e}")
            continue

    return {"emails": emails, "count": len(emails)}


def get_email_content(token_data: dict, message_id: str) -> dict:
    service = get_gmail_service(token_data)
    detail = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()
    headers = {
        h["name"]: h["value"]
        for h in detail.get("payload", {}).get("headers", [])
    }
    body = _extract_body(detail.get("payload", {}))
    # Truncate very long bodies
    if len(body) > 3000:
        body = body[:3000] + "\n\n[... truncated ...]"

    return {
        "id": message_id,
        "subject": headers.get("Subject", ""),
        "from": headers.get("From", ""),
        "date": headers.get("Date", ""),
        "body": body,
    }


def _extract_body(payload: dict) -> str:
    if payload.get("body", {}).get("data"):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    return ""


def send_email(token_data: dict, to: str, subject: str, body: str) -> dict:
    """Send a plain-text email. Validates recipient to block placeholder addresses."""
    _validate_email_address(to)

    service = get_gmail_service(token_data)
    message = email_lib.message.EmailMessage()
    message.set_content(body)
    message["To"] = to.strip()
    message["Subject"] = subject

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(
        userId="me", body={"raw": encoded}
    ).execute()

    logger.info(f"Email sent to {to}, message_id={sent.get('id')}")
    return {"sent": True, "message_id": sent.get("id"), "to": to}


def send_email_with_drive_link(
    token_data: dict,
    to: str,
    subject: str,
    body: str,
    file_id: str,
    file_name: str,
) -> dict:
    """
    Send an email that includes the shareable Google Drive link for a file.
    This is the correct tool for 'send a Drive file via email'.
    """
    _validate_email_address(to)

    # Get the shareable link from Drive
    from googleapiclient.discovery import build as gdrive_build
    creds = build_credentials(token_data)
    drive_service = gdrive_build("drive", "v3", credentials=creds)

    try:
        # Make file accessible via link
        drive_service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
            fields="id",
        ).execute()
        file_meta = drive_service.files().get(
            fileId=file_id, fields="webViewLink,name"
        ).execute()
        link = file_meta.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")
        display_name = file_meta.get("name", file_name)
    except Exception as e:
        logger.warning(f"Could not make file public, using direct link: {e}")
        link = f"https://drive.google.com/file/d/{file_id}/view"
        display_name = file_name

    full_body = f"{body}\n\n📎 {display_name}:\n{link}"

    service = get_gmail_service(token_data)
    message = email_lib.message.EmailMessage()
    message.set_content(full_body)
    message["To"] = to.strip()
    message["Subject"] = subject

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(
        userId="me", body={"raw": encoded}
    ).execute()

    logger.info(f"Email with Drive link sent to {to}, file={display_name}")
    return {
        "sent": True,
        "message_id": sent.get("id"),
        "to": to,
        "file_link": link,
        "file_name": display_name,
    }
