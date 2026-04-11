"""
setup_wizard.py
---------------
First-run dialog that collects user preferences:
  - Topics of interest
  - Delivery time
  - Recipient email address
Saves everything to config/user_profile.json
"""

import json
import os
import re

AVAILABLE_TOPICS = [
    "Headlines",
    "Technology",
    "Politics",
    "Sports",
    "World Stocks",
    "Job Openings",
    "Science",
    "Entertainment",
]


def run_setup(profile_path: str):
    print("=" * 50)
    print("  SETUP: Personalize your daily news digest")
    print("=" * 50)

    # --- Topic selection ---
    print("\nAvailable topics:")
    for i, topic in enumerate(AVAILABLE_TOPICS, 1):
        print(f"  [{i}] {topic}")

    selected_topics = []
    while not selected_topics:
        raw = input(
            "\nEnter topic numbers separated by commas (e.g. 1,3,5): "
        ).strip()
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            selected_topics = [
                AVAILABLE_TOPICS[i]
                for i in indices
                if 0 <= i < len(AVAILABLE_TOPICS)
            ]
            if not selected_topics:
                print("  No valid topics selected. Please try again.")
        except ValueError:
            print("  Invalid input. Please enter numbers only.")

    print(f"\n  Selected: {', '.join(selected_topics)}")

    # --- Delivery time ---
    delivery_time = ""
    while not delivery_time:
        raw = input("\nDelivery time (24h format, e.g. 08:00): ").strip()
        if re.match(r"^\d{2}:\d{2}$", raw):
            hour, minute = int(raw[:2]), int(raw[3:])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                delivery_time = raw
            else:
                print("  Invalid time. Use HH:MM between 00:00 and 23:59.")
        else:
            print("  Invalid format. Use HH:MM (e.g. 07:30).")

    # --- Recipient email ---
    email = ""
    while not email:
        raw = input("\nYour email address (digest will be sent here): ").strip()
        if re.match(r"^[^@]+@[^@]+\.[^@]+$", raw):
            email = raw
        else:
            print("  Invalid email. Please try again.")

    # --- Save profile ---
    profile = {
        "email": email,
        "topics": selected_topics,
        "delivery_time": delivery_time,
        "timezone": "Asia/Kolkata",
    }

    os.makedirs(os.path.dirname(profile_path), exist_ok=True)
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)

    print("\n  Setup complete! Profile saved.")
    print(f"  Digest will be emailed to {email} daily at {delivery_time}.\n")
    return profile
