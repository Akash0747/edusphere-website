"""Apply the high-confidence fixes described in REVIEW.md to app.py.

Run from anywhere; the target path is /home/user/edusphere-backend/app.py.
Every replacement is asserted to match exactly once, so the script fails
loudly if the upstream file has changed.

    python3 apply_fixes.py            # apply (prints a summary)
    python3 apply_fixes.py --check    # verify only, do not write
"""

import sys
from pathlib import Path

TARGET = Path("/home/user/edusphere-backend/app.py")

FIXES = []


def fix(name, old, new):
    FIXES.append((name, old, new))


# 1. Deduplicate imports; add lifespan helper import.
fix(
    "clean imports",
    '''import httpx
from fastapi.responses import StreamingResponse, RedirectResponse
from urllib.parse import urlparse
import os
import re
import time
import uuid
import hashlib
import hmac
import secrets
import os
from urllib.parse import urlparse
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from cbse_discovery import (
    discover_cbse_papers,
    sync_cbse_papers
)
from cbse_sample_discovery import (
    discover_sample_papers,
    sync_sample_papers
)
from jee_main_discovery import (
    discover_jee_main_papers,
    sync_jee_main_papers
)
from jee_advanced_discovery import (
    discover_jee_advanced_papers,
    sync_jee_advanced_papers
)
from neet_discovery import discover_neet_papers, sync_neet_papers
from pathlib import Path
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from supabase import create_client
from fastapi import FastAPI, Request, Response, HTTPException, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form, File, UploadFile
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str
''',
    '''import hashlib
import hmac
import os
import re
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row
from supabase import create_client
from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from cbse_discovery import discover_cbse_papers, sync_cbse_papers
from cbse_sample_discovery import discover_sample_papers, sync_sample_papers
from jee_main_discovery import discover_jee_main_papers, sync_jee_main_papers
from jee_advanced_discovery import (
    discover_jee_advanced_papers,
    sync_jee_advanced_papers,
)
from neet_discovery import discover_neet_papers, sync_neet_papers


class LoginRequest(BaseModel):
    email: str
    password: str
''',
)

# 2. Move init_db() off import time; make the Netlify wildcard opt-in.
fix(
    "startup lifespan + CORS default",
    '''app = FastAPI(title="EduSphere Question Paper Archive API", version="2.0.0")

cors_env = os.getenv(
    "CORS_ORIGINS",
    "https://souray.netlify.app,http://localhost:3000,http://127.0.0.1:3000",
)
allowed_origins = [x.strip() for x in cors_env.split(",") if x.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\\.netlify\\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
''',
    '''@asynccontextmanager
async def lifespan(_: FastAPI):
    # Bootstrap at startup, not at import time: importing this module for
    # tests (or via `from app import connect`) no longer needs a live DB.
    init_db()
    yield


app = FastAPI(
    title="EduSphere Question Paper Archive API",
    version="2.0.0",
    lifespan=lifespan,
)

cors_env = os.getenv(
    "CORS_ORIGINS",
    "https://souray.netlify.app,http://localhost:3000,http://127.0.0.1:3000",
)
allowed_origins = [x.strip() for x in cors_env.split(",") if x.strip()]

# A wildcard here means ANY Netlify site can make credentialed requests as a
# signed-in admin. Opt in explicitly for deploy previews instead.
allow_netlify_previews = (
    os.getenv("CORS_ALLOW_NETLIFY_PREVIEWS", "").lower() == "true"
)
allow_origin_regex = (
    r"https://.*\\.netlify\\.app" if allow_netlify_previews else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
''',
)

# 3. "false" is a truthy Python string; supabase-py turns any truthy upsert
#    value into an x-upsert header. Omit it entirely.
fix(
    "remove accidental x-upsert header",
    '''                "cache-control": "3600",
                "upsert": "false",
            },''',
    '''                "cache-control": "3600",
            },''',
)

