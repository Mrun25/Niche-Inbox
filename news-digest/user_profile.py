"""
user_profile.py
---------------
Helpers for loading and saving the user profile JSON.
"""

import json
import os


def load_profile(profile_path: str) -> dict:
    """Load user profile from JSON file."""
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Profile not found at {profile_path}")
    with open(profile_path, "r") as f:
        return json.load(f)


def save_profile(profile: dict, profile_path: str):
    """Save user profile to JSON file."""
    dir_name = os.path.dirname(profile_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)
