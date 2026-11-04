# Setup guide

Three ways to run EduSphere, from simplest to fullest.

---

## Level 0 — Just view the site (recommended for a demo)

```bash
git clone https://github.com/Akash0747/edusphere-website.git
cd edusphere-website/frontend
# double-click index.html
```

Or serve it:

```bash
python3 serve.py 8080    # → http://localhost:8080
```

No Python packages, no database, no internet connection needed. `serve.py` binds `0.0.0.0` so it also works in a container/preview environment.

---

## Level 1 — Rebuild the frontend from source

Requirements: Python 3.10+ (standard library only for the build).

```bash
cd frontend
python3 build_data.py    # regenerates src/data/archive.json from source datasets
python3 build.py         # writes a fresh, self-contained index.html
node --check src/app.js  # optional JS syntax check
```

Optional browser smoke test:

```bash
pip install playwright
python3 -m playwright install chromium
# On minimal Linux images you may also need: libnspr4 libnss3 libasound2 ...
python3 validate.py
```

`validate.py` walks home → exams → papers → filters → search → drawer → save → dashboard → quiz → connect → mobile and reports JS/console errors. It writes screenshots into `screenshots/`.

`make` shortcuts are available at the repository root: `make build`, `make data`, `make test`, `make serve`.

---

## Level 2 — Full stack (frontend + backend + database)

### 1. Configuration

```bash
cp .env.example .env
# Edit .env: DATABASE_URL, SUPABASE_*, ADMIN_*, COOKIE_SECURE=false for local HTTP
export $(grep -v '^#' .env | xargs)   # or use `set -a; source .env; set +a`
```

> Never commit `.env`. It is in `.gitignore`.

### 2. PostgreSQL

```bash
docker compose up -d db
# or: make db-up
export DATABASE_URL='postgresql://edusphere:edusphere@localhost:5432/edusphere'
psql "$DATABASE_URL" -f database/schema.postgres.sql
psql "$DATABASE_URL" -f database/seed_data.postgres.sql
```

⚠️ Choose **one** seeding method: either run `seed_data.postgres.sql` on an empty database, or let `init_db()` insert its 16 starter rows. Running both duplicates data. See [`DATABASE.md`](DATABASE.md).

### 3. Supabase Storage

Create a bucket named by `SUPABASE_BUCKET` (default `edusphere-papers`) and make it **public**; otherwise `get_public_url()` links return 401. The service-role key stays server-side only.

### 4. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.clean.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

Start it as `uvicorn app:app` **from the `backend/` folder** — the discovery modules use `from app import connect`.

### 5. Connect the frontend (optional)

Open the site → **Connect** view → enter `http://localhost:8000` as the API base → sign in with `ADMIN_EMAIL` / `ADMIN_PASSWORD`. Use `fetch(..., { credentials: "include" })` so the HttpOnly cookie is sent. With `COOKIE_SECURE=true`, the frontend must be on HTTPS and its exact origin must be in `CORS_ORIGINS`.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `RuntimeError` about `DATABASE_URL` on import | Set `DATABASE_URL`; the app validates it at import time |
| Login succeeds but you are immediately logged out | Set `COOKIE_SECURE=false` for local HTTP, or serve over HTTPS |
| Cookie not sent from the frontend | Add the exact origin to `CORS_ORIGINS` and use `credentials: "include"` |
| `relation "papers" does not exist` | Run `database/schema.postgres.sql` first — `init_db()` does not create tables |
| `AUTOINCREMENT` syntax error | You ran the SQLite seed on Postgres; use `seed_data.postgres.sql` |
| Supabase PDF links return 401 | Make the bucket public |
| Duplicate papers after restart | `init_db()` seeds at import time; clear the table or apply the proposed patch |
| `from app import connect` fails | Run uvicorn from the `backend/` folder, not as a package |
| Paper link shows 403 in an automated check | Some board sites block bots / non-Indian IPs; the site labels these as unverified |
| Playwright fails with `libnspr4.so` missing | Install browser libs (`libnspr4 libnss3 libasound2 libatk* libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2`) |

---

## Verification checklist

- [ ] `frontend/index.html` opens from the filesystem with all 137 papers
- [ ] `python3 build.py` produces a reproducible file
- [ ] `python3 validate.py` reports 0 errors
- [ ] `GET /api/health` returns OK
- [ ] `/docs` lists all routes
- [ ] `psql` shows the seeded tables
- [ ] Live demo loads with 0 external requests
