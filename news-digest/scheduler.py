"""
scheduler.py
------------
Uses APScheduler to run the digest pipeline every day
at the time specified in the user's profile.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from user_profile import load_profile
from news_fetcher import fetch_all_topics
from summarizer import generate_newsletter
from email_sender import send_digest


def run_digest(profile_path: str):
    """Full pipeline: fetch → summarize → email."""
    print("\n Running digest pipeline...")

    profile = load_profile(profile_path)
    topics = profile["topics"]
    email  = profile["email"]

    print(f"  Topics: {', '.join(topics)}")
    articles = fetch_all_topics(topics)

    print("  Generating newsletter with Mistral...")
    html = generate_newsletter(articles)

    print(f"  Sending email to {email}...")
    send_digest(email, html)

    print("  Done.\n")


def start_scheduler(profile_path: str):
    """Start the blocking scheduler based on profile delivery time."""
    profile = load_profile(profile_path)
    delivery_time = profile.get("delivery_time", "08:00")
    timezone      = profile.get("timezone", "UTC")
    hour, minute  = delivery_time.split(":")

    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(
        run_digest,
        trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=timezone),
        args=[profile_path],
        id="daily_digest",
        name="Daily News Digest",
    )

    print(f" Scheduler started. Digest will be emailed daily at {delivery_time} {timezone}.")
    print(" Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n Scheduler stopped.")
