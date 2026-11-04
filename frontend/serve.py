"""Tiny static server for the EduSphere archive.

    python3 serve.py            # http://0.0.0.0:8080
    python3 serve.py 3000

The site is also fully self-contained: you can simply open index.html directly
in a browser without any server at all.
"""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("port", nargs="?", type=int, default=8080)
    a = ap.parse_args()
    server = ThreadingHTTPServer(("0.0.0.0", a.port), Handler)
    print(f"EduSphere archive → http://0.0.0.0:{a.port} (root: {ROOT})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
