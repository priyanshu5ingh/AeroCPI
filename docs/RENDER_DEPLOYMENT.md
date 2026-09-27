# AeroCPI Render Deployment Preparation

The AeroCPI core engineering baseline is frozen. This document describes the exact steps to deploy this repository to Render (or a similar PaaS), migrating away from local SQLite/filesystem assumptions to a fully cloud-native PostgreSQL and object-storage architecture.

## 1. Target Architecture Overview

- **Frontend**: Render Static Site (React/Vite).
- **Backend API**: Render Web Service (FastAPI + Uvicorn).
- **Database**: Render PostgreSQL.
- **Collection Cron**: Render Cron Job.
- **Artifact/Capture Storage**: External Object Storage (e.g., AWS S3, Cloudflare R2). Render web service disks are ephemeral and reset on deploy; raw HTML captures and generated ML models must be pushed to an S3-compatible API.

---

## 2. Environment Variables (Required for Production)

Configure the following variables in the Render Dashboard (Environment tab):

| Variable | Description |
|---|---|
| `DATABASE_URL` | Render internal PostgreSQL connection string (e.g., `postgresql://user:pass@host/db`). |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend domains. e.g., `https://aerocpi-frontend.onrender.com`. |
| `VITE_API_BASE_URL` | (Frontend Only) The public URL of the backend web service. e.g., `https://aerocpi-api.onrender.com/api/v1`. |
| `DUFFEL_API_TOKEN` | Access token for the Duffel source adapter. |
| `S3_BUCKET_NAME` | (Placeholder) Target bucket for durable storage. |
| `AWS_ACCESS_KEY_ID` | (Placeholder) Object storage credentials. |
| `AWS_SECRET_ACCESS_KEY` | (Placeholder) Object storage credentials. |

*No secrets should be committed to `render.yaml` or version control.*

---

## 3. Database & Data Migration

AeroCPI natively supports PostgreSQL via SQLAlchemy.
1. Create a Render PostgreSQL database.
2. Link it to the Backend Web Service via `DATABASE_URL`.
3. The backend relies on Alembic for schema creation. 
   - Before starting, run `alembic upgrade head`.

**SQLite to PostgreSQL Migration Script:**
A migration script has been prepared to safely move existing `aerocpi_dev.db` production measurements into PostgreSQL while strictly dropping synthetic data.

```bash
# Run locally before switching fully to the cloud DB
export PYTHONPATH=$(pwd)/backend
python backend/scripts/migrate_sqlite_to_postgres.py --sqlite sqlite:///aerocpi_dev.db --postgres <RENDER_EXTERNAL_DB_URL>
```
*Note: Run this against the external database URL provided by Render.*

---

## 4. Backend Web Service

- **Build Command**: `pip install -r requirements.txt && cd backend && alembic upgrade head`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/api/v1/health`

*Note: The backend has been modified to disable `Base.metadata.create_all()` in production, relying solely on Alembic.*

---

## 5. Frontend Static Site

- **Root Directory**: `frontend`
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `dist`
- **Routing Rules**: Ensure all SPA routes redirect to `index.html`. On Render Static Sites, set a Redirect/Rewrite rule:
  - Source: `/*`
  - Destination: `/index.html`
  - Status: `200`

---

## 6. Scheduled Collection (Cron Job)

The local Windows Task Scheduler cannot be used in production. Create a Render Cron Job linked to the backend repository.

- **Environment**: Same as Backend Web Service (must have `DATABASE_URL`).
- **Command**: `cd backend && python scripts/run_daily_collection.py`
- **Schedule**: `0 2 * * *` (UTC equivalent of 02:00 AM daily, which is 07:30 IST).

The script uses a lock file to prevent overlapping runs and explicitly writes structured logs to stdout, which Render Cron will capture.

---

## 7. Artifact Persistence (Action Required)

**Filesystem Persistence Findings:**
The application currently writes to the local filesystem in several places:
- `data/raw/captures/*.html.gz` (Raw HTML source evidence)
- `data/models/*.json` (ML Model Artifacts and Forecast Manifests)

**Blocker / Requirement:**
Because Render Cron Jobs and Web Services have ephemeral storage, these files will be lost across deployments or container restarts. 
Before public deployment, you must implement an S3 (or similar) storage backend abstraction for the `DataCaptureService` and `ModelTrainingService`. Do not assume local disk persistence.

---

## 8. Render Blueprint (`render.yaml`)

A blueprint has been added to the root of the repository to automate infrastructure as code. It defines the API, Frontend, PostgreSQL, and Cron Job natively.

---

## 9. Rollback & Troubleshooting

- If a deployment fails, use the Render dashboard to rollback to the previous successful deploy.
- Check the `GET /api/v1/health` endpoint to verify DB connectivity.
- Verify CORS errors in the browser console. If blocked, ensure `CORS_ORIGINS` exactly matches the frontend URL without a trailing slash.
