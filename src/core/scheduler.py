"""
scheduler.py — APScheduler: one daily job per active user at their chosen time.
"""

import json
import logging
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.database import get_all_active_users
from src.core.news_fetcher import fetch_articles
from src.core.summarizer import build_newsletter
from src.core.email_sender import send_email

logging.getLogger("apscheduler").setLevel(logging.WARNING)


def deliver_digest(email: str, topics: list):
    """Fetch news, summarize, and email to a single user."""
    print(f"[scheduler] Delivering digest -> {email} | topics: {topics}")
    try:
        articles = fetch_articles(topics)
        html = build_newsletter(email, articles)
        today = date.today().strftime("%B %d, %Y")
        send_email(email, f"Niche Inbox — {today}", html)
        print(f"[scheduler] Digest sent OK -> {email}")
    except Exception as e:
        print(f"[scheduler] FAILED for {email}: {e}")


def schedule_all_users(scheduler: BackgroundScheduler):
    """Load all active users and schedule their Niche Inbox jobs."""
    for job in scheduler.get_jobs():
        if job.id.startswith("digest_"):
            job.remove()

    users = get_all_active_users()
    print(f"[scheduler] Scheduling {len(users)} active user(s)...")

    for user in users:
        email = user["email"]
        topics = json.loads(user["topics"] or "[]")
        delivery_time = user["delivery_time"]
        timezone = user["timezone"] or "UTC"

        if not delivery_time or not topics:
            print(f"[scheduler] Skipping {email} — incomplete preferences.")
            continue

        try:
            hour, minute = map(int, delivery_time.split(":"))
        except ValueError:
            print(f"[scheduler] Invalid delivery_time for {email}: {delivery_time}")
            continue

        try:
            scheduler.add_job(
                deliver_digest,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
                id=f"digest_{email}",
                args=[email, topics],
                replace_existing=True,
            )
            print(f"[scheduler] Scheduled {email} at {delivery_time} {timezone}")
        except Exception as e:
            print(f"[scheduler] FAILED to schedule {email}: {e}")


def _watchdog_reschedule():
    """Heartbeat job: re-registers all user digest jobs every 30 minutes.
    Ensures scheduled digests survive if the scheduler loses its job list
    after a Render sleep/wake cycle."""
    from apscheduler.schedulers.background import BackgroundScheduler
    import src.main as _main
    sched = getattr(_main, "scheduler_instance", None)
    if sched and sched.running:
        print("[scheduler] Watchdog: re-running schedule_all_users...")
        schedule_all_users(sched)
    else:
        print("[scheduler] Watchdog: scheduler not running, skipping.")


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    schedule_all_users(scheduler)

    # Watchdog: re-schedule all users every 30 minutes to survive restarts
    scheduler.add_job(
        _watchdog_reschedule,
        trigger=CronTrigger(minute="*/30"),
        id="watchdog_reschedule",
        replace_existing=True,
    )
    print("[scheduler] Watchdog heartbeat job registered (every 30 min).")

    return scheduler
