"""Reproduce owned fictional inputs and the four rendered QA outputs."""
import io
from pathlib import Path
from allocation import ROOT, Batch, EXAMPLE_STAFF, accounting_copy, example_files, read_staff
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject


def main():
    output = ROOT / "output" / "pdf"
    inputs = ROOT / "output" / "example-input"
    output.mkdir(parents=True, exist_ok=True); inputs.mkdir(parents=True, exist_ok=True)
    files, staff = example_files(), read_staff(EXAMPLE_STAFF)
    (inputs / "fictional-staff.csv").write_text(EXAMPLE_STAFF, encoding="utf-8")
    for name, data in files:
        (inputs / name).write_bytes(data)
    for name, index, eid in [("accounting-alex.pdf", 0, "E001"), ("accounting-cyrillic.pdf", 3, "E004")]:
        (output / name).write_bytes(accounting_copy(files[index][1], staff[eid]))
    reader = PdfReader(io.BytesIO(files[0][1]))
    reader.pages[0].cropbox = RectangleObject([20, 30, 575, 812]); reader.pages[0].rotate(90)
    writer = PdfWriter(); writer.add_page(reader.pages[0]); writer.add_blank_page(width=420, height=595)
    data = io.BytesIO(); writer.write(data)
    (output / "accounting-rotated-cropped.pdf").write_bytes(accounting_copy(data.getvalue(), staff["E001"]))
    (output / "accounting-long-fields.pdf").write_bytes(accounting_copy(
        files[0][1], dict(staff["E001"], location="Long city name " * 10)))
    (output / "reviewed-example-copies.zip").write_bytes(Batch(EXAMPLE_STAFF, files).export([
        {"file_id": "1", "employee_id": "E001", "approved": True},
        {"file_id": "2", "employee_id": "E003", "approved": True},
        {"file_id": "4", "employee_id": "E004", "approved": True}]))
    print("Fictional inputs and accounting copies generated under output/.")


if __name__ == "__main__":
    main()
