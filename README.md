# Tender Agent — AI Tender Matching Platform

Tender Agent is a web application that automatically finds **government tenders** (public contracts published on India's [GeM — Government e-Marketplace](https://gem.gov.in/)) and matches them to your company using Artificial Intelligence.

Instead of a business owner manually reading through hundreds of tender notices to find the few that are actually relevant, Tender Agent does the reading for you: it collects the tenders, understands what your company does, and then shows you a ranked shortlist of the opportunities that best fit your business — along with an explanation of *why* each one matches.

> **In one sentence:** upload your company details once, and the app keeps showing you the government tenders you're most likely to win.

---

## Table of Contents

1. [Who is this for?](#who-is-this-for)
2. [How it works (in plain English)](#how-it-works-in-plain-english)
3. [Key features](#key-features)
4. [The technology behind it](#the-technology-behind-it)
5. [How the pieces fit together](#how-the-pieces-fit-together)
6. [Before you start (prerequisites)](#before-you-start-prerequisites)
7. [Step-by-step setup](#step-by-step-setup)
8. [Configuration explained](#configuration-explained)
9. [Using the app (a walkthrough)](#using-the-app-a-walkthrough)
10. [The admin panel](#the-admin-panel)
11. [Helper scripts](#helper-scripts)
12. [API reference (for developers)](#api-reference-for-developers)
13. [Running the tests](#running-the-tests)
14. [Troubleshooting](#troubleshooting)
15. [Frequently asked questions](#frequently-asked-questions)

---

## Who is this for?

- **Business owners / bid managers** who want to stop hunting for tenders manually.
- **Sales teams** who need a filtered, prioritized list of opportunities every day.
- **Developers** who want to run, extend, or deploy the platform.

You do **not** need to be technical to *use* the finished app — you just log in through a website. The technical sections below are only needed to *set up and run* the app on a computer or server.

---

## How it works (in plain English)

Think of Tender Agent as a tireless assistant that repeats four steps:

1. **Collect** — It visits the GeM website and gathers newly published tenders, downloading each tender's PDF documents.
2. **Understand** — It reads each tender using AI and pulls out the important facts: what is being bought, quantities, deadlines, eligibility rules, location, estimated value, and so on. It does the same for **your** company — reading your uploaded brochures and your website to build a "profile" of what you offer.
3. **Match** — It compares your company profile against every tender and scores how well they fit. The score blends three signals:
   - **Meaning similarity** — does the tender's subject actually relate to what your company does? (Uses AI "embeddings" — see the glossary at the bottom.)
   - **Metadata overlap** — do concrete fields like category, location, and industry line up?
   - **Interest boost** — extra points for the specific topics/tags you told the app you care about.
4. **Act** — It shows you the best matches in a clean dashboard. For each tender you can read AI-generated summaries and suggestions, chat with an AI about the tender, save it to your list, mark it as *Applied* or *Discarded*, download its documents, or share it with a colleague by email.

All of this happens continuously (or on demand), so your shortlist stays fresh.

---

## Key features

**For companies / end users**
- 🔎 **Automatic tender discovery** from the GeM marketplace.
- 🧠 **AI-powered matching** with a plain-language explanation of *why* each tender matched.
- 🏢 **Guided onboarding** — enter your company details, upload documents (PDF/DOCX/PPTX), and optionally let the app scrape your company website to enrich your profile.
- 🏷️ **Interest tags** — tell the app the topics you care about to fine-tune matches.
- 💬 **Discuss with AI** — ask questions about any tender and get answers grounded in its documents.
- ✨ **AI suggestions** — quick summaries and next-step recommendations per tender.
- 📌 **My List / actions** — save tenders and track them as *Saved*, *Applied*, or *Discarded*.
- 📨 **Share by email** — send a tender to a teammate.
- 📥 **Document download** — grab the original tender PDFs.
- 📊 **Dashboard** — stats, recent activity, and a live processing queue.
- ⏱️ **Real-time progress** — a live connection (WebSocket) shows background jobs as they run.
- 👤 **Account management** — edit your profile, change your password, set notification preferences, or delete your account.

**For administrators**
- 🛠️ **Admin panel** — view platform statistics, manage users (search, view details, activate/deactivate, delete), and see applied-vs-discarded trends over time.

---

## The technology behind it

You don't need to understand these to use the app, but here's what powers it:

| Layer | Technology | What it does |
|-------|-----------|--------------|
| **Backend (server)** | Python + [FastAPI](https://fastapi.tiangolo.com/) | The "brain" — handles requests, runs the AI, talks to the database. |
| **Database** | [MongoDB](https://www.mongodb.com/) (via Motor) | Stores companies, tenders, users, and matches. |
| **Web scraping** | [Playwright](https://playwright.dev/) + BeautifulSoup | Browses GeM and company websites like a real browser to collect data. |
| **Document reading** | PyMuPDF, python-docx, python-pptx | Extracts text from PDF, Word, and PowerPoint files. |
| **AI language model (LLM)** | [Ollama](https://ollama.com/) (default) or Google **Gemini** | Reads tenders/profiles and powers the chat and suggestions. |
| **AI embeddings** | `sentence-transformers` (`BAAI/bge-small-en-v1.5`) | Turns text into numbers so the app can measure "meaning similarity". |
| **Frontend (website)** | React + Vite + TypeScript + Tailwind CSS | The user interface you see and click. |
| **Auth** | Central **auth gateway** (JWT / RS256) | Secure login shared across NerveSparks products. |
| **Scheduling** | APScheduler | Optionally runs collection/processing jobs automatically on a timer. |
| **Real-time** | WebSocket (`/ws`) | Pushes live job progress to the browser. |

---

## How the pieces fit together

```
                          ┌─────────────────────────────┐
                          │        GeM Marketplace        │
                          │  (public government tenders)  │
                          └───────────────┬───────────────┘
                                          │  scrape + download PDFs
                                          ▼
┌──────────────┐   HTTP/WebSocket   ┌───────────────────────────────┐   ┌──────────────┐
│   Frontend    │◄──────────────────►│        Backend (FastAPI)       │◄──►│   MongoDB     │
│ React website │                    │  • scraper   • AI matching     │   │  (database)   │
│ (what users   │                    │  • doc reader• jobs/scheduler  │   └──────────────┘
│   see)        │                    │  • REST API  • WebSocket        │
└──────────────┘                    └───────────────┬───────────────┘
                                                     │  reads/writes text
                                          ┌──────────┴──────────┐
                                          ▼                     ▼
                                   ┌─────────────┐      ┌─────────────────┐
                                   │  LLM (Ollama │      │  Embedding model │
                                   │  or Gemini)  │      │  (similarity)    │
                                   └─────────────┘      └─────────────────┘
```

> **Note:** When the frontend is "built" for production, the backend can serve the website directly (see [`app/main.py`](app/main.py)). During development you usually run the frontend and backend separately.

---

## Before you start (prerequisites)

Install these on your computer first:

- **Python 3.11 or newer** — the backend language. ([Download](https://www.python.org/downloads/))
- **Node.js 18 or newer** — needed to build the website. ([Download](https://nodejs.org/))
- **Docker + Docker Compose** — the easiest way to run MongoDB and the backend together. ([Download](https://www.docker.com/products/docker-desktop/))
- *(Optional)* An **AI model provider**:
  - **Ollama** running locally or on a server (default), **or**
  - A **Google Gemini API key** if you prefer Gemini.

If you only want to try the app with sample data, you can skip the AI provider at first and use the demo seed script.

---

## Step-by-step setup

The commands below use **Windows PowerShell** (the platform this project targets). On Mac/Linux, replace `copy` with `cp` and `\` with `/`.

### 1. Create the backend configuration file
This copies the example settings into a real settings file you can edit.
```powershell
copy .env.example .env
```
Before starting the backend, edit `.env` and set `JWT_SECRET` to a unique random value with at least 32 characters.

### 2. Create the frontend configuration file
```powershell
copy frontend\.env.example frontend\.env
```

### 3. Set up the backend (Python)
```powershell
python -m venv .venv           # create an isolated Python environment
.venv\Scripts\activate         # turn it on
pip install -r requirements.txt  # install all Python libraries
playwright install chromium    # install the browser used for scraping
```

### 4. Start the database + backend with Docker
This launches MongoDB and the backend server together.
```powershell
docker-compose up --build
```
The backend will be available at **http://localhost:8000**.

### 5. (Recommended) Load sample data
So you have something to look at immediately, without waiting for a real scrape.
```powershell
python scripts/seed_demo.py
```

### 6. Start the frontend website
Open a **new** terminal:
```powershell
cd frontend
npm install     # install website libraries (first time only)
npm run dev     # start the website
```

### 7. Open the app
- **Website (frontend):** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Interactive API docs:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

---

## Configuration explained

All backend settings live in the `.env` file. You usually only need to touch a few of them. The full list and defaults are defined in [`app/config.py`](app/config.py).

**The settings you're most likely to change:**

| Setting | What it means | Default |
|---------|---------------|---------|
| `MONGO_URI` | Where the database lives | `mongodb://localhost:27017` |
| `DB_NAME` | The database name | `tender_db` |
| `LLM_PROVIDER` | Which AI to use: `ollama` or `gemini` | `ollama` |
| `LLM_BASE_URL` | Address of your Ollama server, required when `LLM_PROVIDER=ollama` | *(set in `.env`; example `http://localhost:11434`)* |
| `LLM_MODEL` | The Ollama model name | `gpt-oss:latest` |
| `GEMINI_API_KEY` | Your Google Gemini key (only if using Gemini) | *(empty)* |
| `GEMINI_MODEL` | The Gemini model to use | `gemini-1.5-flash` |
| `EMBEDDING_MODEL` | Model used for similarity scoring | `BAAI/bge-small-en-v1.5` |
| `ENABLE_SCHEDULER` | Run collection/processing automatically on a timer | `false` |
| `SCRAPE_MAX_PAGES` / `SCRAPE_MAX_BIDS` | How much to scrape per run | `10` / `200` |
| `ADMIN_API_KEY` | Secret key that protects admin endpoints | `tender-admin-secret` |

**Login / security (central auth gateway):**

| Setting | Purpose |
|---------|---------|
| `AUTH_GATEWAY_BASE_URL` | The shared login service (`https://auth.nervesparks.com`) |
| `AUTH_GATEWAY_PREFIX` | The path prefix for the gateway |
| `AUTH_JWKS_URL` | Where the app fetches keys to verify login tokens |
| `JWT_SECRET` | Required secret for local tokens; must be a unique random value with at least 32 characters |

**Email (for the "share tender" feature):**

| Setting | Purpose |
|---------|---------|
| `EMAIL_PROVIDER`, `EMAIL_FROM`, `SMTP_*`, `SENDGRID_API_KEY` | Email delivery settings. If these are left empty, sharing runs in **mock mode** — it logs the share event but doesn't actually send an email. |

> ⚠️ **Security reminder:** Before deploying to a real server, set `JWT_SECRET` and `ADMIN_API_KEY` to strong, unique values, rotate any tokens issued with old secrets, and never commit real secrets or service-account files to version control.

---

## Using the app (a walkthrough)

1. **Sign in** at `/auth` using your email and password.
   - Passwords must be **at least 8 characters** and include **at least one letter and one number**.
2. **Onboard your company** (a short guided flow):
   - `/onboarding/company` — enter your company name, website, and details.
   - `/onboarding/documents` — upload brochures, capability statements, or past bids (PDF/DOCX/PPTX).
   - `/onboarding/interests` — pick the tender topics you care about.
3. **Wait while the app builds your profile** — a loading screen (`/loading/company-processing`) shows progress in real time while the AI reads your documents and website.
4. **Explore your dashboard** (`/dashboard`) — see stats, recent activity, and the processing queue.
5. **Browse tenders** (`/tenders`) — filter and sort the matched tenders. Open any tender (`/tenders/:id`) to:
   - Read AI summaries and suggestions,
   - **Discuss with AI** about the tender,
   - **Download** its documents,
   - **Save**, mark **Applied**, or **Discard** it,
   - **Share** it by email.
6. **Manage your shortlist** (`/my-list`) — everything you've saved.
7. **Organization & profile** (`/organization`, `/profile`) — manage your company info, personal profile, password, and notification preferences.
8. **Help** (`/help`) — in-app guidance.

---

## The admin panel

Administrators have a separate area for managing the platform:

- **Admin login:** `/admin/login`
- **Admin dashboard:** `/admin/dashboard` — total users, active users, applied/discarded tender counts, and trend charts over 7 days, 10 days, 6 months, or 12 months.
- **Manage users:** `/admin/users` — search users, view a user's details and tender activity, activate/deactivate accounts, and delete users.

Admin access is granted to users whose login token carries an `admin` role (synced into MongoDB as `is_admin`). Admin API calls also require the secret `ADMIN_API_KEY` to be sent in an `X-Admin-Key` header.

---

## Helper scripts

Located in the [`scripts/`](scripts/) folder:

| Script | What it does |
|--------|--------------|
| `python scripts/seed_demo.py` | Loads sample companies and tenders so you can try the app immediately. |
| `python scripts/init_db.py` | Sets up the database indexes (usually done automatically on startup). |
| `python scripts/run_scraper.py --max-pages 2 --max-bids 20` | Manually run the GeM scraper. Adjust the numbers to control how much it collects. |
| `python scripts/set_admin_claim.py` | **Disabled** — leftover from the old Firebase login system. Admin rights now come from the auth gateway. |

---

## API reference (for developers)

All API endpoints are prefixed with `/api/v1` (except the WebSocket and health check). Full interactive documentation is auto-generated at **http://localhost:8000/docs**.

### Authentication & account
- `POST /api/v1/auth/login` — log in via the central auth gateway (returns tokens + user)
- `POST /api/v1/auth/refresh` — refresh an expired session
- `POST /api/v1/auth/signup` — create a local account
- `POST /api/v1/auth/signin` — sign in with a local account
- `POST /api/v1/auth/email/start` · `POST /api/v1/auth/email/verify` — legacy OTP flow (kept for compatibility)
- `GET  /api/v1/auth/me` — current user
- `PATCH /api/v1/auth/profile` — update profile fields
- `POST /api/v1/auth/change-password` — change password
- `PATCH /api/v1/auth/notifications` — update notification preferences
- `DELETE /api/v1/auth/account` — delete the account
- `POST /api/v1/auth/logout` — log out

### Companies & onboarding
- `GET  /api/v1/companies/` — list companies
- `POST /api/v1/companies` — create a company profile
- `GET  /api/v1/companies/{company_id}` — get a company
- `PATCH /api/v1/companies/{company_id}` — update a company
- `DELETE /api/v1/companies/{company_id}` — delete a company
- `POST /api/v1/companies/{company_id}/scrape-website` — enrich the profile from the company website
- `POST /api/v1/companies/{company_id}/documents` — upload documents
- `DELETE /api/v1/companies/{company_id}/documents/{file_hash}` — remove a document
- `POST /api/v1/companies/{company_id}/interests` — set interest tags
- `POST /api/v1/companies/{company_id}/process` — build the AI profile
- `GET  /api/v1/companies/{company_id}/matches` — matched tenders for the company
- `GET  /api/v1/companies/{company_id}/my-list` — saved tenders
- `GET  /api/v1/companies/{company_id}/search-history` — past searches
- `POST /api/v1/companies/upload` — legacy single-step profile upload

### Tenders
- `GET  /api/v1/tenders/` — list tenders (with filters)
- `GET  /api/v1/tenders/stats/summary` — tender statistics
- `GET  /api/v1/tenders/{tender_id}` — tender details
- `GET  /api/v1/tenders/{tender_id}/download` — download the tender document
- `POST /api/v1/tenders/{tender_id}/reprocess` — re-run AI extraction on a tender
- `GET  /api/v1/tenders/{tender_id}/matches` — companies matching this tender
- `POST /api/v1/tenders/{tender_id}/action` — save / apply / discard
- `GET  /api/v1/tenders/{tender_id}/ai/suggestions` — AI summary & suggestions
- `POST /api/v1/tenders/{tender_id}/ai/chat` — chat about the tender
- `POST /api/v1/tenders/{tender_id}/share` — share by email

### Search
- `GET  /api/v1/search/tenders/{company_id}` — search/match tenders for a company

### Dashboard
- `GET  /api/v1/dashboard/stats` — headline numbers
- `GET  /api/v1/dashboard/report` — a fuller report
- `GET  /api/v1/dashboard/activity` — recent activity
- `GET  /api/v1/dashboard/queue` — the live processing queue

### Jobs (background work)
- `GET  /api/v1/jobs/` — list jobs
- `GET  /api/v1/jobs/{job_id}` — job details
- `POST /api/v1/jobs/scrape/trigger` — start a scrape now
- `POST /api/v1/jobs/process/trigger` — start processing now
- `GET  /api/v1/jobs/scheduler/status` — is the automatic scheduler running?

### Admin (require `X-Admin-Key` + admin user)
- `GET    /api/v1/admin/stats` — platform stats
- `GET    /api/v1/admin/tender-stats?period=7d|10d|6m|12m` — trend data
- `GET    /api/v1/admin/users` — list/search users
- `GET    /api/v1/admin/users/{user_id}` — user detail
- `PUT    /api/v1/admin/users/{user_id}/inactivate` — toggle active status
- `DELETE /api/v1/admin/users/{user_id}` — delete a user

### Other
- `WS  /ws` — real-time job progress
- `GET /health` — health check (returns `{"status": "ok"}`)

---

## Running the tests

```powershell
pytest -q
```

---

## Troubleshooting

**The app can't connect to the database.**
Make sure MongoDB is running (via `docker-compose up`) and `MONGO_URI` in `.env` points to it. Inside Docker the URI is `mongodb://mongodb:27017`; running locally it's `mongodb://localhost:27017`.

**AI features (matching, chat, summaries) don't work.**
Check `LLM_PROVIDER`. If it's `ollama`, confirm your Ollama server is reachable at `LLM_BASE_URL` and the `LLM_MODEL` is installed. If it's `gemini`, confirm `GEMINI_API_KEY` is set.

**Scraping fails or hangs.**
Run `playwright install chromium` again. Reduce `SCRAPE_MAX_PAGES`/`SCRAPE_MAX_BIDS`. The GeM site may be slow or rate-limiting — the app already adds polite delays (`SCRAPE_MIN_DELAY`/`SCRAPE_MAX_DELAY`).

**Sharing a tender doesn't send an email.**
If SMTP/SendGrid settings are empty, sharing runs in **mock mode** — it logs the event but sends nothing. Fill in the email settings to enable real delivery.

**"Nothing shows up on the dashboard."**
Run `python scripts/seed_demo.py` to load sample data, or trigger a scrape via `POST /api/v1/jobs/scrape/trigger` (or the Jobs page in the UI).

**Login problems.**
Passwords need at least 8 characters with at least one letter and one number. The app relies on the central auth gateway; make sure `AUTH_GATEWAY_BASE_URL` / `AUTH_JWKS_URL` are reachable.

---

## Frequently asked questions

**Do I need to be technical to use Tender Agent?**
No. Using the app is just visiting a website and clicking through it. The technical steps in this file are only for setting it up.

**Where do the tenders come from?**
From India's public **GeM (Government e-Marketplace)**. The app reads publicly listed tenders.

**Does the AI decide which tenders I win?**
No — it *ranks* and *explains* opportunities so you spend your time on the best-fit ones. You always make the final decision to apply.

**Is my company data sent anywhere?**
Your documents and profile are processed by the AI provider you configure (a local Ollama server keeps everything on your own infrastructure; Gemini sends text to Google). Choose the provider that matches your privacy needs.

**Can it run automatically without me clicking anything?**
Yes. Set `ENABLE_SCHEDULER=true` and the app will scrape and process on a timer (`SCRAPE_INTERVAL_HOURS`, `PROCESS_INTERVAL_MINUTES`). It's off by default so you stay in control.

---

## Glossary

- **Tender / bid** — a public request from a government body to buy goods or services; companies compete to win it.
- **Scraping** — automatically reading a website to collect its information.
- **LLM (Large Language Model)** — the AI that reads and understands text (e.g., Ollama, Gemini).
- **Embedding** — a way of turning text into numbers so a computer can measure how similar two pieces of text are in *meaning*, not just wording.
- **WebSocket** — a live, always-open connection that lets the server push updates (like job progress) to your browser instantly.
- **JWT** — a secure digital "pass" that proves you're logged in.
- **MongoDB** — the database where all the app's data is stored.

---

### Notes for maintainers
- The automatic scheduler (APScheduler) is **disabled by default** (`ENABLE_SCHEDULER=false`) for manual-trigger, MVP-style operation.
- The project **migrated from Firebase authentication to the central auth gateway**. Firebase-related files/scripts (e.g. `set_admin_claim.py`, `firebase-service-account.json`) are legacy and no longer used for auth.
- When a production frontend build exists in `frontend/dist`, the backend serves it directly and handles single-page-app routing (see [`app/main.py`](app/main.py)).
