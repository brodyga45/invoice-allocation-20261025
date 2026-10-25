"""Local browser UI. Bind only to loopback; never run as a hosted service."""
import argparse
import base64
import hmac
import json
import mimetypes
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from allocation import Batch, EXAMPLE_STAFF, MAX_TOTAL, ROOT, example_files


class LocalServer(ThreadingHTTPServer):
    def __init__(self, address):
        super().__init__(address, Handler)
        self.token = secrets.token_urlsafe(32)
        self.batch = None
        self.batch_lock = threading.RLock()


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def log_message(self, *_):
        pass  # Do not log employee names, files, request bodies, or tokens.

    def allowed(self):
        port = self.server.server_port
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def send(self, body, kind="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; worker-src 'self' blob:; style-src 'self'; frame-src blob:; object-src 'none'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if not self.allowed():
            return self.send(b'{"error":"Wrong host"}', status=403)
        paths = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                 "/style.css": ("style.css", "text/css; charset=utf-8")}
        paths.update({"/" + p.relative_to(ROOT / "web").as_posix():
                      (p.relative_to(ROOT / "web").as_posix(),
                       "text/javascript" if p.suffix == ".mjs" else mimetypes.guess_type(p.name)[0] or "application/octet-stream")
                      for p in (ROOT / "web").rglob("*") if p.is_file() and p.name != "index.html"})
        if self.path not in paths:
            return self.send(b'{"error":"Not found"}', status=404)
        name, kind = paths[self.path]
        body = (ROOT / "web" / name).read_bytes()
        if name == "index.html":
            body = body.replace(b"__LOCAL_TOKEN__", self.server.token.encode())
        self.send(body, kind)

    def do_POST(self):
        origin = self.headers.get("Origin")
        expected = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
        if not self.allowed() or (origin is not None and origin not in expected) or not hmac.compare_digest(
                self.headers.get("X-Local-Token", ""), self.server.token):
            return self.send(b'{"error":"Only this local app may submit requests"}', status=403)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 35 * 1024 * 1024:
                raise ValueError("Request is too large or empty.")
            body = json.loads(self.rfile.read(size))
            with self.server.batch_lock:
                if self.path == "/api/example":
                    self.server.batch = Batch(EXAMPLE_STAFF, example_files())
                    result = self.server.batch.summary()
                elif self.path == "/api/load":
                    self.server.batch = None
                    files = body.get("files", [])
                    if not isinstance(files, list) or not 1 <= len(files) <= 25:
                        raise ValueError("Choose 1 to 25 PDFs.")
                    decoded = [(f["name"], base64.b64decode(f["data"], validate=True)) for f in files]
                    self.server.batch = Batch(body.get("csv", ""), decoded)
                    result = self.server.batch.summary()
                elif self.path == "/api/clear":
                    self.server.batch = None; result = {"cleared": True}
                elif self.path in ("/api/source", "/api/preview", "/api/export"):
                    batch = self.server.batch
                    if batch is None or body.get("batch_id") != batch.batch_id:
                        raise ValueError("This batch was cleared or replaced. Load it again.")
                    if self.path.endswith("source"):
                        if body.get("file_id") not in batch.files:
                            raise ValueError("Unknown invoice.")
                        return self.send(batch.files[body["file_id"]].data, "application/pdf")
                    if self.path.endswith("preview"):
                        content = batch.make_copy(body.get("file_id"), body.get("employee_id"))
                        return self.send(content, "application/pdf")
                    content = batch.export(body.get("selections"))
                    return self.send(content, "application/zip")
                else:
                    raise ValueError("Unknown operation.")
                self.send(json.dumps(result, ensure_ascii=False).encode())
        except Exception as exc:
            message = str(exc) if isinstance(exc, ValueError) else "Cannot process this batch. No output was returned."
            self.send(json.dumps({"error": message}).encode(), status=400)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local invoice allocation review")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    with LocalServer(("127.0.0.1", args.port)) as server:
        server.timeout = 30
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"Invoice Allocation 0.1.0: {url} (Ctrl+C to close and discard the batch)", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
