import hashlib
import io
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from allocation import (Batch, EXAMPLE_STAFF, accounting_copy, candidates,
                        example_files, read_staff, load_pdf)
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, ArrayObject, RectangleObject
from reportlab.pdfgen import canvas


class AllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = example_files()
        cls.staff = read_staff(EXAMPLE_STAFF)

    def test_unique_duplicate_missing_unicode(self):
        batch = Batch(EXAMPLE_STAFF, self.files)
        self.assertEqual([r.matches for r in batch.files.values()],
                         [["E001"], ["E002", "E003"], [], ["E004"]])

    def test_duplicate_employee_ids_blocked_but_duplicate_names_retained(self):
        self.assertEqual(len(self.staff), 4)
        with self.assertRaisesRegex(ValueError, "duplicate employee_id"):
            read_staff(EXAMPLE_STAFF + "E001,Another,CC-Z,Elsewhere\n")

    def test_csv_bom_quotes_and_required_values(self):
        rows = read_staff('\ufeffemployee_id,name,cost_center,location\r\nE1,"Doe, Alex",CC-1,"City, North"\r\n')
        self.assertEqual(rows["E1"]["location"], "City, North")
        for text in ["name\nAlex\n", "employee_id,name,cost_center,location\nE1,,CC-1,City\n"]:
            with self.assertRaises(ValueError):
                read_staff(text)

    def test_no_substring_employee_match(self):
        staff = read_staff("employee_id,name,cost_center,location\nE1,Alex Nova,CC1,City\n")
        self.assertEqual(candidates(self.files[0][1], staff)[0], [])

    def test_scanned_page_manual_selection_and_copy(self):
        writer = PdfWriter(); writer.add_blank_page(width=595, height=842)
        buf = io.BytesIO(); writer.write(buf)
        data = buf.getvalue()
        batch = Batch(EXAMPLE_STAFF, [("scan.pdf", data)])
        self.assertEqual(batch.files["1"].matches, [])
        self.assertIn("No selectable text", batch.files["1"].note)
        pdf = batch.make_copy("1", "E003")
        self.assertIn("CC-330", PdfReader(io.BytesIO(pdf)).pages[0].extract_text())

    def test_explicit_approval_and_employee_validation(self):
        batch = Batch(EXAMPLE_STAFF, self.files)
        for selection in [[], [{"file_id": "1", "employee_id": "E001"}],
                          [{"file_id": "1", "employee_id": "unknown", "approved": True}],
                          [{"file_id": "unknown", "employee_id": "E001", "approved": True}]]:
            with self.assertRaises(ValueError):
                batch.export(selection)

    def test_manual_duplicate_resolution_and_report(self):
        batch = Batch(EXAMPLE_STAFF, self.files)
        result = batch.export([{"file_id": "2", "employee_id": "E003", "approved": True}])
        with zipfile.ZipFile(io.BytesIO(result)) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(len(z.namelist()), 2)
            report = z.read("allocation-report.csv").decode("utf-8-sig")
            self.assertIn("manual-selection-confirmed", report)
            self.assertIn("Niš", report)
            pdf = z.read(next(n for n in z.namelist() if n.endswith(".pdf")))
            self.assertIn("CC-330", PdfReader(io.BytesIO(pdf)).pages[0].extract_text())
            self.assertNotIn("CC-220", PdfReader(io.BytesIO(pdf)).pages[0].extract_text())

    def test_original_bytes_preserved_and_output_text(self):
        original = self.files[3][1]; digest = hashlib.sha256(original).hexdigest()
        result = accounting_copy(original, self.staff["E004"])
        self.assertEqual(hashlib.sha256(original).hexdigest(), digest)
        page = PdfReader(io.BytesIO(result)).pages[0]
        self.assertIn("Мила Петровић", page.extract_text())
        self.assertIn("Београд", page.extract_text())
        self.assertIn("SYNTH-04", page.extract_text())
        self.assertGreater(float(page.mediabox.height), 842)

    def test_broken_pdf_isolated_and_blocked_export(self):
        batch = Batch(EXAMPLE_STAFF, [("bad.pdf", b"not a pdf"), self.files[0]])
        self.assertTrue(batch.files["1"].error)
        self.assertEqual(batch.files["2"].matches, ["E001"])
        with self.assertRaises(ValueError):
            batch.export([{"file_id": "1", "employee_id": "E001", "approved": True}])

    def test_encrypted_annotated_and_interactive_rejected(self):
        for kind in ["encrypted", "annotation", "form"]:
            writer = PdfWriter(); page = writer.add_blank_page(width=595, height=842)
            if kind == "encrypted": writer.encrypt("private")
            elif kind == "annotation": page[NameObject("/Annots")] = ArrayObject([DictionaryObject()])
            else: writer._root_object[NameObject("/AcroForm")] = DictionaryObject()
            out = io.BytesIO(); writer.write(out)
            with self.assertRaises(ValueError): load_pdf(out.getvalue())

    def test_crop_rotation_and_other_pages_preserved(self):
        src = PdfReader(io.BytesIO(self.files[0][1])); first = src.pages[0]
        first.cropbox = RectangleObject([20, 30, 575, 812]); first.rotate(90)
        writer = PdfWriter(); writer.add_page(first); writer.add_blank_page(width=420, height=595)
        out = io.BytesIO(); writer.write(out)
        result = accounting_copy(out.getvalue(), self.staff["E001"])
        pages = PdfReader(io.BytesIO(result)).pages
        self.assertEqual(len(pages), 2)
        self.assertEqual(float(pages[0].mediabox.width), 782)
        self.assertEqual(float(pages[1].mediabox.width), 420)
        self.assertEqual(float(pages[1].mediabox.height), 595)
        self.assertIn("USD 45.00", pages[0].extract_text())

    def test_long_and_unsupported_glyph_values(self):
        employee = dict(self.staff["E001"], location="Long city name " * 10)
        pdf = accounting_copy(self.files[0][1], employee)
        self.assertIn("Long city", PdfReader(io.BytesIO(pdf)).pages[0].extract_text())
        with self.assertRaisesRegex(ValueError, "font"):
            accounting_copy(self.files[0][1], dict(employee, location="東京"))


if __name__ == "__main__":
    unittest.main()
