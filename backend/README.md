# Backend — FastAPI service

> This is the original backend from `yeahhthaarthh/edusphere-backend` (commit `9607a80`), preserved as received. An accurate, reviewed version of this document is included as [`README.corrected.md`](README.corrected.md). A full engineering review is in [`../docs/CODE_REVIEW.md`](../docs/CODE_REVIEW.md).

## What it actually is

| Concern | Implementation |
| --- | --- |
| Framework | FastAPI + Uvicorn, interactive docs at `/docs` |
| Database | **PostgreSQL** via `psycopg` 3 (`DATABASE_URL`) — *not* SQLite |
| File storage | **Supabase Storage** bucket (public URLs / 302 redirects) — *not* local disk |
| Auth | `admins` + `sessions` tables, `scrypt` password hash, SHA-256-hashed opaque token in an HttpOnly `archive_session` cookie (7-day TTL) |
| Upload limit | 50 MB, PDF validation before upload |
| Discovery | `requests` + BeautifulSoup, one module per exam |

The repository's original `README.md` describes an older SQLite / `SECRET_KEY` / `DATA_DIR` version and is kept for reference only. Use `README.corrected.md` and [`../docs/API.md`](../docs/API.md) for the current routes.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Application, 46 routes (41 under `/api`), auth, CRUD, stats, file proxy |
| `cbse_discovery.py` | CBSE question-paper discovery |
| `cbse_sample_discovery.py` | CBSE sample-paper discovery |
| `jee_main_discovery.py` | JEE Main (NTA) discovery |
| `jee_advanced_discovery.py` | JEE Advanced (jeeadv.ac.in) discovery |
| `neet_discovery.py` | NEET UG discovery |
| `requirements.txt` | Original dependency list (contains duplicates + unused `httpx`) |
| `requirements.clean.txt` | De-duplicated, corrected list — **use this one** |
| `seed_data.sql` | Original SQLite-flavoured seed (reference copy; also in `../database/`) |
| `.env.example` | All recognised environment variables |

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.clean.txt

# 1. Create the schema FIRST — init_db() does not create tables.
psql "$DATABASE_URL" -f ../database/schema.postgres.sql
# 2. Choose ONE seeding method (not both, or you will duplicate rows):
#    either let init_db() insert its 16 starter rows on an empty table,
#    or run ../database/seed_data.postgres.sql once.

export DATABASE_URL='postgresql://edusphere:edusphere@localhost:5432/edusphere'
export ADMIN_EMAIL='you@example.com'
export ADMIN_PASSWORD='a-long-random-password'
export SUPABASE_URL='https://xxxx.supabase.co'
export SUPABASE_SERVICE_ROLE_KEY='...'
export SUPABASE_BUCKET='edusphere-papers'
export COOKIE_SECURE=false          # required for local HTTP
export CORS_ORIGINS='http://localhost:8080'

uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Docs: `http://localhost:8000/docs` · Health: `GET /api/health`.

**Module name matters:** the discovery modules do `from app import connect`, so start it as `uvicorn app:app` from this folder. Importing as a package re-imports the file under a second name.

**Supabase:** create the bucket named by `SUPABASE_BUCKET` and make it public, otherwise `get_public_url()` produces links that return 401.

## Frontend integration

The frontend does **not** require this service — it ships with the catalogue bundled. If you do connect it, use the "Connect" screen in the UI, set the API base to this origin, and call `fetch(..., { credentials: "include" })` so the HttpOnly cookie is sent. With `COOKIE_SECURE=true` the frontend must be on HTTPS and its exact origin must appear in `CORS_ORIGINS`.

## Known issues (documented, not silently fixed)

- `init_db()` runs at import time and only seeds rows — there is no migration. Under multiple workers it can seed twice.
- `seed_data.sql` uses SQLite `AUTOINCREMENT`; use the Postgres files in `../database/` instead.
- Two NEET admin endpoints and the `/api/admin/stats` / `/api/admin/dashboard` aliases are not access-controlled in the original code.
- `GET /api/admin/sample-discovery-test` is registered twice.
- `?download=1` is accepted but ignored; `/api/mock-tests` exposes answers.

See [`../docs/engineering/REVIEW.md`](../docs/engineering/REVIEW.md) and the **unapplied** [`../docs/engineering/PROPOSED_PATCH.patch`](../docs/engineering/PROPOSED_PATCH.patch) for details and 21 proposed fixes. Do not expose this backend publicly without applying them.
