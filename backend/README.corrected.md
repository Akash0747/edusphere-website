# EduSphere Backend — accurate README (drop-in replacement)

> Replaces the repository's `README.md`, which describes an older SQLite/local-disk
> version of this project. This document reflects `app.py` at commit `9607a80`.

A FastAPI backend for the EduSphere question-paper archive. It serves paper
metadata, proxies/redirects to PDFs, exposes admin dashboard metrics, and runs
scrapers that discover official CBSE / JEE Main / JEE Advanced / NEET papers.

## Stack

| Concern | What the code actually uses |
| --- | --- |
| Database | PostgreSQL via `psycopg` 3 (`DATABASE_URL`), typically Supabase Postgres |
| PDF storage | Supabase Storage bucket (`SUPABASE_BUCKET`), public URLs + 302 redirect |
| Auth | `admins` + `sessions` tables; scrypt password hash; SHA-256-hashed opaque session token in an HttpOnly cookie (`archive_session`, 7 days) |
| Server | FastAPI + Uvicorn; interactive docs at `/docs` |
| Scrapers | `requests` + `beautifulsoup4`, one module per exam |

There is **no SQLite**, no `DATA_DIR`, no `SECRET_KEY`, and no local PDF directory
in the current code. `COOKIE_SECURE` does exist (see below).

## 1. Create the database schema first

`init_db()` does **not** create tables — it only inserts an admin row and 16
starter papers. `seed_data.sql` in the repo is SQLite-flavoured
(`INTEGER PRIMARY KEY AUTOINCREMENT`) and only creates `mock_tests`, so it is not
runnable as-is on PostgreSQL.

Use `schema.postgres.sql` from this review folder (inferred from every SQL
statement in the code), or export the DDL from your existing Supabase project.
Then choose **one** seeding method:

- let `init_db()` insert its 16 starter rows on an empty `papers` table, **or**
- run `seed_data.postgres.sql` once against an empty database.

Loading both duplicates seed data. Verify the schema against a live database
before running any DDL — see the header comment in `schema.postgres.sql`.

Supabase Storage: create the bucket named by `SUPABASE_BUCKET` and make it
**public**, otherwise `get_public_url()` produces links that return 401.

## 2. Environment variables

See `.env.example` in this folder. All are read at import time except the
Supabase client, which is created lazily on first upload.

| Variable | Required | Meaning / default |
| --- | --- | --- |
| `DATABASE_URL` | **yes** | Postgres connection string. App raises `RuntimeError` at import if missing. |
| `ADMIN_EMAIL` | no | Initial admin email; defaults to `admin@edusphere.com`. |
| `ADMIN_PASSWORD` | **yes on a fresh DB** | Used only when no admin row exists. Otherwise ignored — you cannot rotate a password with this variable. |
| `SUPABASE_URL` | for uploads | Project URL, e.g. `https://xxxx.supabase.co`. |
| `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_SECRET_KEY`) | for uploads | Service-role key. Server-side only, never expose to the browser. |
| `SUPABASE_BUCKET` | no | Defaults to `edusphere-papers`. |
| `CORS_ORIGINS` | no | Comma-separated list; defaults to `https://souray.netlify.app,http://localhost:3000,http://127.0.0.1:3000`. |
| `COOKIE_SECURE` | no | Defaults to `true` → cookie is `Secure; SameSite=None`. Set to `false` for local HTTP development or the cookie will not be stored. |
| `CORS_ALLOW_NETLIFY_PREVIEWS` | no | Only in the proposed patch; set `true` to re-enable the `https://*.netlify.app` wildcard. |

The old README's `SECRET_KEY`, `DATA_DIR` and `COOKIE_SECURE=true` guidance for
SQLite deployments does not apply.

## 3. Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.clean.txt

export DATABASE_URL='postgresql://user:pass@localhost:5432/edusphere'
export ADMIN_EMAIL='you@example.com'
export ADMIN_PASSWORD='a-long-random-password'
export SUPABASE_URL='https://xxxx.supabase.co'
export SUPABASE_SERVICE_ROLE_KEY='...'
export COOKIE_SECURE=false          # local HTTP only
export CORS_ORIGINS='http://localhost:3000'

uvicorn app:app --host 0.0.0.0 --port 8000
```

Docs: `http://localhost:8000/docs` · Health: `GET /api/health`.

