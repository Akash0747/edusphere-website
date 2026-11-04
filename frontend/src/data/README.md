# Data

| File | Contents |
| --- | --- |
| `archive.json` | **Final catalogue**: 137 papers, 12 practice questions, 7 exam shelves, counts and meta. Embedded as `window.__ARCHIVE__`. |
| `repo-seed.json` | 30 papers + 2 mock-test questions parsed verbatim from `backend/seed_data.sql` by executing the full SQL file in SQLite. |
| `cbse-links.json` | Official CBSE Class XII question-paper links (12 subjects, 2022–2025) parsed from `cbse.gov.in/cbsenew/question-paper.html`. |
| `jeemain-links.json` | Official JEE Main 2026 shift PDFs and archive links parsed from `jeemain.nta.nic.in/sitemap/`. |

## Regenerating

```bash
cd frontend
python3 build_data.py     # → src/data/archive.json
python3 build.py          # → index.html
```

`build_data.py` merges the seed rows and official link indexes with curated official/verified records, de-duplicates them, assigns IDs and sets `origin`, `format`, `verified` and `note`.

See [`../../docs/DATASET.md`](../../docs/DATASET.md) for sources, verification results and the honesty rules (ZIP bundles, archive pages, illustrative questions).
