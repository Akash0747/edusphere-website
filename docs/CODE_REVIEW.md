# Engineering review — summary

As part of the project, the original backend repository (`yeahhthaarthh/edusphere-backend`, commit `9607a80`) was audited end-to-end. This document summarises what was found and what was delivered. The **full** review, the fix script, the route audit and the proposed patch live in [`engineering/`](engineering/).

> ⚠️ **Status:** the backend code in [`../backend/`](../backend/) is preserved exactly as received. The proposed patch is **not applied** — it is provided as a documented next step, not as a claim that the code was rewritten.

## What the review covered

- All of `app.py` (~1,100 lines), five discovery modules, `requirements.txt`, `README.md` and `seed_data.sql`
- Route registration, authentication checks, CORS configuration, cookie handling, SQL statements, Supabase Storage calls, upload validation and startup behaviour
- `python3 -m py_compile` on every Python file
- A stubbed Postgres connection to enumerate all 46 routes and their auth state
- `storage3` API behaviour for `get_public_url()` and `x-upsert`

## Findings by priority

### P0 — fix before any public deployment

| # | Finding |
| --- | --- |
| 1 | `GET /api/admin/neet-discovery-test` and `POST /api/admin/neet-sync` have **no** `require_admin()` check — an unauthenticated caller can trigger a write |
| 2 | Credentialed CORS allows `https://.*\.netlify\.app` (any Netlify site) with no CSRF protection on cookie-authenticated writes |
| 3 | `GET /api/admin/stats` and `GET /api/admin/dashboard` are public aliases despite their names and the old README |

### P1 — correctness / operability

| # | Finding |
| --- | --- |
| 4 | No schema or migration: `init_db()` only inserts rows, so a fresh database fails |
| 5 | `seed_data.sql` is SQLite-flavoured (`AUTOINCREMENT`) and cannot run on Postgres |
| 6 | Stale README describes SQLite, `SECRET_KEY`, `DATA_DIR`, a 20 MB limit and a forgot-password route that does not exist |
| 7 | Import-time `init_db()` duplicates seeding under multiple workers |
| 8 | `GET /api/admin/sample-discovery-test` is registered twice; duplicate OpenAPI operation ID |
| 9 | `?download=1` is accepted but ignored — no `Content-Disposition` |
| 10 | Deleting a DB row can orphan the Supabase object; uploads can orphan objects when the DB write fails |
| 11 | No login rate limiting or lockout |

### P2 — polish

Public mock-test answers, a download counter incremented on `GET`, open redirect risk through admin-supplied `source_url`, synchronous scrapers blocking the event loop, no session cleanup, duplicate requirements entries, unused `httpx`.

## What this repository delivers instead of a silent rewrite

| Deliverable | Path |
| --- | --- |
| Full 18-finding review with priorities and a checklist | [`engineering/REVIEW.md`](engineering/REVIEW.md) |
| 21 concrete fixes as an **apply-cleanly** patch | [`engineering/PROPOSED_PATCH.patch`](engineering/PROPOSED_PATCH.patch) |
| Idempotent fix script (`--check` mode) | [`engineering/apply_fixes.py`](engineering/apply_fixes.py) |
| Route/auth audit script (stubbed DB, counts by `(method, path)`) | [`engineering/audit_routes.py`](engineering/audit_routes.py) |
| Corrected backend README | [`../backend/README.corrected.md`](../backend/README.corrected.md) |
| Reconstructed PostgreSQL schema | [`../database/schema.postgres.sql`](../database/schema.postgres.sql) |
| Postgres-compatible seed | [`../database/seed_data.postgres.sql`](../database/seed_data.postgres.sql) |
| Clean requirements + env template | [`../backend/requirements.clean.txt`](../backend/requirements.clean.txt), [`../.env.example`](../.env.example) |

## Verification performed

| Check | Result |
| --- | --- |
| `python3 -m py_compile *.py` | ✅ pass |
| `apply_fixes.py --check` | ✅ 21/21 checks OK |
| Post-fix route audit (stubbed DB) | ✅ all admin routes protected, no duplicate `(method, path)` |
| `git apply --check PROPOSED_PATCH.patch` | ✅ applies cleanly (97 insertions / 60 deletions) |
| Patched lifespan startup with stub DB | ✅ completes |
| Original clone left clean | ✅ patch intentionally not applied |

**Not tested:** a live FastAPI + Postgres + Supabase runtime, the real cookie flow, actual file uploads, or scraper HTTP calls. Those require real credentials and were out of scope for a static, offline-first school project.

## Suggested next step for a v2

Apply the patch in a branch, add a proper migration runner, add login rate limiting + CSRF, and wire the frontend's Connect view to the hardened service. This is listed as "future scope" in [`PROJECT_REPORT.md`](PROJECT_REPORT.md).
