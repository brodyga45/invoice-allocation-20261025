"""Exercise the actual frozen executable from a different Unicode working folder."""
import csv
import hashlib
import io
import json
import queue
import re
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
exe = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix="Invoice allocation caf\u00e9 ") as work:
    process = subprocess.Popen([str(exe), "--no-browser"], cwd=work, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    output = queue.Queue()
    threading.Thread(target=lambda: [output.put(line) for line in process.stdout], daemon=True).start()
    try:
        line = output.get(timeout=30)
        match = re.search(r"http://127\.0\.0\.1:\d+", line)
        if not match:
            raise RuntimeError("Frozen app did not print its local address: " + line)
        url = match.group()
        with urllib.request.urlopen(url, timeout=10) as response:
            html = response.read().decode()
        token = re.search(r'name="local-token" content="([^"]+)"', html).group(1)
        for asset in ("/app.js", "/viewer.mjs", "/vendor/pdf.mjs", "/vendor/pdf.worker.mjs"):
            with urllib.request.urlopen(url + asset, timeout=10) as response:
                assert response.read() == (ROOT / "web" / asset.lstrip("/")).read_bytes(), asset
        def post(path, data):
            request = urllib.request.Request(url + path, json.dumps(data).encode(),
                {"Content-Type": "application/json", "X-Local-Token": token})
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.read()
        batch = json.loads(post("/api/example", {}))
        assert len(batch["files"]) == 4
        assert batch["files"][0]["matches"] == ["E001"]
        assert set(batch["files"][1]["matches"]) == {"E002", "E003"}
        assert batch["files"][2]["matches"] == []
        assert not any(row["error"] for row in batch["files"])
        common = {"batch_id": batch["batch_id"], "file_id": "4", "employee_id": "E004"}
        source = post("/api/source", common)
        preview = post("/api/preview", common)
        assert "\u041c\u0438\u043b\u0430 \u041f\u0435\u0442\u0440\u043e\u0432\u0438\u045b" in PdfReader(io.BytesIO(preview)).pages[0].extract_text()
        assert float(PdfReader(io.BytesIO(preview)).pages[0].mediabox.height) > float(PdfReader(io.BytesIO(source)).pages[0].mediabox.height)
        try:
            post("/api/export", {"batch_id": batch["batch_id"], "selections": [
                {"file_id": "4", "employee_id": "E004", "approved": False}]})
            raise AssertionError("Unapproved export accepted")
        except urllib.error.HTTPError as error:
            assert error.code == 400
        exported = post("/api/export", {"batch_id": batch["batch_id"], "selections": [
            {"file_id": "4", "employee_id": "E004", "approved": True}]})
        with zipfile.ZipFile(io.BytesIO(exported)) as archive:
            assert archive.testzip() is None
            rows = list(csv.DictReader(io.StringIO(archive.read("allocation-report.csv").decode("utf-8-sig"))))
            assert len(rows) == 1 and rows[0]["employee_id"] == "E004"
            assert rows[0]["source_sha256"] == hashlib.sha256(source).hexdigest()
            assert rows[0]["copy_sha256"] == hashlib.sha256(archive.read(rows[0]["accounting_copy"])).hexdigest()
            assert rows[0]["location"] == "\u0411\u0435\u043e\u0433\u0440\u0430\u0434"
        assert post("/api/source", common) == source
        assert json.loads(post("/api/clear", {}))["cleared"]
        try:
            post("/api/source", common)
            raise AssertionError("Cleared batch accepted")
        except urllib.error.HTTPError as error:
            assert error.code == 400
        receipt = {"frozen_executable": exe.name, "platform": sys.platform,
                   "result": "passed", "separate_unicode_working_directory": True,
                   "bundled_assets_byte_equal": True, "fictional_files": 4,
                   "Cyrillic_preview_and_export": True, "unapproved_and_stale_exports_rejected": True,
                   "source_bytes_and_report_hashes_verified": True,
                   "browser_UI_and_customer_installation": "not tested by this script"}
        (ROOT / "portable-check.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt))
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(timeout=10)
