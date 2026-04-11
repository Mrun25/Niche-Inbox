"""
main.py — Starts the Flask web server and APScheduler together.
Run this file to launch the entire application.

Usage:
    python main.py
"""

import os
import sys
import time
import threading

# Force UTF-8 output so Unicode characters print correctly on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from database import init_db
from onboarding import run_onboarding
from scheduler import create_scheduler

TOKEN_FILE = "token.json"

# Exposed so web/preferences.py can reschedule after new user activates
scheduler_instance = None


def _wait_for_flask(port: int = 5000, timeout: int = 15) -> bool:
    """Poll localhost until Flask is accepting connections."""
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/", timeout=1)
            return True
        except urllib.error.HTTPError:
            # Flask is up but returned 404 for "/" — still means it's ready
            return True
        except Exception:
            time.sleep(0.3)
    return False


def _ensure_gmail_auth():
    """Check token.json exists and is valid; if not, run the OAuth2 browser flow."""
    from setup_auth import setup_auth

    if not os.path.exists(TOKEN_FILE):
        print("[main] token.json not found — launching Gmail OAuth2 setup...")
        ok = setup_auth()
        if not ok:
            print("[main] ERROR: Gmail auth failed. Cannot send emails. Exiting.")
            sys.exit(1)
    else:
        # Verify the token is still valid / refreshable
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                print("[main] Refreshing expired Gmail token...")
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
                print("[main] Gmail token refreshed.")
            else:
                print("[main] Gmail token invalid — re-running OAuth2 setup...")
                os.remove(TOKEN_FILE)
                from setup_auth import setup_auth
                setup_auth()
    print("[main] Gmail auth OK.")


def main():
    global scheduler_instance

    # 1. Ensure Gmail OAuth2 is authorised BEFORE anything tries to send email
    _ensure_gmail_auth()

    # 2. Initialise database
    init_db()
    print("[main] Database initialised.")

    # 3. Start the background scheduler
    scheduler_instance = create_scheduler()
    scheduler_instance.start()
    print("[main] Scheduler started.")

    # 4. Start Flask in a background thread so it doesn't block onboarding
    from web.preferences import app
    port = int(os.getenv("PORT", 5000))

    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False),
        daemon=True,
        name="FlaskThread",
    )
    flask_thread.start()
    print(f"[main] Flask starting on http://localhost:{port} ...")

    # 5. Wait for Flask to be ready, THEN send onboarding emails
    if _wait_for_flask(port):
        print(f"[main] Flask is ready.")
    else:
        print("[main] Flask readiness timeout — proceeding with onboarding anyway.")

    run_onboarding()

    # 6. Keep the main thread alive (scheduler + Flask daemon thread run in bg)
    print("[main] App running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[main] Shutting down...")
        scheduler_instance.shutdown(wait=False)
        sys.exit(0)


if __name__ == "__main__":
    main()