# 4. Honour ?download=1 for Supabase-hosted PDFs.
fix(
    "public_pdf_url download option",
    '''def public_pdf_url(object_path: str):
    try:
        return storage().storage.from_(SUPABASE_BUCKET).get_public_url(object_path)
    except Exception as exc:
        raise HTTPException(502, f"Could not create PDF link: {str(exc)[:200]}")
''',
    '''def public_pdf_url(object_path: str, download_name: Optional[str] = None):
    try:
        options = {"download": download_name} if download_name else None
        return storage().storage.from_(SUPABASE_BUCKET).get_public_url(
            object_path, options
        )
    except Exception as exc:
        raise HTTPException(502, f"Could not create PDF link: {str(exc)[:200]}")
''',
)

# 5. CSRF check for cookie-authenticated admin writes.
fix(
    "CSRF origin check in require_admin",
    '''def require_admin(request: Request):
    admin = current_admin(request)

    if not admin or not admin["is_admin"]:
        raise HTTPException(401, "Admin sign-in required")

    return admin
''',
    '''def require_admin(request: Request):
    admin = current_admin(request)

    if not admin or not admin["is_admin"]:
        raise HTTPException(401, "Admin sign-in required")

    # CORS stops other sites from READING responses, but simple form POSTs
    # still execute. With SameSite=None cookies, check Origin explicitly.
    # Requests without Origin are non-browser clients (curl, server jobs).
    origin = request.headers.get("origin")
    if origin and request.method not in ("GET", "HEAD", "OPTIONS"):
        origin_ok = origin in allowed_origins or (
            allow_origin_regex is not None
            and re.fullmatch(allow_origin_regex, origin) is not None
        )
        if not origin_ok:
            raise HTTPException(403, "Cross-origin admin request rejected")

    return admin
''',
)

# 6. Serialize bootstrap across workers to avoid duplicate seeding.
fix(
    "advisory lock for init_db",
    '''    with connect() as db:
        existing = db.execute(
            "SELECT id FROM admins WHERE email = %s",
''',
    '''    with connect() as db:
        # Serialize startup across uvicorn workers so parallel boots cannot
        # both seed the papers table.
        db.execute("SELECT pg_advisory_xact_lock(9172026)")

        existing = db.execute(
            "SELECT id FROM admins WHERE email = %s",
''',
)

fix(
    "remove import-time init_db()",
    '''# ---------- Startup ----------
init_db()
''',
    '''# ---------- Startup ----------
# init_db() runs from the lifespan handler above (startup), not at import.
''',
)

# 7. Use the download flag on the file endpoint.
fix(
    "honour download=1",
    '''    if row["stored_name"] and row["stored_name"] != "EXTERNAL_URL":
        return RedirectResponse(
            public_pdf_url(row["stored_name"]),
            status_code=302,
        )
''',
    '''    if row["stored_name"] and row["stored_name"] != "EXTERNAL_URL":
        # Supabase Storage sets Content-Disposition: attachment when the
        # download query option is present.
        download_name = (
            (row["file_name"] or "paper.pdf") if download else None
        )
        return RedirectResponse(
            public_pdf_url(row["stored_name"], download_name),
            status_code=302,
        )
''',
)

# 8. Admin aliases for stats/dashboard really require a session.
fix(
    "stats: public decorators only",
    '''@app.get("/api/stats")
@app.get("/api/stats/")
@app.get("/api/admin/stats")
@app.get("/api/admin/stats/")
def stats():''',
    '''@app.get("/api/stats")
@app.get("/api/stats/")
def stats():''',
)

fix(
    "stats: NULL-safe withFile count",
    "                       WHEN (stored_name <> '' OR source_url <> '')",
    "                       WHEN (COALESCE(stored_name, '') <> ''\n"
    "                            OR COALESCE(source_url, '') <> '')",
)

fix(
    "stats: authenticated admin aliases",
    '''    return [
        {
            "exam": row["exam"],
            "total": row["total"],
            "withFile": row["withFile"],
        }
        for row in rows
    ]


@app.get("/api/dashboard")''',
    '''    return [
        {
            "exam": row["exam"],
            "total": row["total"],
            "withFile": row["withFile"],
        }
        for row in rows
    ]


@app.get("/api/admin/stats")
@app.get("/api/admin/stats/")
def admin_stats(request: Request):
    require_admin(request)
    return stats()


@app.get("/api/dashboard")''',
)

