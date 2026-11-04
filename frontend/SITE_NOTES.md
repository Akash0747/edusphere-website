# EduSphere — The Paper Archive

A complete, self-contained frontend for browsing previous year question papers
(PYQs), in the **torn-paper / vintage-cinema collage** style of the reference
picture you supplied. No text from that picture is used — only its visual
language: kraft paper, dusty blue paper, cream stock, roughly torn white edges,
an amber-lit neighbourhood cinema, and heavy condensed display type.

> **Live on Vercel (free Hobby):** https://edusphere-paper-archive.vercel.app/
> See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the deployment details and how to
> keep it free.
>
> **Open `index.html`.** Double-click it, or serve the folder with
> `python3 serve.py` → `http://localhost:8080`. Everything (fonts, photos, CSS,
> JavaScript and the database) is embedded in that one file, so it works with
> no internet connection and no build step.

---

## What's in it

| View | What you can do |
| --- | --- |
| **Home** | Hero collage, live stats, five exam tiles, recent files, how-it-works story, shortcuts |
| **Exams** | Choose one of the 5 requested exam shelves (plus 2 Class 10 shelves from the repo DB), see paper counts, jump to filtered papers |
| **Papers** | Search, filter by exam / year / subject / document type, sort, 4 toggle chips, pagination, "Surprise me", open any record |
| **Paper drawer** | Full metadata (exam, year, subject, session, type, provenance, duration, pattern), illustrative sheet preview, topics, **Open official file**, **Download**, **Copy link**, **Save**, **Mark solved**, related papers, Previous / Next paper navigation |
| **Practice** | Answer questions, get instant explanations, score tracking, filter by exam / subject |
| **My desk** | Saved & solved papers, coverage bars per exam, recently opened, private notes, clear data |
| **Database** | See exactly where the data came from, connect the live FastAPI backend, sign in as admin, add a paper locally or to the API, export / import your data as JSON |

Everything interactive is a real button: hash routing (back/forward works), filter
chips, pagination, drawer, bookmarks, solved marks, quiz, notes, export/import.
Saved papers, solved marks, recent files, notes and locally added papers persist
in `localStorage` (with an in-memory fallback for sandboxed iframes).

---

## The database

