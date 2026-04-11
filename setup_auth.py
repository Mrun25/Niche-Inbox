"""
setup_auth.py — Run this once to authorise Gmail OAuth2 and create token.json.

Usage:
    python setup_auth.py

Opens a browser window for Google login. On success, saves token.json to the
project root. All subsequent email sends use token.json silently.
"""

import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def setup_auth() -> bool:
    if not os.path.exists(CREDENTIALS_FILE):
        print("[auth] ERROR: credentials.json not found in project root.")
        print("[auth] Download it from Google Cloud Console > APIs & Services > Credentials.")
        return False

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.valid:
        print("[auth] token.json is already valid. No action needed.")
        return True

    if creds and creds.expired and creds.refresh_token:
        print("[auth] Refreshing expired token...")
        creds.refresh(Request())
    else:
        print("[auth] Opening browser for Google OAuth2 login...")
        print("[auth] Sign in with your.niche.inbox@gmail.com and click Allow.")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print("[auth] token.json saved successfully.")
    return True


if __name__ == "__main__":
    success = setup_auth()
    sys.exit(0 if success else 1)
