# System Architecture

## Overview
Niche Inbox is a Python-based daily news digest emailer that aggregates live news via NewsAPI, summarizes them using the Mistral AI API, and delivers beautifully formatted emails using Gmail OAuth2.

## High-Level Architecture

```mermaid
graph TD
    subgraph "Core System"
        main["src/main.py"] --> sched["src/core/scheduler.py"]
        main --> api["src/api/preferences.py Flask"]
        sched --> db[("SQLite Database")]
        api --> db
        
        sched --> fetcher["src/core/news_fetcher.py"]
        sched --> sum["src/core/summarizer.py"]
        sched --> mail["src/core/email_sender.py"]
    end
    
    fetcher -- "Fetch Headlines" --> newsapi(("NewsAPI"))
    sum -- "Summarize Articles" --> mistral(("Mistral API"))
    mail -- "Send Emails" --> gmail(("Gmail API"))
    
    user(("User")) -- "Onboarding Form" --> api
```

## Application Flow

### 1. Onboarding Flow
1. An admin adds a user's email to `src/scripts/admin.py`.
2. On startup, `src/scripts/onboarding.py` detects new users and sends an invitation email.
3. The user clicks the link, which opens the Flask web form `src/api/preferences.py`.
4. The user selects their preferred topics and delivery time.
5. The data is saved to `digest.db` and the user's daily scheduler is activated.

```mermaid
sequenceDiagram
    actor Admin
    actor User
    participant System
    participant Database
    
    Admin->>System: Add email to admin.py
    System->>Database: Save as Pending User
    System->>User: Send Onboarding Email
    User->>System: Submit Preferences Form
    System->>Database: Update to Active User & Save Preferences
    System->>User: Send Immediate Digest
    System->>System: Schedule Daily Digest
```

### 2. Daily Digest Flow
When the scheduled time arrives for a given user:

```mermaid
sequenceDiagram
    participant Scheduler
    participant NewsFetcher
    participant Summarizer
    participant EmailSender
    participant User
    
    Scheduler->>NewsFetcher: Fetch articles for user topics
    NewsFetcher-->>Scheduler: Return top articles
    Scheduler->>Summarizer: Send articles for summarization
    Summarizer-->>Scheduler: Return formatted HTML summary
    Scheduler->>EmailSender: Dispatch email
    EmailSender->>User: Deliver Digest Email
```

## Database Schema
The SQLite database `digest.db` contains a `users` table:
- `id` (INTEGER): Primary Key
- `email` (TEXT): User's email address
- `token` (TEXT): Unique onboarding token
- `topics` (TEXT): JSON array of selected topics
- `delivery_time` (TEXT): E.g., "08:00"
- `timezone` (TEXT): User's timezone (e.g., "America/New_York")
- `active` (INTEGER): 0 (pending) or 1 (active)
