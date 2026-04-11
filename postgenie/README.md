# ✨ PostGenie — AI Blog Automation SaaS

AI-powered blog automation platform. Users connect their blog, configure topics and schedule, and PostGenie auto-generates + publishes SEO posts on autopilot.

## Architecture

```
User → Streamlit app (UI)
      ↓
      Google OAuth → Supabase (user data)
      ↓
      Connect Blogger/WordPress → Store refresh tokens
      ↓
      Create schedule (topics + frequency)
      ↓
GitHub Actions cron (hourly) → Worker script
      ↓
      Fetch due schedules → Claude API → Publish to blog
```

## Tech Stack

- **Frontend:** Streamlit
- **Database:** Supabase (Postgres)
- **AI:** Anthropic Claude (Haiku 4.5)
- **Scheduler:** GitHub Actions cron
- **Payments:** Paddle
- **Blogs:** Google Blogger API v3, WordPress REST API

## Project Structure

```
postgenie/
├── app.py                  # Main Streamlit entry
├── schema.sql              # Supabase DB schema
├── requirements.txt
├── Procfile
├── .env.example
├── .streamlit/config.toml
├── lib/
│   ├── config.py           # Env var loader
│   ├── auth.py             # Google OAuth
│   ├── supabase_client.py  # DB client
│   ├── claude.py           # Claude API wrapper
│   ├── topics.py           # Google News RSS topic fetcher
│   └── publishers.py       # Blogger/WordPress publishers
├── pages_lib/
│   ├── connect_blog.py     # Blog connection UI
│   ├── schedules.py        # Schedule config UI
│   ├── posts.py            # Post history UI
│   └── upgrade.py          # Paddle upgrade UI
└── scripts/
    └── worker.py           # Cron worker (runs hourly)
```

## Setup

### 1. Supabase Setup
1. Create project at [supabase.com](https://supabase.com)
2. Run `schema.sql` in SQL Editor
3. Get URL + anon key + service role key from Project Settings

### 2. Google OAuth
1. [Google Cloud Console](https://console.cloud.google.com) → Create OAuth 2.0 Client ID
2. Authorized redirect URIs: `http://localhost:8501/` (dev) + your production URL
3. Enable **Blogger API v3**

### 3. Anthropic API Key
- Get one at [console.anthropic.com](https://console.anthropic.com)

### 4. Local Dev
```bash
cd postgenie
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your keys
streamlit run app.py
```

### 5. Deploy (Render / Streamlit Cloud)
- **Streamlit Cloud:** Point to `postgenie/app.py`, add secrets in dashboard
- **Render:** Use `Procfile`, add env vars

### 6. Cron Worker (GitHub Actions)
The worker runs automatically via `.github/workflows/postgenie-worker.yml`.
Add these GitHub Secrets:
- `POSTGENIE_SUPABASE_URL`
- `POSTGENIE_SUPABASE_SERVICE_KEY`
- `ANTHROPIC_API_KEY`
- `POSTGENIE_BLOGGER_CLIENT_ID`
- `POSTGENIE_BLOGGER_CLIENT_SECRET`

## Pricing Plans

| Plan | Price | Blogs | Posts/day | Features |
|------|-------|-------|-----------|----------|
| Free | $0 | 1 | 1/week | Basic topics |
| Basic | $9/mo | 1 | 1 | All categories |
| Pro | $29/mo | 3 | 3 | Custom topics |
| Agency | $99/mo | 10 | 30 | API access |

## MVP Roadmap

- [x] Project structure + DB schema
- [x] Google OAuth login
- [x] Streamlit UI (landing + dashboard)
- [x] Blog connection (Blogger + WordPress)
- [x] Schedule creation UI
- [x] Cron worker (GitHub Actions)
- [x] Paddle upgrade UI
- [ ] Paddle webhook handler (subscription sync)
- [ ] Email notifications
- [ ] Analytics dashboard
- [ ] API access (for Agency plan)