fix(
    "dashboard: public decorators only",
    '''@app.get("/api/dashboard")
@app.get("/api/dashboard/")
@app.get("/api/admin/dashboard")
@app.get("/api/admin/dashboard/")
def dashboard():''',
    '''@app.get("/api/dashboard")
@app.get("/api/dashboard/")
def dashboard():''',
)

fix(
    "dashboard: NULL-safe withFile count",
    '''               WHERE (stored_name <> '' OR source_url <> '')"''',
    '''               WHERE (COALESCE(stored_name, '') <> ''
                      OR COALESCE(source_url, '') <> '')"''',
)

fix(
    "dashboard: authenticated admin aliases",
    '''    return {
        "total": total,
        "withFile": with_file,
        "downloads": downloads,
    }


@app.get("/api/mock-tests")''',
    '''    return {
        "total": total,
        "withFile": with_file,
        "downloads": downloads,
    }


@app.get("/api/admin/dashboard")
@app.get("/api/admin/dashboard/")
def admin_dashboard(request: Request):
    require_admin(request)
    return dashboard()


@app.get("/api/mock-tests")''',
)

# 9. Remove the shadowed duplicate handler (OpenAPI emits a duplicate ID
#    warning and the second function is unreachable).
fix(
    "remove duplicate sample-discovery-test",
    '''    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
@app.get("/api/admin/sample-discovery-test")
async def sample_discovery_test(request: Request):
    require_admin(request)

    try:
        papers = discover_sample_papers()
        return {
            "success": True,
            "total_found": len(papers),
            "sample": papers[:10]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/admin/sample-papers-sync")''',
    '''    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/admin/sample-papers-sync")''',
)

# 10. Self-import is unnecessary and can re-import app.py under another name.
fix(
    "remove self-import in JEE Advanced view",
    '''    from app import connect

    with connect() as db:
        with db.cursor() as cur:''',
    '''    with connect() as db:
        with db.cursor() as cur:''',
)

# 11. Don't orphan a freshly uploaded PDF when removeFile=true is also sent.
fix(
    "track discarded upload",
    '''    old_path = ""
    replacement_path = ""

    with connect() as db:''',
    '''    old_path = ""
    replacement_path = ""
    discarded_upload = ""

    with connect() as db:''',
)

fix(
    "handle removeFile + upload in same request",
    '''        if str(form.get("removeFile", "")).lower() == "true":
            filename, stored, size = "", "", 0
            replacement_path = ""
''',
    '''        if str(form.get("removeFile", "")).lower() == "true":
            # A file uploaded in this same request must not be orphaned.
            discarded_upload = replacement_path
            filename, stored, size = "", "", 0
            replacement_path = ""
''',
)

fix(
    "delete discarded upload",
    '''    if old_path and old_path != replacement_path:
        delete_stored_pdf(old_path)

    return result
''',
    '''    if old_path and old_path != replacement_path:
        delete_stored_pdf(old_path)

    if discarded_upload:
        delete_stored_pdf(discarded_upload)

    return result
''',
)

# 12. NEET discovery/sync were the only /api/admin/* routes with no auth.
fix(
    "protect NEET discovery",
    '''@app.get("/api/admin/neet-discovery-test")
def neet_discovery_test():
    records = discover_neet_papers()
''',
    '''@app.get("/api/admin/neet-discovery-test")
def neet_discovery_test(request: Request):
    require_admin(request)

    records = discover_neet_papers()
''',
)

fix(
    "protect NEET sync",
    '''@app.post("/api/admin/neet-sync")
def neet_sync():
    return sync_neet_papers()
''',
    '''@app.post("/api/admin/neet-sync")
def neet_sync(request: Request):
    require_admin(request)
    return sync_neet_papers()
''',
)


def main():
    source = TARGET.read_text()
    for name, old, new in FIXES:
        count = source.count(old)
        if count != 1:
            raise SystemExit(
                f"FAILED [{name}]: expected 1 match, found {count}. "
                "Upstream app.py may have changed."
            )
        source = source.replace(old, new, 1)
        print(f"  ok  {name}")

    compile(source, str(TARGET), "exec")  # syntax check
    if "--check" in sys.argv:
        print("\nCheck only: all replacements match and result compiles.")
        return

    TARGET.write_text(source)
    print(f"\nWrote {len(FIXES)} fixes to {TARGET}")


if __name__ == "__main__":
    main()
