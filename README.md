# Tender Agent

Tender Agent is an end-to-end MVP that scrapes GeM tenders, analyzes them with LLM + embeddings, builds company profiles, and surfaces matched tenders with action workflows.

## Stack

- Backend: FastAPI, Motor/MongoDB, Playwright, PyMuPDF, python-docx, python-pptx
- Frontend: React + Vite + TypeScript + Tailwind + React Query
- Matching: Hybrid (embedding similarity + metadata overlap + interest-tag boost)
- Realtime: WebSocket `/ws` for job progress

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker + Docker Compose

## Quick Start

1. Backend env
```bash
copy .env.example .env
```

2. Frontend env
```bash
copy frontend\.env.example frontend\.env
```

3. Install backend deps + Playwright
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

4. Start MongoDB + backend (docker)
```bash
docker-compose up --build
```

5. Seed demo data (optional but recommended)
```bash
python scripts/seed_demo.py
```

6. Start frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`  
Backend: `http://localhost:8000`

## Dev Login

- Use email + password auth from the `/auth` page.
- Password must be at least 8 characters and include at least one letter and one number.
- Legacy OTP endpoints remain available (`/auth/email/start`, `/auth/email/verify`) for backward compatibility.

## Main Routes (Frontend)

- `/auth`
- `/onboarding/company`
- `/onboarding/documents`
- `/onboarding/interests`
- `/loading/company-processing`
- `/dashboard`
- `/tenders`
- `/tenders/:id`
- `/my-list`
- `/organization`
- `/help`

## Main API Endpoints (Backend)

Auth
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/signin`
- `POST /api/v1/auth/email/start`
- `POST /api/v1/auth/email/verify`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`

Companies / Onboarding
- `POST /api/v1/companies`
- `POST /api/v1/companies/{company_id}/scrape-website`
- `POST /api/v1/companies/{company_id}/documents`
- `DELETE /api/v1/companies/{company_id}/documents/{file_hash}`
- `POST /api/v1/companies/{company_id}/interests`
- `POST /api/v1/companies/{company_id}/process`
- `GET /api/v1/companies/{company_id}`
- `GET /api/v1/companies/{company_id}/matches`
- `GET /api/v1/companies/{company_id}/my-list`

Tenders
- `GET /api/v1/tenders`
- `GET /api/v1/tenders/{tender_id}`
- `GET /api/v1/tenders/{tender_id}/download`
- `POST /api/v1/tenders/{tender_id}/action`
- `GET /api/v1/tenders/{tender_id}/ai/suggestions`
- `POST /api/v1/tenders/{tender_id}/ai/chat`
- `POST /api/v1/tenders/{tender_id}/share`

Dashboard / Jobs
- `GET /api/v1/dashboard/stats`
- `GET /api/v1/dashboard/report`
- `POST /api/v1/jobs/scrape/trigger`
- `POST /api/v1/jobs/process/trigger`
- `WS /ws`

## Manual Scrape Trigger (CLI)

```bash
python scripts/run_scraper.py --max-pages 2 --max-bids 20
```

## Tests

```bash
pytest -q
```

## Notes

- APScheduler is disabled by default (`ENABLE_SCHEDULER=false`) for MVP manual-trigger behavior.
- If email credentials are missing, share-email runs in mock mode and still logs share events.
