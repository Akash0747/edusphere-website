# Dataset — how the 137 papers were assembled

The catalogue is the heart of the project. This document records exactly where it came from so the work is reproducible and can be defended in a viva.

## Final shape

`frontend/src/data/archive.json`

```jsonc
{
  "meta":   { /* build info, title, caveats */ },
  "exams":  [ /* 7 shelves */ ],
  "papers": [ /* 137 records */ ],
  "questions": [ /* 12 practice questions */ ],
  "counts": { "isc-12": 16, "cbse-12": 58, "jee-main": 14,
              "jee-advanced": 30, "neet": 10, "cbse-10": 7, "icse-10": 2 }
}
```

Each paper carries: `id, exam, year, subject, session, title, description, type, format, sourceUrl, sourceLabel, fileName, origin, downloads, featured, verified, note, topics`.

| Field | Why it matters |
| --- | --- |
| `origin` | `repo` (verbatim from `seed_data.sql`), `official` (board/NTA), `verified` (checked mirror) |
| `verified` | `false` when a link could not be confirmed |
| `format` | `pdf` (direct file), `zip` (bundle), `archive` (index/list page) |
| `note` | Explains edge cases, e.g. "Link unchecked", "Bundle, not a single PDF" |
| `sourceLabel` | Human-readable attribution shown in the UI |

## Sources

| Source | Used for |
| --- | --- |
| `backend/seed_data.sql` (SQLite) | 30 papers + 2 mock-test questions, parsed by executing the full file in SQLite → `repo-seed.json` |
| [jeeadv.ac.in/archive.html](https://jeeadv.ac.in/archive.html) | Official JEE Advanced papers 2007–2025; pattern `past_qps/{year}_{1\|2}[_English\|_Hindi].pdf` plus AAT papers |
| [cbse.gov.in/cbsenew/question-paper.html](https://www.cbse.gov.in/cbsenew/question-paper.html) | 935 Class XII links; 12 subjects, years 2022–2025 → `cbse-links.json` |
| [jeemain.nta.nic.in/sitemap/](https://jeemain.nta.nic.in/sitemap/) | 9 official 2026 B.Tech shift PDFs + archive pages → `jeemain-links.json` |
| [neet.nta.nic.in/archive/](https://neet.nta.nic.in/archive/) | NTA archive; curated code-wise indexes (CollegeDunia, Careers360, Aakash) and repo-allowlisted mirrors |
| [cisce.org](https://cisce.org/specimen-question-papers-isc-class-xii-2025/) + AglaSem mirrors | ISC Class 12 specimen papers |

## Build pipeline

```
backend/seed_data.sql ──(sqlite3 execute)──> src/data/repo-seed.json
cbse.gov.in HTML      ──(parse)───────────> src/data/cbse-links.json
jeemain.nta.nic.in    ──(parse)───────────> src/data/jeemain-links.json
curated official + verified records ──────┐
                                          ├─ build_data.py ─> src/data/archive.json
repo-seed + link indexes ─────────────────┘
                                                  │
                                            build.py
                                                  ▼
                            frontend/index.html :: window.__ARCHIVE__
```

`build_data.py` de-duplicates records, assigns stable IDs, sets `origin`/`format`/`verified`, and adds the honest `note` labels. `build.py` then inlines the JSON together with CSS, JS, fonts and photos.

## Link verification (run on 2026-11-03)

| Result | Count | Handling |
| --- | ---: | --- |
| HTTP 200 | 111 | Marked `verified: true` where applicable |
| HTTP 403 | 8 | Anti-bot / region blocks (cisce.org, AglaSem, CollegeDunia, Aakash) — labelled |
| HTTP 000 (unreachable) | 4 | NCERT textbook PDFs — `verified: false`, "Link unchecked" |

Total: **123 unique `sourceUrl`s**. Broken links are shown, not hidden — students can still copy them or try from a different network.

## Honesty rules

1. **ZIP records are bundles**, not individual question papers — labelled in the UI.
2. **Archive-page records are indexes**, not PDFs — labelled.
3. **10 of the 12 practice questions are illustrative** and explicitly marked "not official". The other 2 come verbatim from `mock_tests` in `seed_data.sql`.
4. **No text from the reference screenshot** was reproduced; it was used only for the torn-paper / vintage-cinema visual direction.
5. **Ownership** stays with CISCE, CBSE, NTA and the IITs; EduSphere only links to publicly available educational material.

## Adding more papers

See [`../CONTRIBUTING.md`](../CONTRIBUTING.md). Prefer official URLs, fill all provenance fields, rebuild with `python3 build.py`, and update the counts here and in the root `README.md`.
