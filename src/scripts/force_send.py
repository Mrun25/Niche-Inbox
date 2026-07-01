import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import json
from src.core.database import get_all_active_users
from src.core.scheduler import deliver_digest

def trigger_all():
    users = get_all_active_users()
    print(f"[force_send] Found {len(users)} active users in database.")
    for user in users:
        email = user["email"]
        topics = json.loads(user["topics"] or "[]")
        print(f"[force_send] Triggering immediate digest for: {email}")
        print(f"[force_send] Topics: {topics}")
        
        # This will fetch, summarize and send
        deliver_digest(email, topics)

if __name__ == "__main__":
    trigger_all()
    print("[force_send] Finished.")
