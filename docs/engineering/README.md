# Engineering review artefacts

These files came from the audit of the original backend repository and are kept here for transparency and as a discussion point in the project report. Read the summary first: [`../CODE_REVIEW.md`](../CODE_REVIEW.md).

| File | What it is |
| --- | --- |
| `REVIEW.md` | Full review: architecture, 18 findings with P0/P1/P2 priorities, route counts and a priority checklist |
| `PROPOSED_PATCH.patch` | 21 fixes as a unified diff. Applies cleanly with `git apply --check`; **not applied** to `backend/app.py` |
| `apply_fixes.py` | Idempotent script that applies the 21 fixes; `--check` runs a dry run |
| `audit_routes.py` | Enumerates routes and their auth state using a stubbed `psycopg.connect` (`DATABASE_URL=postgresql://stub/stub`); counts duplicates by `(method, path)` |

## Reproduce the audit

```bash
# From the backend clone, with dependencies installed
python3 audit_routes.py
python3 apply_fixes.py --check     # dry run: 21 checks
git apply --check PROPOSED_PATCH.patch
```

The audit used a stubbed Postgres connection — **no real database or Supabase project was contacted**. A patched lifespan startup was also tested with the stub. A live runtime, cookie flow, file upload and scraper HTTP calls were **not** tested.

## Important

`seed_data.sql` in the backend is SQLite-flavoured and contains `INSERT INTO papers` without creating that table. To run it in SQLite (as `build_data.py` does), execute the **whole file** in order — stripping the `CREATE TABLE` statement causes `no such table: mock_tests`. For PostgreSQL, use [`../../database/schema.postgres.sql`](../../database/schema.postgres.sql) and `seed_data.postgres.sql` instead.
