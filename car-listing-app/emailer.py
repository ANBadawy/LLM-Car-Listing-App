import os, base64, mimetypes, json
from typing import List, Tuple, Optional
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _creds_path() -> str:
    """Return the path to the OAuth client credentials file."""
    return os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")


def _token_path() -> str:
    """Return the path to the cached OAuth token file."""
    return os.getenv("GMAIL_TOKEN_PATH", "token.json")


def get_gmail_service():
    """
    Build and return an authorized Gmail API service.
    """
    creds = None
    token_path = _token_path()

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(_creds_path(), SCOPES)
            # Opens a browser for user consent; stores refresh token for next runs
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _guess_mime(filename: str) -> Tuple[str, str]:
    """
    Guess MIME type from filename.

    Returns:
        (maintype, subtype), defaulting to ("application", "octet-stream").
    """
    ctype, _ = mimetypes.guess_type(filename)
    if not ctype:
        return "application", "octet-stream"
    main, sub = ctype.split("/", 1)
    return main, sub


def build_message(
    to_addr: str,
    subject: str,
    body_text: str,
    attachments: List[Tuple[str, bytes, Optional[str]]],
    ) -> EmailMessage:
    """
    Build an EmailMessage with optional attachments.
    """
    msg = EmailMessage()
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body_text)

    for filename, data, explicit_mime in attachments:
        if explicit_mime and "/" in explicit_mime:
            main, sub = explicit_mime.split("/", 1)
        else:
            main, sub = _guess_mime(filename)
        msg.add_attachment(data, maintype=main, subtype=sub, filename=filename)

    return msg


def send_message(service, mime_msg: EmailMessage):
    """
    Send an EmailMessage via the Gmail API.
    """
    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_car_payload(
    to_addr: str,
    subject_prefix: str,
    doc: dict,
    image_meta: Optional[dict],
    ):
    """
    Compose and send the car listing email with JSON and optional image.
    """
    # Prepare JSON attachment
    json_bytes = json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")
    attachments = [("car.json", json_bytes, "application/json")]

    # Optional image attachment
    if image_meta and image_meta.get("data"):
        img_name = image_meta.get("name") or "car.jpg"
        img_mime = image_meta.get("type") or None  # e.g., "image/jpeg"
        attachments.append((img_name, image_meta["data"], img_mime))

    subject = f"{subject_prefix} Car listing"
    body = "New car listing attached (JSON + image)."

    svc = get_gmail_service()
    msg = build_message(to_addr, subject, body, attachments)
    return send_message(svc, msg)
