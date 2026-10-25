# Invoice Allocation 0.1.0 candidate validation — 25 Oct 2026

This is a fictional-data candidate, not a customer deployment or paid acceptance.

- Python 3.12 bundled desktop runtime: **12 core checks passed**, final source
  output in output/core-tests.txt. Unique/duplicate/missing names, UTF-8 CSV,
  manual scan selection, source-byte preservation, Cyrillic output, explicit
  approval, broken/encrypted/annotated/interactive rejection, cropped/rotated
  first page and unchanged remaining-page dimensions, long values, glyph errors.
- **5 final HTTP checks passed** in output/http-tests.txt: exact source bytes,
  preview, ZIP/report, clear/stale batch, failed replacement clears old batch,
  wrong token/origin, static asset MIME and idle browser preconnection.
- Node syntax check on our app.js passed. Vendor assets were byte-compared with
  the existing Shtops provenance manifest; no mismatches. PDF.js assets are unchanged.
- Four actual generated PDF outputs were rendered using bundled Poppler and
  visually inspected: Latin, Cyrillic, cropped/rotated, long wrapped location.
  No clipped allocation text, missing Cyrillic glyphs or covered original content
  was observed in those fixtures. Regenerate with make_examples.py.
- Actual Chrome localhost: fictional batch loaded; unique proposals visible;
  duplicate and missing-name rows initially unselected; Save disabled at zero
  approvals. Original/accounting-copy PDF.js canvas rendered with a document
  switch. Explicit first approval enabled Save. Changing its employee to E004
  cleared the approval and disabled Save; restoring E001 and choosing duplicate
  E003 showed CC-330/Niš. One export click returned “Download prepared: 1 reviewed
  copies and the allocation report.” These observations preceded the last
  cosmetic removal of “reviewed copy” from the PDF title and the switch from
  HTTPServer to ThreadingHTTPServer; those changes have separate final PDF/core
  and HTTP evidence above. A fresh full browser run of the frozen package is
  reserved for independent review.
- The browser download event wait exceeded its configured bound: 2415.718 seconds
  for a 20-second event wait / 60-second requested tool call. The UI confirms
  preparation, **not a verified saved browser ZIP**. A targeted chrome://downloads
  read was rejected by URL policy; no alternate read or repeated click was used.
  Separate core and HTTP outputs establish ZIP bytes and CRC, not browser saving.
- Browser file chooser/upload, physical Windows installation/launcher scripts,
  unassisted customer use, OCR, signed/PDF-A preservation, actual invoice layouts
  and accounting acceptance remain unverified. No Windows compatibility claim.
- All input examples, names and allocations are fictional. No client HR data or
  screening results, credentials, customer files or payment records were used.

Independent product review completed on 25 Oct 2026. A separate team agent,
Rasp, checked the frozen a1273ae7a736113d5aa074e0de5d93b3710f16af385b1db6bf8646a342980a10
archive and kept the complete demonstrable workflow within its documented scope.
The independent browser check covered proposals, original/copy canvas, manual
same-name selection, explicit approval, approval reset and Clear. Separate HTTP
export checks verified the ZIP/report/hashes and two rendered resulting PDFs.
No blocking defect was reproduced in that scope. Acceptance of the taller first
page by an actual accounting recipient remains unproven. Browser saved-ZIP,
Windows and customer-compatibility limits above remain unchanged.

This documentation revision records the review; it changes no runtime code or
fixtures. No client delivery, order, receipt or willingness to pay is implied by
the separate $150 quote.
