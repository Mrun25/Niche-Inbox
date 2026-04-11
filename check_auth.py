import sys, os, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

service = build("gmail", "v1", credentials=creds)

msg = MIMEMultipart("alternative")
msg["Subject"] = "Niche Inbox — Delivery Test"
msg["From"] = "your.niche.inbox@gmail.com"
msg["To"] = "youthsunrise25@gmail.com"
msg.attach(MIMEText("""
<html><body>
<p>Hello from <strong>Niche Inbox</strong>!</p>
<p>If you see this, email delivery is working correctly.</p>
</body></html>
""", "html"))

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
print(f"Message ID: {result['id']}")
print(f"Labels: {result['labelIds']}")
print("Done.")
