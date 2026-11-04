"""Static-ish audit of the EduSphere FastAPI app.

Imports app.py with a stubbed psycopg connection (so no real database is
needed), then reports every registered route and whether its handler calls
require_admin(). Also flags duplicate paths.

Usage:
    DATABASE_URL=postgresql://stub/stub \
    PYTHONPATH=/path/to/deps:/home/user/edusphere-backend \
    python audit_routes.py
"""

import inspect
import os
import sys
from collections import Counter

os.environ.setdefault("DATABASE_URL", "postgresql://stub/stub")

# --- stub psycopg.connect before importing app ---
import psycopg


class FakeResult:
    def fetchone(self):
        return {"id": 1, "c": 1, "n": 1}

    def fetchall(self):
        return []


class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def executemany(self, *args, **kwargs):
        return None


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, *args, **kwargs):
        return FakeResult()

    def cursor(self):
        return FakeCursor()


psycopg.connect = lambda *args, **kwargs: FakeConnection()

sys.path.insert(0, "/home/user/edusphere-backend")
import app as target  # noqa: E402

routes = [r for r in target.app.routes if getattr(r, "methods", None)]
# Duplicates matter only when both the HTTP method AND the path match.
counts = Counter((m, r.path) for r in routes for m in r.methods)

print(f"{'METHOD':<8} {'PATH':<58} {'AUTH':<12} HANDLER")
print("-" * 110)
for route in routes:
    method = ",".join(sorted(route.methods - {"HEAD", "OPTIONS"}))
    source = ""
    try:
        source = inspect.getsource(route.endpoint)
    except (OSError, TypeError):
        pass
    auth = "yes" if "require_admin(" in source else "NO"
    print(f"{method:<8} {route.path:<58} {auth:<12} {route.endpoint.__name__}")

print("\nDuplicate (method, path) pairs (first registered handler wins):")
for (method, path), n in counts.items():
    if n > 1:
        handlers = [
            r.endpoint.__name__
            for r in routes
            if r.path == path and method in r.methods
        ]
        print(f"  {method} {path}: {n} registrations -> {handlers}")

print("\nOpenAPI operation IDs with duplicates:")
spec = target.app.openapi()
ops = [
    (p, m, o.get("operationId"))
    for p, item in spec["paths"].items()
    for m, o in item.items()
    if isinstance(o, dict)
]
seen = Counter(op[2] for op in ops)
for opid, n in seen.items():
    if n > 1:
        print(f"  {opid}: {n}")
