# Contributing

This is a school project, but improvements are welcome — a corrected paper link, a new official paper, a typo fix or a better screenshot all help.

## Ground rules

1. **Keep it non-commercial.** No ads, paid features or monetisation; the site must stay within Vercel Hobby's free-tier terms.
2. **Never commit secrets.** Use `.env` (git-ignored) for `DATABASE_URL`, Supabase keys and admin credentials. `.env.example` lists the keys only.
3. **Cite sources.** Every new paper needs `sourceUrl`, `sourceLabel`, `origin` and a `verified` flag. Prefer official board/NTA URLs.
4. **Don't add reference-screenshot text.** The visual theme is torn paper / vintage cinema; no wording from any reference image is reproduced.
5. **Label honestly.** ZIP bundles, archive/index pages and illustrative practice questions must stay labelled as such.

## Adding a paper

1. Add the record to `frontend/src/data/archive.json` (or to the relevant source JSON in `frontend/src/data/`).
2. Run `cd frontend && python3 build.py` to regenerate `index.html`.
3. Run `python3 validate.py` (Playwright) or at least open `index.html` and check the new record appears and its link works.
4. Update the count in `README.md` / `docs/DATASET.md`.

## Changing the frontend

Editable sources live in `frontend/src/`:

| File | Purpose |
| --- | --- |
| `index.template.html` | Markup + placeholders |
| `styles.css`, `tears.css` | Theme and torn-edge clip-paths |
| `app.js` | All views, routing, state, filters, drawer, quiz |
| `data/` | Catalogue JSON files |
| `assets/` | Embedded JPEGs and woff2 fonts |

`build.py` inlines everything into `frontend/index.html`. Never edit `index.html` by hand.

## Commit style

`feat:`, `fix:`, `docs:`, `data:`, `chore:` — small, descriptive commits, e.g. `data: add JEE Advanced 2025 Paper 2 (official)`.

## Reporting a broken link

Open an issue with: paper title, exam/year, the URL, and what happened (403 / 404 / zip mismatch). Links are checked in batches; see `docs/DATASET.md`.