**Module name matters:** the discovery modules do `from app import connect`, so
start the app as `uvicorn app:app` from the repository root. Importing it as a
package (`uvicorn mypkg.app:app`) re-imports the file under a second name.

## 4. API routes

Auth column = whether the handler calls `require_admin(request)` in the
**current** repository. `/api/admin/*` routes marked "no" are a security bug
(see `REVIEW.md` and `PROPOSED_PATCH.patch`).

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/` | no | Liveness + `total_papers_in_sql` |
| GET | `/api/health` | no | Health check |
| GET | `/api/session` | no | Current session or `null` |
| POST | `/api/auth/login` | no | JSON `{ "email", "password" }`, sets cookie |
| POST | `/api/auth/logout` | no | Deletes session + cookie |
| GET | `/api/papers` | no | List; query `exam`, `q`, `limit` (≤500), `offset` |
| GET | `/api/papers/{id}` | no | Single paper |
| GET | `/api/papers/{id}/file` | no | 302 to Supabase public URL or `source_url`; `?download=1` is accepted but currently ignored |
| GET | `/api/stats`, `/api/dashboard` | no | Public metrics |
| GET | `/api/admin/stats`, `/api/admin/dashboard` | **no** | Aliases of the above — README claims admin-only |
| GET | `/api/mock-tests` | no | Mock questions; **includes `correct_option` and `explanation`** |
| POST | `/api/admin/papers` | yes | Multipart create; fields `exam, year, subject, session, title, description, sourceUrl, file` |
| PUT | `/api/admin/papers/{id}` | yes | Multipart edit; `file` and/or `removeFile=true` |
| DELETE | `/api/admin/papers/{id}` | yes | Delete row + stored object |
| GET | `/api/admin/cbse-discovery-test` | yes | Preview scraper output |
| POST | `/api/admin/cbse-sync` | yes | Insert discovered CBSE papers into `papers` |
| GET | `/api/admin/sample-discovery-test` | yes | Preview CBSE sample-paper discovery (registered twice; only the first handler runs) |
| POST | `/api/admin/sample-papers-sync` | yes | Insert into `sample_papers` |
| GET | `/api/admin/jee-main-discovery-test` | yes | Preview JEE Main discovery |
| POST | `/api/admin/jee-main-sync` | yes | Insert into `jee_main_papers` / `jee_main_year_sources` |
| GET | `/api/admin/jee-advanced-discovery-test` | yes | Preview JEE Advanced discovery |
| POST | `/api/admin/jee-advanced-sync` | yes | Upsert into `jee_advanced_papers` |
| GET | `/api/jee-advanced-papers/{id}/view` | no | 302 to stored PDF or an approved `jeeadv.ac.in` URL |
| GET | `/api/jee-advanced-papers/{id}/download` | no | Calls the view handler (no attachment header) |
| GET | `/api/admin/neet-discovery-test` | **no** | Preview NEET discovery |
| POST | `/api/admin/neet-sync` | **no** | Upsert into `public.neet_papers` |
| GET | `/docs`, `/redoc`, `/openapi.json` | no | Swagger / ReDoc |

Most routes are also registered with a trailing-slash alias. There is **no**
`/api/auth/forgot-password` endpoint despite the old README claiming one.

## 5. Frontend integration

The deployed frontend appears to be a TanStack Start app using server
functions, not these `/api/...` routes. Point its data layer at this origin and
use `fetch(..., { credentials: "include" })` so the HttpOnly cookie is sent.
PDF links should use `/api/papers/{id}/file`. With `COOKIE_SECURE=true` the
frontend must be on HTTPS, and its exact origin must be in `CORS_ORIGINS`.

## 6. Production notes

- Postgres and Supabase Storage are external and persistent; no local disk is
  needed. Use a connection pooler for serverless/multi-worker deployments —
  `connect()` opens a new connection per request.
- Run `init_db()` once (see the lifespan change in the proposed patch); with
  multiple Uvicorn workers, startup seeding needs serialization.
- Keep the service-role key secret; it bypasses all Row Level Security.
- Add login rate limiting, session cleanup, and CSRF protection before exposing
  admin routes publicly — see `REVIEW.md`.
- The scrapers make dozens of outbound HTTP requests per sync and are invoked
  synchronously inside request handlers; put them behind a background job.
