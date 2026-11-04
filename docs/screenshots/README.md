# Screenshots

All images are JPEGs captured from the built website with a headless Chromium browser at desktop (1440 × 950) and mobile widths. They are used in the root [`README.md`](../../README.md) gallery and in [`PROJECT_REPORT.md`](../PROJECT_REPORT.md).

| File | View | Notes |
| --- | --- | --- |
| `00-hero-zoom.jpg` | Hero detail | Close-up of the torn-paper display type |
| `01-home.jpg` | Home | Hero, exam tiles, featured papers |
| `02-exams.jpg` | Exams | All shelves with counts |
| `03-papers.jpg` | Papers | Filters + 12 cards per page |
| `04-drawer.jpg` | Paper drawer | Metadata and action buttons |
| `05-dashboard.jpg` | My Desk | Saved / solved / notes |
| `06-practice.jpg` | Practice | Quiz with explanation |
| `07-connect.jpg` | Connect | Optional API base + admin login |
| `08-mobile-home.jpg` | Mobile home | Responsive layout |
| `09-mobile-papers.jpg` | Mobile papers | Responsive filters/cards |
| `10-mobile-hero.jpg` | Mobile hero | Early version (before contrast fix) |
| `11-hero-fixed.jpg` | Hero fix | Final contrast treatment |
| `12-mobile-fixed.jpg` | Mobile fix | Translucent torn panel + light type |
| `13-vercel-live.jpg` | **Live site** | Captured from https://edusphere-paper-archive.vercel.app/ |

`10-mobile-hero.jpg` is kept deliberately: it documents the contrast problem found during testing and the fix visible in `12-mobile-fixed.jpg` — a nice detail for a project presentation.

To regenerate: `cd frontend && python3 validate.py` (requires Playwright + Chromium).
