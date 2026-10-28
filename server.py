"""TasteDesk web demo: stdlib HTTP server. Run: python3 server.py  (PORT env, default 8080)."""
import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import agent

HTML = open(os.path.join(os.path.dirname(__file__), "static", "index.html"), "rb").read()


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, HTML, "text/html; charset=utf-8")
        if self.path == "/health":
            return self._send(200, b'{"ok":true}')
        self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        if self.path != "/api/chat":
            return self._send(404, b'{"error":"not found"}')
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
            msg = str(data.get("message", ""))[:500]
            out = agent.run(msg, data.get("mode", "concierge"), str(data.get("city") or "Austin, TX")[:80], str(data.get("business", ""))[:120])
            self._send(200, json.dumps(out).encode())
        except Exception as e:
            self._send(500, json.dumps({"error": str(e)}).encode())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"TasteDesk on http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
