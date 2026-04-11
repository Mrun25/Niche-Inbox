"""
onboarding.py — Detects new users from admin.py and sends them a setup email
with a link to the preference form.
"""

import os
from admin import RECIPIENTS
from database import add_pending_user, get_user_by_email
from email_sender import send_email


def send_onboarding_email(email: str, token: str):
    base_url = os.getenv("BASE_URL", "http://localhost:5000")
    setup_link = f"{base_url}/setup?token={token}"

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=EB+Garamond:ital,wght@0,400;0,600;1,400&display=swap');
    body {{
      margin: 0; padding: 0;
      background: #f5f0e8;
      font-family: 'EB Garamond', Georgia, serif;
      color: #1a1208;
    }}
    .wrapper {{
      max-width: 580px;
      margin: 40px auto;
      background: #fffdf7;
      border: 1px solid #c8b89a;
      border-top: 6px solid #1a1208;
    }}
    .masthead {{
      padding: 32px 40px 20px;
      border-bottom: 3px double #1a1208;
      text-align: center;
    }}
    .paper-name {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 36px;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #1a1208;
      margin: 0 0 4px;
    }}
    .edition {{
      font-size: 12px;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: #7a6a4a;
    }}
    .content {{
      padding: 32px 40px;
    }}
    .headline {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 26px;
      line-height: 1.3;
      margin: 0 0 20px;
      border-bottom: 1px solid #c8b89a;
      padding-bottom: 16px;
    }}
    p {{
      font-size: 17px;
      line-height: 1.7;
      margin: 0 0 16px;
    }}
    .cta-wrap {{
      text-align: center;
      margin: 32px 0;
    }}
    .cta {{
      display: inline-block;
      background: #1a1208;
      color: #fffdf7 !important;
      text-decoration: none;
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 15px;
      letter-spacing: 2px;
      text-transform: uppercase;
      padding: 14px 36px;
    }}
    .footer {{
      padding: 16px 40px;
      border-top: 1px solid #c8b89a;
      font-size: 12px;
      color: #7a6a4a;
      text-align: center;
      letter-spacing: 1px;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="masthead">
      <div class="paper-name">Niche Inbox</div>
      <div class="edition">Your Personalised News Chronicle</div>
    </div>
    <div class="content">
      <div class="headline">You Have Been Invited to Receive Your Daily Briefing</div>
      <p>Dear Reader,</p>
      <p>You have been cordially invited to receive <em>Niche Inbox</em> — a personalised news briefing curated to your interests and delivered to your inbox each morning.</p>
      <p>To begin, kindly take a moment to select your preferred news topics and the time at which you would like your digest delivered each day.</p>
      <div class="cta-wrap">
        <a href="{setup_link}" class="cta">Set Your Preferences</a>
      </div>
      <p>Upon submitting your preferences, you will receive today's digest immediately — and every day thereafter at your chosen hour.</p>
      <p>This link is unique to you and expires once used.</p>
    </div>
    <div class="footer">
      Niche Inbox &nbsp;·&nbsp; Delivered with care &nbsp;·&nbsp; Unsubscribe anytime
    </div>
  </div>
</body>
</html>
"""
    send_email(email, "You're Invited — Set Up Your Niche Inbox", html)


def run_onboarding():
    """Check RECIPIENTS list and send onboarding emails to any new users."""
    print("[onboarding] Checking for new recipients...")
    for email in RECIPIENTS:
        existing = get_user_by_email(email)
        if existing is None:
            token = add_pending_user(email)
            send_onboarding_email(email, token)
            print(f"[onboarding] Onboarding email sent -> {email}")
        elif existing["status"] == "pending":
            print(f"[onboarding] {email} is still pending (already sent).")
        else:
            print(f"[onboarding] {email} is already active. Skipping.")
