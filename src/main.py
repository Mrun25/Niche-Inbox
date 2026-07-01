"""
main.py — Starts the Flask web server and APScheduler together.
Run this file to launch the entire application.

Usage:
    python main.py
"""

import os
import sys
import time
import base64
import threading
import urllib.request
import urllib.error

# Force UTF-8 output so Unicode characters print correctly on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

from dotenv import load_dotenv
load_dotenv()

from src.core.database import init_db
from src.scripts.onboarding import run_onboarding
from src.core.scheduler import create_scheduler

TOKEN_FILE = "/etc/secrets/token.json" if os.path.exists("/etc/secrets/token.json") else "token.json"

# Exposed so web/preferences.py can reschedule after new user activates
scheduler_instance = None


def _wait_for_flask(port: int = 5000, timeout: int = 15) -> bool:
    """Poll localhost until Flask is accepting connections."""
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
    from src.scripts.setup_auth import setup_auth

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
                try:
                    creds.refresh(Request())
                    with open(TOKEN_FILE, "w") as f:
                        f.write(creds.to_json())
                    print("[main] Gmail token refreshed.")
                except Exception as e:
                    print(f"[main] Gmail token refresh failed: {e}. Re-running OAuth2 setup...")
                    if os.path.exists(TOKEN_FILE):
                        os.remove(TOKEN_FILE)
                    from src.scripts.setup_auth import setup_auth
                    setup_auth()
            else:
                print("[main] Gmail token invalid — re-running OAuth2 setup...")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                from src.scripts.setup_auth import setup_auth
                setup_auth()
    print("[main] Gmail auth OK.")


def _restore_db_from_env():
    """On Render, the SQLite file is wiped on restart. Restore it from the
    DB_BACKUP env var (base64-encoded content of digest.db) if available."""
    backup_b64 = os.getenv("DB_BACKUP")
    if not backup_b64:
        print("[main] No DB_BACKUP env var found — starting with fresh database.")
        return
    try:
        db_bytes = base64.b64decode(backup_b64)
        with open("digest.db", "wb") as f:
            f.write(db_bytes)
        print(f"[main] Database restored from DB_BACKUP ({len(db_bytes):,} bytes).")
    except Exception as e:
        print(f"[main] WARNING: DB_BACKUP restore failed: {e} — starting fresh.")


def _start_self_ping(port: int):
    """Ping our own /ping endpoint every 10 minutes to prevent Render
    free-tier from putting the process to sleep."""
    base_url = os.getenv("BASE_URL", f"http://localhost:{port}")
    ping_url = base_url.rstrip("/") + "/ping"

    def _loop():
        # Wait for Flask to be fully up before first ping
        time.sleep(30)
        while True:
            try:
                urllib.request.urlopen(ping_url, timeout=10)
                print(f"[main] Self-ping OK → {ping_url}")
            except urllib.error.HTTPError as e:
                # Any HTTP response (even 4xx) means the server is alive
                print(f"[main] Self-ping HTTP {e.code} (server alive) → {ping_url}")
            except Exception as e:
                print(f"[main] Self-ping FAILED: {e}")
            time.sleep(600)  # 10 minutes

    t = threading.Thread(target=_loop, daemon=True, name="SelfPingThread")
    t.start()
    print(f"[main] Self-ping watchdog started (every 10 min → {ping_url}).")


def main():
    global scheduler_instance

    # 1. Always sync secrets from env vars — on Render, files are wiped on each
    #    restart so we must re-write them unconditionally every startup.
    credentials_json = os.getenv("CREDENTIALS_JSON")
    token_json = os.getenv("TOKEN_JSON")

    if credentials_json:
        with open("credentials.json", "w") as f:
            f.write(credentials_json)
        print("[main] credentials.json written from CREDENTIALS_JSON env var.")

    if token_json:
        with open("token.json", "w") as f:
            f.write(token_json)
        print("[main] token.json written from TOKEN_JSON env var.")

    # 2. Restore SQLite database from base64 backup if available
    _restore_db_from_env()

    # 3. Ensure Gmail OAuth2 is authorised BEFORE anything tries to send email
    _ensure_gmail_auth()

    # 4. Initialise database schema (safe to call on existing DB)
    init_db()
    print("[main] Database initialised.")

    # 5. Start the background scheduler (includes 30-min watchdog job)
    scheduler_instance = create_scheduler()
    scheduler_instance.start()
    print("[main] Scheduler started.")

    # 6. Start Flask in a background thread so it doesn't block onboarding
    from src.api.preferences import app
    port = int(os.getenv("PORT", 5000))

    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False),
        daemon=True,
        name="FlaskThread",
    )
    flask_thread.start()
    print(f"[main] Flask starting on http://localhost:{port} ...")

    # 7. Wait for Flask to be ready, THEN send onboarding emails
    if _wait_for_flask(port):
        print(f"[main] Flask is ready.")
    else:
        print("[main] Flask readiness timeout — proceeding with onboarding anyway.")

    # 8. Start self-ping to keep Render free tier awake
    _start_self_ping(port)

    run_onboarding()

    # 9. Keep the main thread alive (scheduler + Flask daemon thread run in bg)
    print("[main] App running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[main] Shutting down...")
        scheduler_instance.shutdown(wait=False)
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("====== FATAL CRASH IN MAIN.PY ======", flush=True)
        traceback.print_exc()
        print("====================================", flush=True)
        sys.exit(1)
