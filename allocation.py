"""Local, review-first accounting copies. No invoice or employment decisions."""
import base64
import csv
import hashlib
import io
import json
import re
import secrets
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont("AllocationSans", str(ROOT / "assets/NotoSans-Regular.ttf")))
MAX_FILE = 12 * 1024 * 1024
MAX_TOTAL = 24 * 1024 * 1024
MAX_PAGES = 20


def normalize(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def read_staff(text):
    if not isinstance(text, str) or len(text.encode("utf-8")) > 2_000_000:
        raise ValueError("Staff CSV must be UTF-8 text, at most 2 MB.")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff"), newline=""))
    required = {"employee_id", "name", "cost_center", "location"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError("CSV needs employee_id,name,cost_center,location headers.")
    staff = {}
    for line, row in enumerate(reader, 2):
        record = {key: (row.get(key) or "").strip() for key in required}
        if None in row or any(not v or len(v) > 160 or any(ord(c) < 32 for c in v) for v in record.values()):
            raise ValueError(f"CSV row {line}: required values must be nonempty, single-line, and at most 160 characters.")
        if record["employee_id"] in staff:
            raise ValueError(f"CSV row {line}: duplicate employee_id.")
        if len(staff) >= 2000:
            raise ValueError("Use at most 2,000 employee rows per batch.")
        staff[record["employee_id"]] = record
    if not staff:
        raise ValueError("Staff CSV has no employee rows.")
    return staff


def load_pdf(data):
    if not isinstance(data, bytes) or not data.startswith(b"%PDF-") or len(data) > MAX_FILE:
        raise ValueError("Use a PDF at most 12 MB.")
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported. Keep the original.")
    if not 1 <= len(reader.pages) <= MAX_PAGES:
        raise ValueError("Use invoices with 1 to 20 pages.")
    root = reader.trailer["/Root"]
    if any(key in root for key in ("/AcroForm", "/Perms", "/OpenAction", "/AA")):
        raise ValueError("Signed, interactive, or action-bearing PDFs are not supported.")
    for page in reader.pages:
        if page.get("/Annots") or page.get("/AA"):
            raise ValueError("Annotated or interactive PDFs are not supported.")
        if float(page.get("/UserUnit", 1)) != 1:
            raise ValueError("Nonstandard PDF units are not supported.")
        w, h = float(page.cropbox.width), float(page.cropbox.height)
        if not 200 <= w <= 2000 or not 200 <= h <= 2000:
            raise ValueError("Unsupported invoice page dimensions.")
    return reader


def candidates(data, staff):
    reader = load_pdf(data)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    haystack = normalize(text)
    ids = [key for key, item in staff.items()
           if re.search(r"(?<!\w)" + re.escape(normalize(item["name"])) + r"(?!\w)", haystack)]
    if not haystack:
        note = "No selectable text. Choose the employee manually; no OCR is performed."
    elif not ids:
        note = "No staff name found. Choose manually after checking the invoice."
    elif len(ids) > 1:
        note = "Several staff rows match. Choose the correct employee ID."
    else:
        note = "One name match proposed. Check the invoice and allocation before approval."
    return ids, note


def accounting_copy(data, employee):
    reader = load_pdf(data)
    source_writer = PdfWriter(clone_from=reader)
    original = source_writer.pages[0]
    if original.rotation:
        original.transfer_rotation_to_content()
    w, h = float(original.cropbox.width), float(original.cropbox.height)
    lines = ["Internal accounting allocation",
             f"Employee: {employee['name']} (ID: {employee['employee_id']})",
             f"Cost center: {employee['cost_center']}", f"Location: {employee['location']}"]
    cmap = pdfmetrics.getFont("AllocationSans").face.charToGlyph
    if any(ord(c) not in cmap for c in "".join(lines)):
        raise ValueError("The included font cannot display a selected value. No copy created.")
    style = ParagraphStyle("allocation", fontName="AllocationSans", fontSize=9, leading=13,
                           textColor=colors.HexColor("#18332d"))
    paragraphs = [Paragraph(escape(line), style) for line in lines]
    heights = [p.wrap(w - 48, 500)[1] for p in paragraphs]
    footer = max(96, sum(heights) + 34)
    out = io.BytesIO()
    c = canvas.Canvas(out, pagesize=(w, h + footer))
    c.setFillColor(colors.HexColor("#edf5f0")); c.rect(0, 0, w, footer, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#517e6e")); c.line(24, footer - 8, w - 24, footer - 8)
    y = footer - 18
    for paragraph, height in zip(paragraphs, heights):
        y -= height; paragraph.drawOn(c, 24, y)
    c.showPage(); c.save()
    footer_writer = PdfWriter(clone_from=PdfReader(io.BytesIO(out.getvalue())))
    first = footer_writer.pages[0]
    first.merge_transformed_page(original, Transformation().translate(
        tx=-float(original.cropbox.left), ty=footer - float(original.cropbox.bottom)))
    writer = PdfWriter()
    writer.add_page(first)
    for page in source_writer.pages[1:]:
        writer.add_page(page)
    writer.add_metadata({"/Title": "Accounting copy", "/Producer": "Invoice Allocation 0.1.0"})
    result = io.BytesIO(); writer.write(result)
    return result.getvalue()


@dataclass
class Invoice:
    file_id: str
    name: str
    data: bytes
    matches: list
    note: str
    error: str = ""


class Batch:
    def __init__(self, csv_text, files):
        self.staff = read_staff(csv_text)
        if not isinstance(files, list) or not 1 <= len(files) <= 25:
            raise ValueError("Choose 1 to 25 PDF files.")
        if sum(len(data) for _, data in files) > MAX_TOTAL:
            raise ValueError("The batch exceeds 24 MB.")
        self.batch_id = secrets.token_urlsafe(18)
        self.files = {}
        for index, (name, data) in enumerate(files, 1):
            name = Path(str(name).replace("\\", "/")).name
            if not name or len(name) > 160 or any(ord(c) < 32 for c in name):
                raise ValueError("Use filenames of at most 160 characters without control characters.")
            row = Invoice(str(index), name, data, [], "")
            try:
                row.matches, row.note = candidates(data, self.staff)
            except Exception as exc:
                row.error = f"Cannot process: {type(exc).__name__}. Use a plain, unsigned PDF copy."
            self.files[row.file_id] = row

    def summary(self):
        return {"batch_id": self.batch_id, "staff": list(self.staff.values()),
                "files": [{"id": f.file_id, "name": f.name, "matches": f.matches,
                           "note": f.note, "error": f.error} for f in self.files.values()]}

    def make_copy(self, file_id, employee_id):
        if file_id not in self.files or employee_id not in self.staff:
            raise ValueError("Unknown invoice or employee.")
        f = self.files[file_id]
        if f.error:
            raise ValueError("This invoice could not be processed.")
        return accounting_copy(f.data, self.staff[employee_id])

    def export(self, selections):
        if not isinstance(selections, list) or not selections or len(selections) > len(self.files):
            raise ValueError("Approve at least one invoice.")
        seen, rows = set(), []
        # Validate the entire request before generating or returning any copies.
        for item in selections:
            fid, eid = item.get("file_id"), item.get("employee_id")
            if item.get("approved") is not True or fid in seen or fid not in self.files or eid not in self.staff:
                raise ValueError("Each selected invoice needs one explicit approval and a valid employee ID.")
            if self.files[fid].error:
                raise ValueError("A selected invoice is blocked.")
            seen.add(fid); rows.append((fid, eid, self.make_copy(fid, eid)))
        output = io.BytesIO(); report = io.StringIO(newline="")
        writer = csv.writer(report)
        writer.writerow(["source_file", "source_sha256", "accounting_copy", "copy_sha256",
                         "employee_id", "name", "cost_center", "location", "selection"])
        def cell(value):
            return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            for fid, eid, pdf in rows:
                f, e = self.files[fid], self.staff[eid]
                stem = re.sub(r"[^\w .-]", "_", Path(f.name).stem, flags=re.UNICODE)[:90] or "invoice"
                name = f"{int(fid):02d}-{stem}-accounting-copy.pdf"
                z.writestr(name, pdf)
                writer.writerow([cell(f.name), hashlib.sha256(f.data).hexdigest(), name,
                                 hashlib.sha256(pdf).hexdigest(), *[cell(e[k]) for k in
                                 ("employee_id", "name", "cost_center", "location")],
                                 "proposed-name-confirmed" if f.matches == [eid] else "manual-selection-confirmed"])
            z.writestr("allocation-report.csv", report.getvalue().encode("utf-8-sig"))
        return output.getvalue()


EXAMPLE_STAFF = "employee_id,name,cost_center,location\nE001,Alex Novak,CC-110,Belgrade\nE002,Sam Lee,CC-220,Novi Sad\nE003,Sam Lee,CC-330,Niš\nE004,Мила Петровић,CC-440,Београд\n"


def example_files():
    """Owned fictional documents only; generated on request for the trial."""
    files = []
    for name, employee in [("01-match.pdf", "Alex Novak"), ("02-duplicate.pdf", "Sam Lee"),
                           ("03-unmatched.pdf", "Taylor Example"), ("04-cyrillic.pdf", "Мила Петровић")]:
        b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(595, 842))
        c.setFont("AllocationSans", 20); c.drawString(48, 775, "FICTIONAL TRAINING INVOICE")
        c.setFont("AllocationSans", 11)
        for y, line in [(725, "Example Screening Ltd - no real company or person"),
                        (685, "Employee: " + employee), (650, "Service: screening administration"),
                        (615, "Invoice number: SYNTH-" + name[:2]), (580, "Total: USD 45.00"),
                        (70, "Synthetic fixture. No screening results or personal records.")]:
            c.drawString(48, y, line)
        c.showPage(); c.save(); files.append((name, b.getvalue()))
    return files
