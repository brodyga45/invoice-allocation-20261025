# Invoice Allocation 0.1.0

A local browser tool for adding reviewed employee cost-center and location details
to accounting copies of invoice PDFs. It replaces repeated lookups and manual
Paint annotations. This is an original, AI-assisted candidate built using fictional
invoices for one observed workflow. It is not a customer installation or a promise
of compatibility with an unknown invoice layout.

## Run

Python 3.10+ is required. From the extracted folder:

On Windows with the Python launcher installed, you can instead double-click
**Setup Windows.cmd** once, wait for **Ready**, then double-click
**Start Windows.cmd**. The commands below are the manual alternative.

```text
python -m venv .venv
```

Windows:

```text
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

macOS / Linux:

```text
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

The browser opens the printed `http://127.0.0.1:<port>` address. If it does not,
open that address manually. The port is selected automatically; Ctrl+C in the
terminal closes the server. Do not host this as a public web service. Installation
uses PyPI; processing makes no cloud calls.

## Try the complete workflow

1. Click **Try fictional invoices**. Four invoices demonstrate a unique name,
   a duplicate name with two employee IDs, a missing name and Cyrillic text.
2. Choose the correct employee ID for every file you want to export. Review the
   displayed cost center and location. Changing the employee removes its approval.
3. Click **Preview**, inspect the accounting copy, then mark that invoice
   **Reviewed**. No file is approved automatically.
   The local viewer switches between the unchanged original and the accounting
   copy, and supports page navigation and zoom. No external PDF viewer is required.
4. **Save reviewed copies** returns a ZIP with only checked invoices and a
   UTF-8 CSV allocation report including source and result SHA-256 hashes.
   Nothing is submitted to accounting.
5. **Clear batch** discards the loaded batch from the process. Browser downloads
   remain in the browser's download folder. Closing the process also discards
   its current in-memory batch; this version has no resume database.

For your own batch, choose a UTF-8 staff CSV with these headers and unique IDs:

```csv
employee_id,name,cost_center,location
E001,Alex Novak,CC-110,Belgrade
E002,Sam Lee,CC-220,Novi Sad
E003,Sam Lee,CC-330,Niš
```

Duplicate names are allowed; they require selection of the correct employee ID.
Names are matched against extracted selectable text, using normalized whitespace,
Unicode case folding and whole-name boundaries. A match is only a suggestion:
the same name can occur elsewhere in a document. For scanned or unmatched PDFs,
select the employee manually. This release has no OCR and does not inspect
screening results or make employment decisions.

## What changes in the PDF

The first page gains a clearly separated allocation block below its original
visible area. Its page becomes taller; original content is neither covered nor
scaled. Other pages retain their dimensions. This is an **accounting copy**,
not a replacement vendor original, PDF/A guarantee or preserved digital signature.
Confirm your accounting team's acceptance of this format before using it.

Encrypted, signed/interactive, action-bearing and annotated PDFs are rejected.
This includes PDFs with link annotations. The included Noto Sans supports common
Latin, Greek and Cyrillic text; unsupported glyphs block generation instead of
silently printing squares. Limits: 25 files, 12 MB each / 24 MB combined, 20 pages
per file, 2,000 staff rows. A blocked file does not prevent review of other files.

The tool reads user-selected files into the local Python process and browser.
It does not overwrite the sources, write a server-side customer database, upload
documents to a cloud service or send email. It does not securely erase memory,
browser caches or downloaded files. Use an authorized local machine and close
the process when finished.

## Validation and boundaries

Run `python -m unittest discover -s tests -v`. Synthetic checks cover ambiguous
names, manual selection, explicit approval, Cyrillic output, original-byte
preservation, rotated/cropped pages, multi-page copies, bad/encrypted/annotated
PDF rejection and the ZIP/report. Actual rendered PDFs and browser checks are
recorded separately in QA.md. Physical Windows installation, customer layouts,
accounting acceptance and payment are not established by those checks.

The proposed $150 service for one agreed invoice layout, setup and one correction
is separate from this candidate. No customer has accepted that quote. Client
documents, operating environment, delivery scope and acceptance must be agreed
before client work; do not put HR records in public comments.

## Rights

Our code is MIT; see LICENSE. Bundled Noto Sans is unmodified SIL OFL 1.1 with
its notice in assets/NotoSans-LICENSE.txt. pypdf and ReportLab are separate
dependencies; see THIRD_PARTY_NOTICES.md. No client materials are included.
