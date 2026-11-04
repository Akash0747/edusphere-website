# Frontend — EduSphere website

## ⭐ Just open it

```
frontend/index.html
```

Double-click it. No install, no server, no internet connection. Every font, photo, stylesheet, script and all 137 paper records are embedded in that one 1.5 MB file.

Or serve it locally:

```bash
python3 serve.py 8080     # → http://localhost:8080
```

## Views

| View | Hash | What it does |
| --- | --- | --- |
| Home | `#/home` | Hero, exam tiles, featured papers, quick stats |
| Exams | `#/exams` | All shelves with paper counts |
| Papers | `#/papers` | Searchable/filterable catalogue, 12 per page |
| Practice | `#/practice` | 12 questions with explanations |
| My Desk | `#/desk` | Saved papers, solved progress, notes, add your own paper |
| Database | `#/database` | Raw catalogue table, provenance, export/import JSON |

Interactions: exam chips, year/subject/type/format filters, sort, pagination, surprise-me, paper drawer with Previous/Next, Open / Download / Copy link / Save / Mark solved, quiz, local add-paper form, optional API connect + admin login.

## Files

| Path | Purpose |
| --- | --- |
| `index.html` | **Built deliverable** — do not edit by hand |
| `src/index.template.html` | Markup with `{{...}}` placeholders |
| `src/styles.css` | Torn-paper / vintage-cinema theme |
| `src/tears.css` | Generated `clip-path` torn edges |
| `src/app.js` | All views, state, routing, filters, drawer, quiz, localStorage |
| `src/assets/` | `cinema.jpg`, `street.jpg`, `desk.jpg` + 3 woff2 fonts |
| `src/data/archive.json` | Final catalogue: 137 papers, 12 questions, 7 shelves |
| `src/data/repo-seed.json` | 30 papers + 2 mock questions parsed from backend `seed_data.sql` |
| `src/data/cbse-links.json`, `jeemain-links.json` | Official link indexes |
| `build_data.py` | Regenerates `archive.json` from the source datasets + curated official links |
| `build.py` | Inlines CSS/JS/fonts/images/data into `index.html` |
| `serve.py` | `ThreadingHTTPServer` bound to `0.0.0.0` |
| `validate.py` | Playwright smoke test (home → exams → papers → drawer → quiz → dashboard → mobile) |
| `SITE_NOTES.md` | Original site notes, provenance and caveats |

## Rebuild

```bash
python3 build_data.py     # optional: only if the source datasets changed
python3 build.py          # writes a fresh index.html
node --check src/app.js   # syntax check (optional)
python3 validate.py       # browser test (needs playwright + chromium)
```

## Design notes

- **Zero external requests.** No CDN, no web fonts over the network, no analytics. Verified with a headless browser: 0 external requests, 0 console/JS errors.
- **Offline-first by design.** The backend is optional; the "Database" and "Connect" screens explain the link. When an API base is configured, the frontend can talk to `../backend` over `fetch(..., { credentials: "include" })`.
- **Responsive.** On mobile the hero uses a translucent torn panel with light type so the display text stays readable over the photograph.
- **No copied text.** The reference screenshot supplied only the visual direction; none of its wording appears anywhere in the site.
- **Provenance is visible.** Each paper records `origin` (`repo` / `official` / `verified`), `verified`, `format` (pdf / zip / archive) and a `note` for edge cases.

## Caveats

- `localStorage` powers saved papers / notes / solved marks, so they are per-browser. In sandboxed iframes, `target="_blank"`, downloads and storage may be restricted — every drawer has a **Copy link** button as a fallback.
- Some official URLs return 403 to automated or non-Indian clients; these are labelled `verified: false` / "Link unchecked" rather than hidden.
- ZIP records are bundles and archive records are index pages, not single PDFs.

See [`../docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md) for the live Vercel deployment.
