# AeroCPI: Real-Time Airfare Price Index for India (Milestone 1)

**Tagline:** Measure. Explain. Verify.  
**SIH Problem Statement:** SIH26056 — Real-time Airfare Price Index for India for CPI Augmentation  
**System Nature:** Experimental prototype airfare price measurement platform intended to augment Consumer Price Index (CPI) airfare measurement.  

---

## Milestone 1 Goal

"AeroCPI can create, validate, persist and retrieve normalized airfare observations and their associated virtual-trip specifications."

---

## Repository Structure

```
AeroCPI/
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/                      # Architectural specifications
├── data/
│   ├── raw/
│   ├── processed/
│   ├── official/
│   └── demo/
├── scripts/
│   └── seed_demo_data.py      # Seed demo observations script
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── api/v1/endpoints/  # REST endpoints
│   │   ├── config/            # Settings management
│   │   ├── db/                # Base & Session setup
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic schemas & validators
│   │   ├── services/          # Domain services (Normalization, Quality, Observation)
│   │   └── main.py            # FastAPI entry point
│   └── tests/                 # Pytest suite
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/                   # React + TypeScript minimal shell
```

---

## Developer Setup Instructions

### 1. Backend Setup & Virtual Environment

```bash
cd backend
python -m venv .venv

# On Windows PowerShell
.\.venv\Scripts\activate

# On Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Running Database Migrations (Alembic)

```bash
cd backend
alembic upgrade head
```

### 3. Running Backend Tests (Pytest)

```bash
cd backend
python -m pytest tests -v
```

### 4. Seeding Demo Dataset

```bash
# From project root
python scripts/seed_demo_data.py
```

### 5. Starting Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
API Documentation available at `http://localhost:8000/docs`.

### 6. Starting Frontend Shell

```bash
cd frontend
npm install
npm run dev
```
Frontend application loads at `http://localhost:3000`.

---

## Verification Commands Summary

- **Backend Health Check:** `curl http://localhost:8000/api/v1/health`
- **List Observations:** `curl http://localhost:8000/api/v1/observations`
- **Filter Observations:** `curl "http://localhost:8000/api/v1/observations?route_id=DEL-BOM&booking_horizon_days=15"`
- **List Routes:** `curl http://localhost:8000/api/v1/routes`
