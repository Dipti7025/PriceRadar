# PriceRadar — Full-Stack Price Surveillance & Analytics

PriceRadar is an automated price-tracking, history visualization, and target-price alert platform.

---

## Architecture Overview

```
PriceRadar/
├── .env                  # Environment variables & PostgreSQL credentials
├── .env.example          # Template configuration
├── README.md             # Setup guide and Windows instructions
├── backend/              # FastAPI Application
│   ├── alembic/          # Database migrations (PostgreSQL strictly)
│   │   └── versions/     # 0001_initial_schema.py
│   ├── app/
│   │   ├── api/v1/       # Endpoints (Health, Products, Alerts, Jobs)
│   │   ├── core/         # Config, Database engine, and SSRF Guard
│   │   ├── models/       # SQLAlchemy 2.x Declarative Models
│   │   ├── schemas/      # Pydantic v2 validation models
│   │   └── main.py       # FastAPI application & lifespan
│   ├── tests/            # Test suite (Health, SSRF, Schemas)
│   └── requirements.txt  # Python backend dependencies
├── worker/               # Background ETL & Extraction Worker
│   ├── extractor.py      # Safe HTTP scraping & JSON-LD parser
│   ├── playwright_scraper.py # Headless browser automation (SPAs)
│   ├── tasks.py          # ETL pipeline & alert triggers
│   └── main.py           # Worker polling daemon
└── frontend/             # React + Vite + TypeScript + Tailwind CSS
    ├── src/
    │   ├── components/   # Dashboard, Navbar, Alerts, URL Form
    │   ├── services/     # API Client & Client-side SSRF Pre-check
    │   └── App.tsx       # Main dashboard layout
    └── package.json
```

---

## Security & Reliability Design

- **PostgreSQL Strictly**: PriceRadar explicitly disallows SQLite to prevent race conditions and data corruption across concurrent scraping workers.
- **SSRF Guard**: All user-submitted URLs pass through strict Server-Side Request Forgery verification. Hostnames resolving to private subnets (RFC 1918), loopback (`127.0.0.1`, `::1`), link-local/cloud metadata (`169.254.169.254`), or non-web ports are immediately rejected.
- **Website Restrictions**: Checks and respects `robots.txt` before fetching pages. Never bypasses access controls.

---

## Quick Windows Setup Guide

### 1. PostgreSQL Database Setup

PostgreSQL server is **required** locally on port 5432.

#### Check if PostgreSQL service is installed:
In Windows PowerShell (Run as Administrator):
```powershell
Get-Service *postgres*
```

#### If PostgreSQL is not installed:
1. Download the official Windows installer from: [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)
2. Run the installer and note your superuser password (default used in `.env` is `postgres`).
3. Ensure the service is started:
```powershell
Start-Service postgresql*
```

#### Create the `priceradar` database:
Using Command Prompt or PowerShell:
```cmd
createdb -U postgres priceradar
```
*(Or via `psql -U postgres -c "CREATE DATABASE priceradar;"`)*

---

### 2. Backend Setup & Database Migrations

From the root project directory:

```cmd
:: Create and activate Python virtual environment
python -m venv .venv
.venv\Scripts\activate

:: Install backend dependencies
cd backend
pip install -r requirements.txt

:: Run Alembic migrations against PostgreSQL
alembic upgrade head

:: Start the FastAPI Backend server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be live at `http://127.0.0.1:8000`.
- Health status: `http://127.0.0.1:8000/health`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`

---

### 3. Frontend Setup & Startup

In a new terminal window:

```cmd
cd frontend

:: Install Node dependencies
npm install

:: Start Vite dev server
npm run dev
```

The frontend dashboard will be live at `http://localhost:5173`.

---

### 4. Background Worker Setup (Extraction Pipeline)

In a third terminal window:

```cmd
:: Activate virtual environment
.venv\Scripts\activate

:: Install worker dependencies & Playwright browser binaries
cd worker
pip install -r requirements.txt
playwright install chromium

:: Start background worker
python -m worker.main
```

---

### 5. Running Automated Checks and Tests

From the backend directory:

```cmd
cd backend
pytest -v
```

This validates:
- System and Database Health endpoint structure (`tests/test_health.py`)
- Complete SSRF protection matrix against private IPs, loopbacks, cloud metadata, and unsafe schemes (`tests/test_ssrf.py`)
- Pydantic schema validation (`tests/test_schemas.py`)
