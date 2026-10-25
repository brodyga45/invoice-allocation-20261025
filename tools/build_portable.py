"""Build the existing app without requiring Python on the recipient's machine."""
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
    "--name", "InvoiceAllocation", "--noupx", "--add-data", "assets:assets",
    "--add-data", "web:web", "app.py",
], cwd=ROOT, check=True)
bundle = ROOT / "dist/InvoiceAllocation"
for name in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "QA.md"):
    shutil.copy2(ROOT / name, bundle / name)
licenses = bundle / "licenses"
licenses.mkdir(exist_ok=True)
versions = {}
for name in ("pypdf", "reportlab", "pillow", "charset-normalizer", "pyinstaller"):
    dist = importlib.metadata.distribution(name)
    versions[name] = dist.version
    found = []
    for entry in dist.files or []:
        if any(part.lower().startswith(("license", "copying", "notice")) for part in entry.parts):
            source = Path(dist.locate_file(entry))
            if source.is_file():
                target = licenses / name / Path(*entry.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                found.append(str(entry))
    if not found:
        raise RuntimeError(f"Missing installed license notice: {name}")
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if not python_license.is_file():
    python_license = Path(sys.base_prefix) / "LICENSE"
if not python_license.is_file():
    raise RuntimeError("Missing Python distribution license")
shutil.copy2(python_license, licenses / "Python-LICENSE.txt")
versions["python"] = sys.version
(bundle / "BUILD-VERSIONS.json").write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
(bundle / "START-HERE.txt").write_text(
    "Invoice Allocation 0.1.0 - Windows x64 portable candidate\n\n"
    "1. Extract the entire ZIP to a folder. Keep _internal next to the application.\n"
    "2. Open InvoiceAllocation.exe. Python installation is not required.\n"
    "3. Your browser opens a 127.0.0.1 address. Click Try fictional invoices.\n"
    "4. Review an employee, preview the accounting copy, mark Reviewed, then Save reviewed copies.\n"
    "5. Close the console window to stop the app and discard the in-memory batch.\n\n"
    "This build is unsigned. Use it only if allowed by your computer's software policy.\n"
    "No administrator privileges, firewall changes or security-warning bypass is required or requested.\n"
    "See README.md for supported files, data handling and the taller first-page output format.\n"
    "A successful automated Windows check is not a physical customer-computer installation.\n",
    encoding="utf-8")
print(f"Built {bundle}")
