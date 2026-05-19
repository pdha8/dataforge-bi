"""
Mini-proxy local pour TestSprite — forwarde localhost:8000 vers le backend Render.

Permet de pointer TestSprite (qui exige un port localhost) vers la prod Render
sans installer mitmproxy / nginx. Pas de TLS local (TestSprite tape en HTTP).

Usage :
    python dev_proxy_render.py
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import requests

UPSTREAM = "https://dataforge-api.onrender.com"
PORT = 8000

# Headers qu'on ne réémet jamais vers l'upstream / le client
HOP_BY_HOP = {
    "connection", "keep-alive", "transfer-encoding",
    "te", "trailer", "upgrade", "proxy-authorization", "proxy-authenticate",
    "host", "content-length",
}


class ProxyHandler(BaseHTTPRequestHandler):
    def _forward(self, method: str) -> None:
        url = f"{UPSTREAM}{self.path}"
        headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in HOP_BY_HOP
        }

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None

        try:
            r = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                allow_redirects=False,
                timeout=120,
            )
        except requests.RequestException as exc:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Upstream error: {exc}".encode("utf-8"))
            return

        self.send_response(r.status_code)
        for k, v in r.headers.items():
            if k.lower() in HOP_BY_HOP or k.lower() == "content-encoding":
                continue
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(r.content)))
        self.end_headers()
        self.wfile.write(r.content)

    def log_message(self, format: str, *args) -> None:
        # Log lisible (sinon BaseHTTPRequestHandler crache vers stderr en couleurs).
        print(f"[{self.command}] {self.path} -> {args[1] if len(args) > 1 else '?'}")

    def do_GET(self):    self._forward("GET")
    def do_POST(self):   self._forward("POST")
    def do_PUT(self):    self._forward("PUT")
    def do_PATCH(self):  self._forward("PATCH")
    def do_DELETE(self): self._forward("DELETE")
    def do_OPTIONS(self): self._forward("OPTIONS")
    def do_HEAD(self):   self._forward("HEAD")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), ProxyHandler)
    print(f"Proxy ready: http://localhost:{PORT}  ->  {UPSTREAM}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
