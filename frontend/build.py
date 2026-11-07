"""Inline all CSS, JS, fonts, images and data into a single index.html.

The resulting file is fully self-contained: it needs no network, no server and
no external assets, so it also renders inside a sandboxed preview iframe.

Run:  python3 build.py
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
SRC = ROOT / "src"
ASSETS = SRC / "assets"


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


fonts = "\n".join(
    [
        "@font-face{font-family:'Anton';src:url(data:font/woff2;base64," + b64(ASSETS / "anton-latin.woff2") + ") format('woff2');font-weight:400;font-display:swap;}",
        "@font-face{font-family:'DM Mono';src:url(data:font/woff2;base64," + b64(ASSETS / "dmmono-latin.woff2") + ") format('woff2');font-weight:400;font-display:swap;}",
        "@font-face{font-family:'Libre Baskerville';src:url(data:font/woff2;base64," + b64(ASSETS / "baskerville-italic-latin.woff2") + ") format('woff2');font-style:italic;font-weight:400;font-display:swap;}",
    ]
)

images = ":root{\n" + "\n".join(
    f"  --img-{name}: url(data:image/jpeg;base64,{b64(ASSETS / (name + '.jpg'))});"
    for name in ("cinema", "street", "desk")
) + "\n}\n"

head_style = "\n".join(
    [fonts, images, (SRC / "tears.css").read_text(), (SRC / "styles.css").read_text()]
)

archive = json.loads((SRC / "data" / "archive.json").read_text())
data_json = json.dumps(archive, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
inline_data = "window.__ARCHIVE__ = " + data_json + ";"

script = (SRC / "app.js").read_text().replace("</script", "<\\/script")

# The designer seal is inlined (no network request) and reused as the tab favicon.
logo_svg = (ASSETS / "edusphere-logo.svg").read_text().strip()
logo_favicon = "data:image/svg+xml," + quote(logo_svg, safe="")

html = (SRC / "index.template.html").read_text()
html = html.replace("{{HEADSTYLE}}", head_style)
html = html.replace("{{INLINE_DATA}}", inline_data)
html = html.replace("{{INLINE_SCRIPT}}", script)
html = html.replace("{{LOGO}}", logo_svg)
html = html.replace("{{FAVICON}}", logo_favicon)

out = ROOT / "index.html"
out.write_text(html)
print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
print(f"  {len(archive['papers'])} papers · {len(archive['questions'])} questions · {len(archive['exams'])} exam shelves")
