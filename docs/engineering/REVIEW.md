# EduSphere Backend — code review

**Repository:** https://github.com/yeahhthaarthh/edusphere-backend
**Reviewed:** 2026-11-03, `main` @ `9607a80` (65 commits, last commit 2026-10-31)
**Scope:** all 9 tracked files, ~1,080 lines of `app.py` + 5 discovery modules
**Method:** static reading, `py_compile` on every file, and an import of the
FastAPI app with a stubbed `psycopg` connection to enumerate all 46 registered
routes (41 `/api/...`, the root, and 4 docs paths) and check which call
`require_admin()` (`audit_routes.py`). Supabase SDK
behaviour was checked against the installed `storage3` source. **No live
Postgres/Supabase instance was available**, so runtime DB behaviour is inferred
from the SQL, not executed.

---

## TL;DR

The API is a reasonable small FastAPI service with good instincts (parameterized
SQL, hashed passwords, hashed session tokens, PDF magic-byte validation, host
allowlists in the scrapers). But it is **not safe to expose publicly as-is** and
**cannot be bootstrapped from a fresh database using the checked-in files**:

1. Two `/api/admin/*` NEET endpoints have **no authentication** at all.
2. CORS trusts **every** `*.netlify.app` site with credentials, and there is no
   CSRF check on cookie-authenticated admin writes.
3. There is **no schema/migration** for 7 of the 9 tables the code queries; the
   only `CREATE TABLE` in the repo uses SQLite syntax that PostgreSQL rejects.
