# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trytimeback is an AI-powered YouTube lecture summarizer SaaS built with Streamlit. Users sign in via Google OAuth, paste a YouTube URL, and get AI-generated key-point "shorts" (5 clips), a full summary, and a downloadable PDF. Monetized via Paddle subscriptions (Basic/Pro, Monthly/Yearly).

**Live URL:** https://trytimeback.com

## Commands

```bash
# Run locally
streamlit run app.py

# Run with specific port
streamlit run app.py --server.port 8501 --server.headless true

# Full deployment command (matches Procfile)
python patch_meta.py && streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0

# Run auto blog publisher manually
python scripts/auto_blog.py

# Trigger auto blog via GitHub Actions
# Actions tab → Auto Blog Publisher → Run workflow
```

No test suite exists. Manual testing only.

## Architecture

### app.py (~2000 lines, single-file application)

The app is structured in this order:
1. **Config & SEO injection** (lines ~1-80): Page config, meta tags via `window.top` JS injection
2. **OAuth functions** (~330-420): `get_google_login_url()`, `handle_oauth_callback()` — Google OAuth 2.0 flow
3. **YouTube processing pipeline** (~420-680):
   - `fetch_subtitles()` — Uses `youtube-transcript-api` with Webshare rotating proxy, falls back to direct
   - `get_video_info()` — YouTube Data API v3 for metadata
   - `analyze_with_gpt()` — GPT-4o-mini generates JSON with 5 key points + full summary
4. **PDF generation** (~680-760): `fpdf2` with Korean font support (NotoSansKR TTF files)
5. **Global CSS** (~760-1120): Dark theme, glassmorphism, responsive breakpoints (768px, 480px)
6. **Login page** (~1130-1390): Landing page with Google Sign-In, How It Works, Features, Policy sections
7. **Main app** (~1400-1950): URL input → analysis → shorts cards → PDF download
8. **Paddle pricing** (~1950-end): Payment integration via `components.html()` with iframe `window.top` escape

### Key Patterns

- **Paddle.js iframe escape:** Paddle checkout is injected into `window.top` because Streamlit components render in iframes. Links inside `components.html()` need `target="_top"` for external navigation.
- **Proxy-based subtitle fetching:** YouTube blocks server IPs, so Webshare residential proxy is used. Falls back to direct if proxy fails. Env vars: `WEBSHARE_PROXY_USER`, `WEBSHARE_PROXY_PASS`.
- **SEO at runtime:** `patch_meta.py` injects meta tags into Streamlit's compiled `index.html` at startup (not build time). Additional SEO via JS in `window.top.document`.
- **`st.markdown` HTML limitations:** Streamlit sanitizes HTML — tags like `<nav>`, `<svg>`, `<path>` get escaped. Use `streamlit.components.v1.html()` for complex HTML, but remember it renders in an iframe.

### scripts/auto_blog.py

Daily automated blog publisher: picks random SEO topic → Claude Haiku generates HTML post → publishes via Blogger API v3. Runs on GitHub Actions cron (`0 0 * * *` = 9 AM KST).

## Environment Variables

**App (via `.streamlit/secrets.toml` or env):**
- `OPENAI_API_KEY` — GPT-4o-mini
- `YOUTUBE_API_KEY` — YouTube Data API v3
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `REDIRECT_URI` — OAuth
- `WEBSHARE_PROXY_USER`, `WEBSHARE_PROXY_PASS` — Proxy (optional)

**Auto Blog (GitHub Secrets):**
- `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `BLOGGER_BLOG_ID`

## Deployment

- **Platform:** Streamlit Cloud / Render (via Procfile)
- **Build:** nixpacks with ffmpeg system dependency (`packages.txt`)
- **Process:** `patch_meta.py` runs first (SEO injection), then Streamlit starts

## Paddle Price IDs

| Plan | Period | Price ID |
|------|--------|----------|
| Basic | Monthly | `pri_01knn7r684skwj2z54htyseaj2` |
| Pro | Monthly | `pri_01knpry35zcjv6wqxsyjzdma9j` |
| Basic | Yearly | `pri_01knn7hhdez2seb412f4t34g2c` |
| Pro | Yearly | `pri_01knn7w9ppn9csr86fz0sq47zh` |
