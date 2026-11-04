# Assets

Everything here is embedded into `frontend/index.html` by `build.py` as a base64 data URI. The built site therefore makes **zero external requests**.

## Photographs (generated for this project)

| File | Used as |
| --- | --- |
| `cinema.jpg` | Hero backdrop — vintage cinema / queue at night |
| `street.jpg` | Torn collage photo, amber street scene |
| `desk.jpg` | Torn collage photo, study desk / paper texture |

Generated with an image model specifically for this project; no stock photography or third-party assets are required at runtime.

## Fonts (Latin subsets)

| File | CSS family |
| --- | --- |
| `anton-latin.woff2` | `Anton` — heavy condensed display type |
| `dmmono-latin.woff2` | `DM Mono` — eyebrows, labels, metadata |
| `baskerville-italic-latin.woff2` | `Libre Baskerville` italic — pull quotes |

Downloaded from Google Fonts (Chrome user-agent is required to obtain woff2 rather than TTF) and embedded locally so the site works offline.

## Regenerating

If you replace any file, run `cd frontend && python3 build.py`. The build reads the files by path, base64-encodes them and substitutes the `{{...}}` placeholders in `index.template.html`.
