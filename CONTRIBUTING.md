# Contributing to Niche-Inbox

Niche-Inbox is a self-hosted personalised news digest.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup_wizard.py   # one-time configuration
```

## Tests

```bash
pytest
```

## Pull requests

Keep PRs focused on one change. The digest pipeline is fetch -> summarise ->
send, so say which stage your change touches and how you verified it. Never
commit credentials or a generated config - config belongs to the local
install, not the repo.
