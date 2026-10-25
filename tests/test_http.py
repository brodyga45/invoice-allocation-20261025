import base64
import io
import json
import socket
import sys
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import LocalServer
from allocation import EXAMPLE_STAFF, example_files


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LocalServer(("127.0.0.1", 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def post(self, path, body, token=True, origin=None):
        headers = {"Content-Type": "application/json"}
        if token: headers["X-Local-Token"] = self.server.token
        if origin: headers["Origin"] = origin
        request = urllib.request.Request(self.url + path, json.dumps(body).encode(), headers)
        return urllib.request.urlopen(request, timeout=10)

    def test_static_assets_local_and_no_arbitrary_file(self):
        for path, mime in [("/", "text/html"), ("/viewer.mjs", "text/javascript"),
                           ("/vendor/pdf.worker.mjs", "text/javascript")]:
            with urllib.request.urlopen(self.url + path) as r:
                self.assertIn(mime, r.headers["Content-Type"])
                self.assertEqual(r.headers["Cache-Control"], "no-store")
                self.assertGreater(len(r.read()), 10)
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(self.url + "/../app.py")

    def test_idle_browser_preconnection_does_not_block_other_requests(self):
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=3):
            with urllib.request.urlopen(self.url + "/", timeout=3) as response:
                self.assertIn(b"Invoice Allocation", response.read())

    def test_missing_token_and_cross_origin_blocked(self):
        for args in [{"token": False}, {"origin": "https://other.example"}]:
            with self.assertRaises(urllib.error.HTTPError) as e:
                self.post("/api/example", {}, **args)
            self.assertEqual(e.exception.code, 403)

    def test_load_source_preview_export_and_clear(self):
        source = example_files()[0][1]
        with self.post("/api/load", {"csv": EXAMPLE_STAFF, "files": [
                {"name": "invoice.pdf", "data": base64.b64encode(source).decode()}]}) as r:
            batch = json.load(r)
        common = {"batch_id": batch["batch_id"], "file_id": "1", "employee_id": "E001"}
        with self.post("/api/source", common) as r: self.assertEqual(r.read(), source)
        with self.post("/api/preview", common) as r:
            self.assertEqual(r.headers["Content-Type"], "application/pdf")
            self.assertTrue(r.read().startswith(b"%PDF-"))
        with self.post("/api/export", {"batch_id": batch["batch_id"], "selections": [
                {"file_id": "1", "employee_id": "E001", "approved": True}]}) as r:
            self.assertEqual(r.headers["Content-Type"], "application/zip")
            with zipfile.ZipFile(io.BytesIO(r.read())) as z: self.assertIsNone(z.testzip())
        with self.post("/api/clear", {}) as r: self.assertTrue(json.load(r)["cleared"])
        with self.assertRaises(urllib.error.HTTPError): self.post("/api/source", common)

    def test_failed_replacement_discards_old_batch(self):
        with self.post("/api/example", {}) as r: old = json.load(r)
        with self.assertRaises(urllib.error.HTTPError): self.post("/api/load", {"csv": "bad", "files": []})
        with self.assertRaises(urllib.error.HTTPError):
            self.post("/api/source", {"batch_id": old["batch_id"], "file_id": "1"})


if __name__ == "__main__": unittest.main()
