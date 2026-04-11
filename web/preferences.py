"""
web/preferences.py — Flask routes for the preference form and submission.
"""

import os
import sys
# Ensure project root is on sys.path before any local-module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import traceback
import threading
from flask import Flask, request, render_template, abort

from database import get_user_by_token, activate_user
from news_fetcher import fetch_articles
from summarizer import build_newsletter
from email_sender import send_email
from scheduler import schedule_all_users

app = Flask(__name__, template_folder="../templates")
app.secret_key = os.getenv("SECRET_KEY", "changeme-in-production")

TOPICS = [
    "Top Headlines",
    "Business & Economy",
    "Technology",
    "Science & Health",
    "Politics & World Affairs",
    "Sports",
    "Entertainment & Culture",
    "Environment & Climate",
    "Job Openings & Careers",
    "Crime & Justice",
    "Travel & Tourism",
    "Food & Lifestyle",
    "Education",
    "Defence & Military",
    "Law & Policy",
]

TIMEZONES = [
    "UTC",
    "US/Eastern",
    "US/Central",
    "US/Mountain",
    "US/Pacific",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Kolkata",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Dubai",
    "Australia/Sydney",
    "America/Sao_Paulo",
]


@app.route("/")
def index():
    return "Niche Inbox is running.", 200

@app.route("/setup")
def setup():
    token = request.args.get("token", "")
    user = get_user_by_token(token)
    if not user:
        abort(404)
    if user["status"] == "active":
        return render_template("success.html", already_done=True)
    return render_template("preferences.html", token=token, topics=TOPICS, timezones=TIMEZONES)


@app.route("/submit", methods=["POST"])
def submit():
    token = request.form.get("token", "")
    user = get_user_by_token(token)
    if not user:
        abort(404)

    topics = request.form.getlist("topics")
    delivery_time = request.form.get("delivery_time", "08:00")
    timezone = request.form.get("timezone", "UTC")

    if not topics:
        return render_template(
            "preferences.html",
            token=token,
            topics=TOPICS,
            timezones=TIMEZONES,
            error="Please select at least one topic.",
        )

    # Save to DB and activate — commit is fully complete before we spawn the thread
    activate_user(token, topics, delivery_time, timezone)
    print(f"[web] User activated: {user['email']} | topics: {topics} | time: {delivery_time} {timezone}")

    # Re-schedule all users so this user's job is added to the scheduler
    from main import scheduler_instance
    if scheduler_instance:
        schedule_all_users(scheduler_instance)

    email = user["email"]
    thread = threading.Thread(
        target=_send_immediate_digest,
        args=(email, topics),
        daemon=True,
        name=f"ImmediateDigest-{email}",
    )
    thread.start()

    return render_template(
        "success.html",
        already_done=False,
        delivery_time=delivery_time,
        timezone=timezone,
    )


def _send_immediate_digest(email: str, topics: list):
    from datetime import date
    print(f"[web] Sending immediate digest to: {email}")
    try:
        articles = fetch_articles(topics)
        print(f"[web] Articles fetched for {email}. Building newsletter...")
        html = build_newsletter(email, articles)
        today = date.today().strftime("%B %d, %Y")
        send_email(email, f"Niche Inbox -- {today} (First Edition!)", html)
        print(f"[web] Immediate digest sent OK to: {email}")
    except Exception as e:
        print(f"[web] FAILED to send immediate digest to {email}: {e}")
        print("[web] Full traceback:")
        traceback.print_exc()
