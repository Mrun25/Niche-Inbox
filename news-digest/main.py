"""
Daily News Digest - Main Entry Point
Run this file to start the app.

Usage:
  python main.py           — first-run setup (if needed), then start scheduler
  python main.py --test    — run the full pipeline once immediately and exit
"""

from setup_wizard import run_setup
from scheduler import start_scheduler, run_digest
from user_profile import load_profile
import os
import sys

def main():
    profile_path = "config/user_profile.json"
    run_now = "--test" in sys.argv or "--run-now" in sys.argv

    if not os.path.exists(profile_path):
        print("\n Welcome to Daily News Digest!\n")
        run_setup(profile_path)

    if run_now:
        print("\n --test flag detected: running digest pipeline immediately...\n")
        run_digest(profile_path)
        return

    print("\n Daily News Digest is running.")
    print(" Your digest will be sent at the scheduled time.")
    print(" Press Ctrl+C to stop.\n")

    start_scheduler(profile_path)

if __name__ == "__main__":
    main()
