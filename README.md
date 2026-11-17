# logisistance-api

FastAPI backend for **logisistance** — a logistics assistant for independent road freight
carriers in the European Union.

The web client lives in a separate repository:
[`logisistance-web`](https://github.com/deniskoliban/logisistance-web) (Angular).

**Status:** v0.1 — accounts, driver profiles and vehicle profiles. Freight exchange adapters,
route planning and backhaul matching are next.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2 · SQLite (PostgreSQL-ready) · JWT (HS256) · Argon2 · pytest

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1                 # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

- API docs: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/health>

Tables are created from the SQLAlchemy models at startup (no migrations yet — Alembic lands
before the first real deploy). Copy `.env.example` to `.env` to override the database URL, JWT
secret or CORS origins; the defaults work for local development.

The web client is expected at <http://localhost:4200>, which is already in `CORS_ORIGINS`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest        # 26 tests
```

## Endpoints

All under `/api/v1`.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/register` | — | Create account, returns JWT + profile |
| POST | `/auth/login` | — | Sign in, returns JWT + profile |
| GET | `/users/me` | Bearer | Current profile |
| PATCH | `/users/me` | Bearer | Update name / age / country / city |
| GET | `/vehicles` | Bearer | List own vehicles |
| POST | `/vehicles` | Bearer | Add a vehicle |
| GET | `/vehicles/{id}` | Bearer | Read one own vehicle |
| PATCH | `/vehicles/{id}` | Bearer | Partially update a vehicle |
| DELETE | `/vehicles/{id}` | Bearer | Remove a vehicle |
| GET | `/reference/countries` | — | Selectable EU/EEA/CH country codes |
| GET | `/reference/vehicle-options` | — | Vehicle type / body type options |

## Layout

```
app/
├── api/
│   ├── deps.py          # auth dependency, DB session
│   ├── router.py
│   └── routes/          # auth, users, vehicles, reference
├── core/
│   ├── config.py        # settings from env / .env
│   ├── reference.py     # EU country codes, normalisation helpers
│   └── security.py      # Argon2 hashing, JWT encode/decode
├── db/
│   ├── base.py          # declarative base + timestamp mixin
│   └── session.py       # engine, SessionLocal, get_db
├── models/              # User, Vehicle
├── schemas/             # Pydantic request/response models
└── main.py              # app factory, CORS, lifespan
tests/                   # pytest suite
docs/PROJECT_SPEC.md     # product brief and decisions
```

## Behaviour worth knowing

- Login returns the same error for unknown email and wrong password — no account enumeration.
- Another driver's vehicle answers `404`, not `403`.
- Drivers are stored with a `date_of_birth`; `age` is derived on every response, so it can never go
  stale. The rules (18–100, no future dates) live in `app/core/dates.py`.
- MVP assumes a self-employed carrier (sole proprietor), so a driver has one country: `country` is the
  country of residence and doubles as the default starting point for load search. A company mode with
  several drivers and vehicles is planned; `company_country` will come back with it.
- The country must be an EU/EEA/CH code.
- The API also serves the country list the UI picks from.
- Plates are normalised to upper case and unique per owner.

## Schema changes

There are no migrations yet: tables come from the SQLAlchemy models at startup and existing SQLite
files are **not** altered. After changing a model, delete `app.db` (or point `DATABASE_URL`
elsewhere) and restart. Alembic is the planned fix before the first real deploy.

## Roadmap

| Feature | State |
| --- | --- |
| Vehicle registration and management | ✅ v0.1 |
| Registration, driver profile | ✅ v0.1 |
| Freight exchange adapters (mock provider first) | next |
| Intelligent freight search and filtering | next |
| Route planning, driving time, ETA | later |
| Return cargo / backhaul search | later |
