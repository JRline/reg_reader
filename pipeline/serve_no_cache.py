#!/usr/bin/env python3
"""
Same as `python3 -m http.server`, except every response tells the browser not to cache
it. Plain http.server sends no Cache-Control header at all, which browsers then cache
heuristically — observed to silently serve stale feed.json/style.css/app.js even across
a hard reload during this project's iterative pipeline development. Use this instead
whenever you're actively re-running the pipeline and viewing the result locally.

Usage: python3 serve_no_cache.py [port]  (default 8877)
"""
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def do_GET(self):
        # SimpleHTTPRequestHandler honors If-Modified-Since/If-None-Match and returns a
        # bare 304 when they match — and a 304 has no body, so the browser reuses its
        # cached copy regardless of the Cache-Control header above. Strip the
        # conditional headers before that logic runs, so every request gets a real 200.
        for h in ("If-Modified-Since", "If-None-Match"):
            if h in self.headers:
                del self.headers[h]
        super().do_GET()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8877
    HTTPServer(("", port), NoCacheHandler).serve_forever()