4. The **README describes a different application** (SQLite, local disk, 20 MB,
   `SECRET_KEY`, `DATA_DIR`, a forgot-password route that doesn't exist).
5. Startup work runs at **import time**, which makes the app fragile under
   multiple workers and when imported by its own discovery modules.

`PROPOSED_PATCH.patch` fixes 21 high-confidence issues in `app.py` (verified to
compile and re-audited). The other deliverables supply the missing schema,
docs, dependency list and env template.

---

## Architecture (what the code actually does)

```
Browser ──fetch(credentials:include)──► FastAPI (app.py)
                                        │
                    ┌───────────────────┼────────────────────┐
                    ▼                   ▼                    ▼
        Postgres/Supabase DB   Supabase Storage    Official exam sites
        admins, sessions,      (public bucket,     (cbseacademic.nic.in,
        papers, mock_tests,     PDF objects)        jeeadv.ac.in,
        sample_papers,                             jeemain.nta.nic.in,
        jee_main_papers,                           neet.nta.nic.in, + 3
        jee_advanced_papers,                       third-party NEET sites)
        neet_papers                                ▲
                    ▲                             │
                    └── 5 discovery modules ──────┘
                        (requests + BeautifulSoup → sync_*() → INSERT/UPSERT)
```

- `papers` is the main table. A row either points at a Supabase Storage object
  (`stored_name`) or is a redirect to an external `source_url`
  (`stored_name = "EXTERNAL_URL"`). `GET /api/papers/{id}/file` 302-redirects.
- All 5 discovery modules do `from app import connect` to reuse the DB helper.
- Auth: scrypt (`n=2**14`, 16 MB) salted hash; session token is random, only its
  SHA-256 is stored; cookie `archive_session` HttpOnly, 7-day TTL,
  `Secure; SameSite=None` by default.

---

## Findings

Severity: **P0** fix before any public deployment · **P1** should fix soon ·
**P2** correctness/maintainability.

### P0-1 — Unauthenticated admin endpoints (confirmed)

`app.py:1065` and `app.py:1076`:

```python
@app.get("/api/admin/neet-discovery-test")
def neet_discovery_test():              # no Request, no require_admin
    records = discover_neet_papers()

@app.post("/api/admin/neet-sync")
def neet_sync():                        # no Request, no require_admin
    return sync_neet_papers()
```

These are the **only** `/api/admin/*` routes without `require_admin()` — the
route audit confirms every other admin route has it. `neet_sync` performs a long
multi-site crawl (NTA + Examgoal + Pracbee + Aglasem, years 2007–2026, with PDF
HEAD/Range verification) and then upserts into `public.neet_papers`. An
anonymous caller can trigger unlimited outbound traffic and DB writes — an easy
DoS and unauthenticated data-integrity hole.

**Fix in patch:** add `request: Request` + `require_admin(request)` to both.

### P0-2 — Credentialed CORS wildcard + no CSRF protection

`app.py:75` `allow_origin_regex=r"https://.*\.netlify\.app"` with
`allow_credentials=True`, and `app.py:~440` sets the session cookie to
`SameSite=None; Secure`. Anyone can host a page on `*.netlify.app` (free deploy
previews included) and have the browser attach the admin's cookie.

CORS alone does **not** stop this class of attack: the admin write endpoints are
`multipart/form-data` POSTs, which are CORS "simple requests" — they are sent
**before** any preflight check, and the browser only blocks reading the
response. `PUT`/`DELETE` are preflighted and would be blocked, but
`POST /api/admin/papers` and `POST /api/admin/*-sync` execute. There is no CSRF
token, no `Origin`/`Sec-Fetch-Site` check, and no `SameSite` protection.

**Fix in patch:** the wildcard becomes opt-in via `CORS_ALLOW_NETLIFY_PREVIEWS`,
and `require_admin()` rejects state-changing requests whose `Origin` is not in
`CORS_ORIGINS` (requests with no `Origin` — curl, server jobs — still work).
For full protection also add a CSRF token or set `SameSite=Strict`/`Lax` if the
frontend is same-site.

### P0-3 — `/api/admin/stats` and `/api/admin/dashboard` are public

`app.py:556-587` registers four decorators on the same unprotected `stats()` /
`dashboard()` functions. The old README labels the admin-prefixed variants
"(admin)". Impact is limited to exposing counts (total papers, downloads), but
it is an auth-consistency bug and a hint that route protection was added ad hoc.

**Fix in patch:** `/api/stats` + `/api/dashboard` stay public; the
`/api/admin/*` aliases get dedicated wrappers that call `require_admin()`.

### P1-4 — No schema; the shipped SQL is SQLite, not Postgres

`app.py:372` calls `init_db()` at import, which immediately does
`SELECT id FROM admins ...` and `SELECT COUNT(*) FROM papers`. These tables are
never created anywhere in the repo. `seed_data.sql` contains exactly one DDL
statement, and it is invalid PostgreSQL:

```sql
CREATE TABLE IF NOT EXISTS mock_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- SQLite-only syntax
    ...
);
INSERT INTO papers (...) VALUES ...;        -- `papers` never created
```

Tables referenced but never created: `admins`, `sessions`, `papers`,
`mock_tests` (invalid DDL), `sample_papers`, `jee_main_papers`,
`jee_main_year_sources`, `jee_advanced_papers`, `public.neet_papers`.
`cbse_discovery.py:184` also inserts `papers.class_name` and
`papers.subject_code`, two columns never mentioned by `app.py` or the seed file.

A fresh deployment therefore fails at import with `UndefinedTable`. The service
only works today because someone created these tables manually in Supabase —
that knowledge is not in the repo.

**Deliverable:** `schema.postgres.sql` (inferred from every SQL statement, with
the `UNIQUE(source_url)` constraints required by the two `ON CONFLICT` upserts)
and `seed_data.postgres.sql`. **Verify against your live schema first** — see
the warning at the top of the SQL file.

### P1-5 — README describes a different application

| README says | Code does |
| --- | --- |
| SQLite database | PostgreSQL via `psycopg`, `DATABASE_URL` mandatory |
| Local PDFs under `DATA_DIR` | Supabase Storage bucket + public URLs |
| 20 MB upload limit | `MAX_PDF_BYTES = 50 * 1024 * 1024` |
| `SECRET_KEY`, `DATA_DIR`, `COOKIE_SECURE` env vars | Only `COOKIE_SECURE` exists; needs `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` |
| `POST /api/auth/forgot-password` placeholder | **Route does not exist** |
| "SQLite and uploaded PDFs may be lost on redeploy" | Not applicable |
| Lists 13 routes | 41 `/api` routes (incl. 10 discovery/sync endpoints), plus `/`, 4 docs paths and trailing-slash aliases |

**Deliverable:** `README.corrected.md` (drop-in replacement) + `.env.example`.

### P1-6 — Startup work at import time; duplicate seeding under multiple workers

`init_db()` is called as a top-level statement (`app.py:372`). Consequences:

- Importing `app.py` (tests, tooling, or `from app import connect` from a
  discovery module under a different module name) opens a DB connection and can
  re-run the bootstrap.
- `uvicorn --workers 4` → 4 processes all check `COUNT(*)` and can all seed 16
  rows. There is no unique constraint on `papers`, so duplicates are silent.
- A brief DB outage at import kills the process rather than serving 503.

**Fix in patch:** move `init_db()` into a FastAPI `lifespan` handler and take a
`pg_advisory_xact_lock()` so concurrent workers serialize the bootstrap.
Longer term, use a real migration tool (Alembic) and a unique key for seed rows.

### P1-7 — Duplicate route registration

`app.py:825` and `app.py:867` both register
`GET /api/admin/sample-discovery-test` under the **same function name**.
Starlette matches the first, so the second handler is dead code. FastAPI emits:

```
UserWarning: Duplicate Operation ID sample_discovery_test_api_admin_sample_discovery_test_get
```

(confirmed by generating the OpenAPI schema). Clients generated from `/openapi.json`
may be wrong. **Fix in patch:** remove the second definition (the richer first
one, with `by_class`/`by_session` summaries, is kept).

### P1-8 — `?download=1` is silently ignored

`app.py:524` accepts `download: int = 0` but `paper_file()` never uses it; it
always 302-redirects to an inline public URL. Docstrings for
`/api/jee-advanced-papers/{id}/download` (`app.py:1057`) similarly just calls the
view handler with no `Content-Disposition`.

**Fix in patch:** for Supabase-hosted PDFs, pass
`get_public_url(path, {"download": filename})` (verified against `storage3`'s
`SyncBucketProxy.get_public_url`) so Storage returns an attachment header.
External `source_url` redirects cannot be forced to download without proxying
the bytes — document that limitation.

### P1-9 — Storage objects can be orphaned

- `save_pdf()` uploads to Supabase **before** the DB insert. If `INSERT` fails
  (`app.py:660`) the object is unreachable but still stored.
- `update_paper()` (`app.py:~730`): if a form sends both a new `file` and
  `removeFile=true`, the newly uploaded object is forgotten while the old one is
  deleted.
- `delete_stored_pdf()` (`app.py:156`) swallows **all** exceptions, so cleanup
  failures are invisible.

**Fix in patch:** handle the `file + removeFile` case. Full transactional
cleanup (compensating delete on DB failure, retry queue, error logging) remains
recommended follow-up work.

### P1-10 — No rate limiting on login; weak-ish KDF

`app.py:413` `/api/auth/login` has no throttling, lockout, CAPTCHA or logging.
scrypt `n=2**14, r=8, p=1` is ~16 MB per attempt — adequate but modest; a
flood of guesses also burns CPU. Unknown emails skip the hash entirely, giving
a timing oracle for account enumeration.

**Recommend:** `slowapi`/Redis rate limit per IP+email, constant-time dummy hash
for unknown users, bump to `n=2**15` or switch to Argon2id/bcrypt, add audit
logging. Not in the patch (needs infrastructure choices).

### P2-11 — `upsert: "false"` is a truthy string

`app.py:140` passes `"upsert": "false"`. In `storage3`:

```python
upsert = options.pop("upsert", None)
if upsert:                      # "false" is truthy in Python
    options["x-upsert"] = upsert
```

So an `x-upsert: false` header is sent even though the intent is "never
overwrite". UUID-prefixed object paths make collisions practically impossible,
but the header is unintended. **Fix in patch:** omit the key (the SDK default is
no upsert).

### P2-12 — NULL-unsafe metrics

`app.py:566` and `app.py:596` use `stored_name <> '' OR source_url <> ''`. In
SQL, `NULL <> ''` is `NULL`, so a row with one NULL and one populated column is
counted as having **no** file (`CASE WHEN NULL → ELSE 0`). **Fix in patch:**
`COALESCE(...)`.

### P2-13 — GET with side effects

`paper_file()` increments `downloads` and writes `updated_at` on **every**
request — including bots, prefetch, HEAD-like probes and the browser's own
redirect follow. Counts drift. Consider a dedicated `POST /api/papers/{id}/view`
or a queued counter, and add `Cache-Control` to the response.

### P2-14 — Mock-test answers exposed publicly

`GET /api/mock-tests` (`app.py:610`) returns `SELECT *`, including
`correct_option` and `explanation`. If these are student-facing quizzes, anyone
can fetch the answer key. Also no `LIMIT`. Recommend a separate DTO that omits
answers until submission.

### P2-15 — Fragile self-import + unverified table

`app.py:987` does `from app import connect` **inside** `app.py` itself. It works
only when the module is imported as top-level `app`; under another module name it
creates a second module instance and re-runs import-time side effects. **Fix in
patch:** use the already-in-scope `connect`.

That endpoint also queries `jee_advanced_papers.download_url` /
`storage_path` — columns absent from the repo's seed file. Its URL allowlist
logic correctly requires HTTPS on `jeeadv.ac.in` for external links, but skips
validation entirely for `storage_path`-derived URLs (built from env vars, so
lower risk).

### P2-16 — Seed data quality

`init_db()` and `seed_data.sql` include rows whose `source_url` is an HTML
landing page (`https://jeemain.nta.nic.in/`, `https://neet.nta.nic.in/`, CISCE
specimen pages) while `file_name` claims a `.pdf`. Clicking "Download" on those
opens a website. `paper_dict()` also sets `hasFile = True` for any row with
`stored_name = "EXTERNAL_URL"`, even if `source_url` is later blanked.

### P2-17 — Error handling inconsistencies

- Discovery "test" endpoints return **HTTP 200** with `{"success": false}` on
  exception, so monitoring won't see failures.
- Sync endpoints return `detail=f"... failed: {str(e)}"` — raw exception text
  (potentially containing DB hostnames or credentials) leaks to clients.
- `delete_paper()` returns `{"ok": true}` with no 204; harmless, but inconsistent.

### P2-18 — Repo hygiene

- `requirements.txt` lists `requests`, `beautifulsoup4`, `psycopg[binary]`
  twice; `httpx` is imported but unused → `requirements.clean.txt`.
- `app.py` imports `os`, `urlparse`, `HTTPException`, `RedirectResponse`,
  `UploadFile` 2–3× each; `httpx`, `StreamingResponse` unused → patch cleans up.
- No `.gitignore` (a committed `.env` is one mistake away), no `.env.example`,
  no tests, no CI, no Dockerfile, no license.
- No session cleanup job (`sessions` grows forever), no session rotation on
  login, no password-change endpoint, no way to invalidate all sessions.
- `parse_paper_fields()` declares `title: str = Form("")` but rejects titles
  shorter than 3 chars — effectively required, but documented as optional.
  `sourceUrl` uses camelCase while every other form field is snake_case.
- `save_pdf()` reads up to 50 MB fully into memory and only checks that
  `%PDF-` appears somewhere in the first 1024 bytes (no `%EOF`, no real parse).
  Concurrent uploads can spike RAM.
- `/api/papers/{id}/file` redirects to any admin-supplied `http(s)://` URL —
  an admin-controlled open redirect. Low risk, but worth an allowlist.
- Discovery syncs are invoked **inside the HTTP request** and run for minutes;
  move to a background queue. On the plus side, `neet_discovery.py` has proper
  per-source host allowlists, re-checks hosts after redirects, and verifies PDF
  magic bytes before accepting a link — good defensive work.

---

## What's done well

- Every SQL statement uses `%s` parameterization; the dynamic `WHERE` in
  `list_papers` only appends fixed fragments. No injection found.
- Passwords are scrypt-hashed with a random salt; session tokens are random and
  stored only as SHA-256 digests; cookies are HttpOnly.
- Input validation on exam slug, year range, title/subject lengths, URL scheme,
  file extension, size and PDF magic bytes.
- `ON CONFLICT ... DO UPDATE` upserts for JEE Advanced and NEET discovery.
- Scrapers validate hosts before and after redirects (`neet_discovery.py`).
- Trailing-slash route aliases show attention to frontend integration details.

---

## Priority checklist

**Before any public deployment**
- [ ] Apply `PROPOSED_PATCH.patch` (or run `apply_fixes.py`) — auth on NEET routes, CORS/CSRF, admin alias protection.
- [ ] Add login rate limiting and session cleanup.
- [ ] Confirm the Supabase bucket is public **only** for PDFs and the service-role key is server-side only.
- [ ] Verify live DB schema against `schema.postgres.sql`.

**Soon**
- [ ] Replace `README.md` with `README.corrected.md`; swap `requirements.txt` and add `.env.example` + `.gitignore`.
- [ ] Introduce Alembic (or checked-in migrations) and remove the runtime seed.
- [ ] Move discovery syncs to background jobs.

**Later**
- [ ] Background download counters, hide mock-test answers, structured logging/metrics, tests + CI, container image.

---

## Deliverables in this folder

| File | What it is |
| --- | --- |
| **REVIEW.md** | This report |
| **PROPOSED_PATCH.patch** | 21 targeted fixes to `app.py`; apply with `git apply PROPOSED_PATCH.patch` from the repo root |
| **apply_fixes.py** | Idempotent-by-assertion script that regenerates the patch's changes; `--check` validates without writing |
| **audit_routes.py** | Imports the app with a stubbed DB and prints every route + auth status; reproduces the findings |
| **README.corrected.md** | Accurate setup, env vars, and full endpoint table |
| **schema.postgres.sql** | Inferred DDL for all 9 tables — **verify against live DB before running** |
| **seed_data.postgres.sql** | Postgres-compatible conversion of the repo's seed file |
| **.env.example** | All environment variables with safe defaults |
| **requirements.clean.txt** | Deduplicated, bounded dependency list |

The pristine clone is at `/home/user/edusphere-backend` (unmodified apart from
this review's temporary test run, which was reverted).

### Applying the patch

```bash
cd /home/user/edusphere-backend
git apply /home/user/edusphere-review/PROPOSED_PATCH.patch
python3 -m py_compile app.py
# re-run the audit to confirm all /api/admin/* routes are protected:
cd /home/user/edusphere-review && PYTHONPATH=<deps> python3 audit_routes.py
```

The patch was validated: all 21 replacements matched exactly once, the result
compiles, the app imports cleanly with a stub DB, no duplicate-operation-ID
warning is emitted, and the route audit reports `yes` for every admin route.
