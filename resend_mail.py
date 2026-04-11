import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()
from database import init_db, get_user_by_email, add_pending_user
from onboarding import send_onboarding_email
from scheduler import deliver_digest
import json

def main():
    init_db()
    email = "youthsunrise25@gmail.com"
    user = get_user_by_email(email)

    if user is None:
        token = add_pending_user(email)
        send_onboarding_email(email, token)
        print(f"User wasn't in DB. Added and sent onboarding email to {email}")
    elif user["status"] == "pending":
        token = user["token"]
        send_onboarding_email(email, token)
        print(f"User is pending. Resent onboarding email to {email}")
    elif user["status"] == "active":
        topics = json.loads(user["topics"] or "[]")
        print(f"User is active with topics: {topics}. Resending digest...")
        deliver_digest(email, topics)

if __name__ == "__main__":
    main()
