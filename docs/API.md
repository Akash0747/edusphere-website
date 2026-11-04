# API reference

Base URL (local): `http://localhost:8000` · Interactive docs: `/docs`, `/redoc`, `/openapi.json`.

The backend defines **46 routes** (41 under `/api`); most also have a trailing-slash alias. The "Auth" column below reflects the **original code** — routes marked ⚠️ are `/api/admin/*` endpoints that lack an access check (see [`CODE_REVIEW.md`](CODE_REVIEW.md)).

## Public

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Liveness + `total_papers_in_sql` |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/session` | Current session or `null` |
| `POST` | `/api/auth/login` | JSON `{ "email", "password" }`; sets HttpOnly `archive_session` cookie |
| `POST` | `/api/auth/logout` | Deletes session + clears cookie |
| `GET` | `/api/papers` | List papers; query `exam`, `q`, `limit` (≤500), `offset` |
| `GET` | `/api/papers/{id}` | Single paper |
| `GET` | `/api/papers/{id}/file` | 302 to Supabase public URL or `source_url`; `?download=1` is accepted but currently ignored |
| `GET` | `/api/stats` | Public metrics |
| `GET` | `/api/dashboard` | Public dashboard metrics |
| `GET` | `/api/mock-tests` | Mock questions — **includes `correct_option` and `explanation`** |
| `GET` | `/api/jee-advanced-papers/{id}/view` | 302 to stored PDF or an approved `jeeadv.ac.in` URL |
| `GET` | `/api/jee-advanced-papers/{id}/download` | Calls the view handler (no attachment header) |
| `GET` | `/docs`, `/redoc`, `/openapi.json` | Auto-generated docs |

## Admin (intended)

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/admin/papers` | ✅ | Multipart create: `exam, year, subject, session, title, description, sourceUrl, file` |
| `PUT` | `/api/admin/papers/{id}` | ✅ | Multipart edit; `file` and/or `removeFile=true` |
| `DELETE` | `/api/admin/papers/{id}` | ✅ | Delete row + stored object |
| `GET` | `/api/admin/cbse-discovery-test` | ✅ | Preview CBSE scraper output |
| `POST` | `/api/admin/cbse-sync` | ✅ | Insert discovered CBSE papers into `papers` |
| `GET` | `/api/admin/sample-discovery-test` | ✅ | Preview CBSE sample-paper discovery (registered twice; only the first handler runs) |
| `POST` | `/api/admin/sample-papers-sync` | ✅ | Insert into `sample_papers` |
| `GET` | `/api/admin/jee-main-discovery-test` | ✅ | Preview JEE Main discovery |
| `POST` | `/api/admin/jee-main-sync` | ✅ | Insert into `jee_main_papers` / `jee_main_year_sources` |
| `GET` | `/api/admin/jee-advanced-discovery-test` | ✅ | Preview JEE Advanced discovery |
| `POST` | `/api/admin/jee-advanced-sync` | ✅ | Upsert into `jee_advanced_papers` |

## Admin aliases / gaps ⚠️

| Method | Path | Auth | Issue |
| --- | --- | --- | --- |
| `GET` | `/api/admin/stats` | ⚠️ none | Alias of public `/api/stats`; README claims admin-only |
| `GET` | `/api/admin/dashboard` | ⚠️ none | Alias of public `/api/dashboard` |
| `GET` | `/api/admin/neet-discovery-test` | ⚠️ none | Unauthenticated NEET discovery preview |
| `POST` | `/api/admin/neet-sync` | ⚠️ none | Unauthenticated write into `public.neet_papers` |

There is **no** `/api/auth/forgot-password` endpoint despite the original README mentioning one.

## Auth model

1. `POST /api/auth/login` verifies the `scrypt` hash from `admins`.
2. A random opaque token is generated; its **SHA-256 hash** is stored in `sessions` with a 7-day `expires_at`.
3. The raw token is returned in an HttpOnly `archive_session` cookie (`Secure; SameSite=None` when `COOKIE_SECURE=true`).
4. `require_admin(request)` hashes the incoming cookie and looks it up in `sessions`.
5. `POST /api/auth/logout` deletes the row and clears the cookie.

For browser clients, always use `fetch(url, { credentials: "include" })`, and list the exact frontend origin in `CORS_ORIGINS`.

## Example

```bash
curl -s http://localhost:8000/api/health
curl -s "http://localhost:8000/api/papers?exam=jee-advanced&limit=5"

curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"..."}'

curl -b cookies.txt -F 'exam=cbse-12' -F 'year=2025' -F 'subject=Physics' \
  -F 'title=Sample paper' -F 'file=@paper.pdf' \
  http://localhost:8000/api/admin/papers
```
