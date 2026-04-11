# Daily News Digest

A personalized AI-powered newsletter bot that fetches news based on your interests and emails you a clean digest every day at your chosen time.

---

## How it works

```
User preferences (topics + time + email)
        ↓
  NewsAPI  →  Fetch articles per topic
        ↓
  Mistral API  →  Summarize & format into HTML newsletter
        ↓
  Gmail API (OAuth2)  →  Send to your inbox — no password stored
```

---

## Project structure

```
news-digest/
├── main.py              # Entry point — run this to start the app
├── setup_wizard.py      # First-run CLI dialog for preferences
├── user_profile.py      # Load/save user profile JSON
├── news_fetcher.py      # Fetch articles from NewsAPI
├── summarizer.py        # Generate newsletter via Mistral API
├── email_sender.py      # Send email via Gmail API (OAuth2)
├── scheduler.py         # APScheduler daily trigger
├── requirements.txt     # Python dependencies
├── credentials.json     # ← You place this here (from Google Cloud Console)
├── token.json           # ← Auto-created after first login (do not commit)
├── .env.example         # Environment variable template
├── .gitignore
└── config/
    └── user_profile.json   (auto-created on first run)
```

---

## Setup instructions

### 1. Clone or download the project

```bash
cd news-digest
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API keys

Copy the example env file and fill in your two keys:

```bash
cp .env.example .env
```

| Variable | Where to get it |
|---|---|
| `MISTRAL_API_KEY` | [console.mistral.ai](https://console.mistral.ai) — free account |
| `NEWSAPI_KEY` | [newsapi.org](https://newsapi.org) — free tier: 100 req/day |

### 5. Set up Gmail OAuth2 (one-time, ~3 minutes)

This replaces the Gmail App Password entirely. You only do this once.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → **New Project**
2. In the project, go to **APIs & Services → Library** → search for **Gmail API** → Enable it
3. Go to **APIs & Services → Credentials** → **Create Credentials → OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Name it anything (e.g. `news-digest`)
4. Click **Download JSON** → rename the file to `credentials.json`
5. Place `credentials.json` in the project root (same folder as `main.py`)

> **Note:** `credentials.json` and `token.json` are in `.gitignore` — they will never be committed.

### 6. Run the app

```bash
python main.py
```

**First run:**
- Setup wizard asks for your topics, delivery time, and recipient email
- A **browser window opens** asking you to log into Google and grant send permission
- After you approve, `token.json` is saved locally
- The digest pipeline runs (or schedules, depending on flags)

**All subsequent runs:**
- `token.json` is reused silently — no browser, no login, no password

---

## Running the pipeline immediately (for testing)

```bash
python main.py --test
```

---

## Available topics

| Topic | Source |
|---|---|
| Headlines | NewsAPI general category |
| Technology | NewsAPI technology category |
| Politics | NewsAPI politics category |
| Sports | NewsAPI sports category |
| World Stocks | NewsAPI business category |
| Job Openings | NewsAPI everything (keyword search) |
| Science | NewsAPI science category |
| Entertainment | NewsAPI entertainment category |

---

## Changing your preferences

Delete `config/user_profile.json` and re-run `main.py` to go through setup again:

```bash
rm config/user_profile.json
python main.py
```

---

## Running in the background (optional)

### On Windows — use Task Scheduler to run `main.py` at startup.

### On Linux/Mac — use `nohup`:
```bash
nohup python main.py &
```

---

## Troubleshooting

**Browser doesn't open for Google login?**
- Make sure `credentials.json` is in the project root folder.
- Check that the Gmail API is enabled in your Google Cloud project.

**`token.json` expired or invalid?**
- Delete `token.json` and re-run — the browser login flow will repeat once.

**No articles fetched?**
- Verify your `NEWSAPI_KEY` in `.env`.
- Free NewsAPI tier only works for `top-headlines` from a limited set of countries.

**Mistral API error?**
- Check your `MISTRAL_API_KEY` in `.env`.
- Ensure you have available credits at [console.mistral.ai](https://console.mistral.ai).

---

## Tech stack

- **Python 3.10+**
- **Mistral API** (`mistral-small`) — newsletter generation
- **NewsAPI** — article fetching
- **Gmail API + OAuth2** — email delivery (no App Password)
- **APScheduler** — daily scheduling
- **python-dotenv** — environment variable management

---

## License

MIT — free to use and modify.
