"""
email_sender.py
---------------
Sends the generated HTML newsletter via the Gmail API using OAuth2.

First run: opens a browser window for Google login + permission grant.
After that: token.json is reused silently — no password ever stored.

Setup:
  1. Go to console.cloud.google.com → New Project
  2. Enable the Gmail API
  3. APIs & Services → Credentials → Create OAuth 2.0 Client ID (Desktop app)
  4. Download credentials.json and place it in this project folder
  5. Run the app — browser opens once for login
  6. token.json is created and reused on every future run
"""

import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Only request permission to send email — nothing else
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Resolve paths relative to this file so the app works from any directory
_HERE        = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH   = os.path.join(_HERE, "credentials.json")
TOKEN_PATH   = os.path.join(_HERE, "token.json")


def _get_gmail_service():
    """
    Authenticate with Gmail OAuth2 and return an authorised service object.
    Opens a browser on first run; uses token.json silently thereafter.
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[email_sender] Token refresh failed: {e}. Re-authenticating...")
                if not os.path.exists(CREDS_PATH):
                    raise FileNotFoundError(
                        f"credentials.json not found at {CREDS_PATH}.\n"
                        "Download it from: console.cloud.google.com → "
                        "APIs & Services → Credentials → OAuth 2.0 Client IDs"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            if not os.path.exists(CREDS_PATH):
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDS_PATH}.\n"
                    "Download it from: console.cloud.google.com → "
                    "APIs & Services → Credentials → OAuth 2.0 Client IDs"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_digest(to_email: str, html_content: str):
    """
    Send the HTML newsletter to the given email address via the Gmail API.
    Authenticates using OAuth2 — no Gmail App Password required.
    """
    today   = date.today().strftime("%B %d, %Y")
    subject = f"Your Daily News Digest — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = "me"          # Gmail API replaces "me" with the authenticated address
    msg["To"]      = to_email

    plain_text = "Your daily news digest is ready. Please view this email in an HTML-capable client."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    raw_bytes = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    try:
        service = _get_gmail_service()
        service.users().messages().send(
            userId="me",
            body={"raw": raw_bytes}
        ).execute()
        print(f"  ✅ Digest sent to {to_email} via Gmail API")
    except HttpError as e:
        print(f"  ❌ [Gmail API] Failed to send: {e}")
        raise
