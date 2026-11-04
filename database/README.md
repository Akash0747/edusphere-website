# Database — schema, seed and SQL

The backend repository shipped a seed file but **no schema or migration**, and its SQL was written for SQLite. This folder makes the database explicit and runnable, which is what a school project needs to be reproducible.

## Files

| File | Dialect | Purpose |
| --- | --- | --- |
| `schema.postgres.sql` | PostgreSQL | Reconstructed DDL for every table referenced by `app.py` and the five discovery modules. Uses `BIGSERIAL`, `BIGINT` epoch columns and `CREATE TABLE IF NOT EXISTS`. |
| `seed_data.postgres.sql` | PostgreSQL | Postgres-compatible seed data. |
| `seed_data.sqlite.sql` | SQLite | The original `seed_data.sql` from the backend repository, kept verbatim for reference. |

Related data files:

| File | Purpose |
| --- | --- |
| `../frontend/src/data/repo-seed.json` | 30 papers + 2 mock questions parsed out of the original seed |
| `../frontend/src/data/archive.json` | Final 137-paper / 12-question catalogue bundled into the website |

## Quick start

```bash
# From the repository root:
docker compose up -d db
export DATABASE_URL='postgresql://edusphere:edusphere@localhost:5432/edusphere'

psql "$DATABASE_URL" -f database/schema.postgres.sql
psql "$DATABASE_URL" -f database/seed_data.postgres.sql
```

Or with `make`: `make db-up && make db-schema && make db-seed`.

## ⚠️ Important caveats

1. **Verify against a live database first.** The schema was inferred from every SQL statement in the code. Before running it on an existing Supabase/Postgres project, compare columns:

   ```sql
   SELECT table_name, column_name, data_type, is_nullable, column_default
   FROM information_schema.columns
   WHERE table_schema = 'public'
   ORDER BY table_name, ordinal_position;
   ```

   `CREATE TABLE IF NOT EXISTS` will **not** add missing columns to existing tables — write explicit `ALTER TABLE` statements instead.

2. **Seed only once.** `app.py`'s `init_db()` also inserts 16 starter papers plus an admin row on an empty `papers` table. Either let `init_db()` seed **or** run `seed_data.postgres.sql`, never both, or you will get duplicate rows.

3. **Do not run the SQLite seed on Postgres.** It uses `INTEGER PRIMARY KEY AUTOINCREMENT`, which PostgreSQL rejects. Its `CREATE TABLE` only covers `mock_tests`; the `papers` table is assumed to already exist.

4. **Epoch columns are `BIGINT`.** The Python code writes `int(time.time())`, not timestamps.

5. **Supabase Storage is separate.** PDFs live in a bucket, not in Postgres. Create the bucket named by `SUPABASE_BUCKET` and make it public.

## Tables

`admins`, `sessions`, `papers`, `mock_tests`, plus the discovery tables: `cbse_papers` / `cbse_year_sources`, `sample_papers` / `sample_year_sources`, `jee_main_papers` / `jee_main_year_sources`, `jee_advanced_papers`, and `public.neet_papers`.

A full table-by-table breakdown and an ER diagram are in [`../docs/DATABASE.md`](../docs/DATABASE.md).