The repository you pointed at —
[Upstream backend reference](https://github.com/yeahhthaarthh/edusphere-backend) (source of the SQL seed) —
contains `seed_data.sql`. I parsed it with SQLite into JSON and **bundled every
row** into the site:

- **30 papers** verbatim (`papers` table): exam, year, subject, session, title,
  description, source URL, filename, download count.
- **2 questions** verbatim (`mock_tests` table): question, four options, correct
  option, explanation — these appear in the Practice view labelled
  "FROM seed_data.sql".

Those 30 rows alone are thin on real PYQs for the five exams you named, so I
added **107 curated records** built from official / verified sources, for a
total of **137 papers**:

| Exam | Papers |
| --- | --- |
| ISC Class 12 | 16 |
| CBSE Class 12 | 58 |
| JEE Main | 14 |
| JEE Advanced | 30 |
| NEET UG | 10 |
| CBSE Class 10 *(also in the repo DB)* | 7 |
| ICSE Class 10 *(also in the repo DB)* | 2 |

**Where the curated links come from** (all checked 2026-11-03):

- **JEE Advanced** — `jeeadv.ac.in/archive.html` → direct official
  `past_qps/{year}_{1|2}[_English|_Hindi].pdf` files, 2014–2025.
- **CBSE Class 12** — `cbse.gov.in/cbsenew/question-paper.html` → official
  2022–2025 Class XII PDFs and ZIP bundles, subject-wise. ZIPs usually contain
  several paper sets.
- **JEE Main** — `jeemain.nta.nic.in/sitemap/` → 9 official shift-wise
  question-paper PDFs on the NTA CDN, plus the official document/archive pages.
- **NEET UG** — official NTA archive (`neet.nta.nic.in`) plus the verified
  year-wise collections already allowlisted in the repo's `neet_discovery.py`
  (ExamGOAL, PracBee, AglaSem) and published 2024 code-wise paper indexes.
- **ISC Class 12** — CISCE specimen-paper pages (also in the repo's seed data),
  the CISCE publications page, and AglaSem's ISC PYQ index as a mirror.

Every record carries a provenance badge: `seed_data.sql`, `official`, `verified`,
`live` or `local`, and a format badge: `PDF`, `ZIP BUNDLE` or `ARCHIVE PAGE`.
Of 123 unique source URLs, **111 returned HTTP 200** when checked on
2026-11-03. Eight returned 403 because those sites (`cisce.org`, AglaSem,
CollegeDunia, Aakash) block automated/non-Indian requests — they normally open
fine in a browser in India. Four NCERT textbook PDFs that came verbatim from
`seed_data.sql` did not respond at build time; those records carry a
**"Link unchecked"** badge and an explanatory note rather than being silently
presented as working. Archive-page records are explicitly labelled so nobody
mistakes a portal link for a direct PDF.

Ten extra **practice questions** are included for the quiz so all five exams
have something to answer; they are clearly marked *"ILLUSTRATIVE PRACTICE ·
NOT AN OFFICIAL PAPER"* and are never presented as real PYQs.

---

## Connecting the live FastAPI backend

The uploaded `app.js` used `API_BASE = http://127.0.0.1:8000`. That integration
is kept and expanded on the **Database** page:

1. Start the backend: `uvicorn app:app --host 0.0.0.0 --port 8000`.
2. In **Database → Live backend**, enter the API base URL and press
   **Connect & sync**. The site calls `GET /api/papers?limit=500` and
   `GET /api/session`, then merges live rows into the shelf (`live-*` IDs).
3. **Admin sign-in** posts to `POST /api/auth/login`. When signed in, the
   **Add a paper locally** form posts multipart data to
   `POST /api/admin/papers` instead of storing it in the browser.
4. Live PDFs open through `GET /api/papers/{id}/file`.

For this to work cross-origin, set the backend's `CORS_ORIGINS` to the exact
origin serving this page, use `credentials: "include"`, and set
`COOKIE_SECURE=true` on HTTPS. If the backend is unreachable the site silently
keeps using the bundled database — it never breaks.

---

## File layout

```
edusphere-site/
├── index.html                 ← THE DELIVERABLE (self-contained, ~1.5 MB)
├── README.md                  ← this file
├── serve.py                   ← optional static server
├── build.py                   ← inlines src/ into index.html
├── build_data.py              ← builds archive.json from seed_data.sql + official links
├── validate.py                ← headless Chromium smoke test + screenshots
├── screenshots/               ← verification screenshots
└── src/
    ├── index.template.html    ← markup
    ├── styles.css             ← theme
    ├── tears.css              ← generated torn-edge clip-paths
    ├── app.js                 ← all interactions
    ├── assets/                ← 3 generated photos + 3 embedded woff2 fonts
    └── data/
        ├── repo-seed.json     ← 30 papers + 2 questions from seed_data.sql
        ├── cbse-links.json    ← official CBSE XII file links
        ├── jeemain-links.json ← official JEE Main shift PDFs
        └── archive.json       ← final 137-paper / 12-question dataset
```

**Rebuild after editing source:**

```bash
python3 build_data.py   # only if the data sources change
python3 build.py        # regenerate index.html
```

Note: `build_data.py` reads `src/data/*.json`, which are committed here, so it
does not need network access to rebuild the dataset.

---

## Verification

Headless Chromium (`validate.py`) exercised: home, exams, papers, exam-chip
filtering, search, paper drawer, save → dashboard, quiz answer + explanation,
database view, mobile navigation. **0 JavaScript errors**; all 137 papers and
12 questions load; desktop (1440×950) and mobile (390×844) screenshots are in
`screenshots/`.

### Small caveats

- The in-app preview iframe is sandboxed: `target="_blank"` links, downloads
  and `localStorage` may be restricted there. Opening `index.html` in a normal
  browser (or via `serve.py`) gives the full experience. A **Copy link** button
  is provided in every paper drawer for that reason.
- ZIP records download a bundle of paper sets, not a single PDF.
- Question papers belong to their respective boards/examining bodies; always
  verify against the official source.
