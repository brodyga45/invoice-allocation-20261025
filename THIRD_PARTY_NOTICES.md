# Component provenance

- **Our Python/HTML/CSS/JS:** original AI-assisted work, MIT (LICENSE).
- **pypdf 6.10.0:** BSD-3-Clause, https://github.com/py-pdf/pypdf . Installed from
  PyPI for source use; the portable build includes its installed license notice.
- **ReportLab 4.4.9:** BSD-style ReportLab license, https://www.reportlab.com/ .
  Installed from PyPI for source use; the portable build includes its installed notice.
- **Portable Windows candidate:** packages CPython and runtime dependencies,
  including Pillow and charset-normalizer. Installed versions are recorded in
  BUILD-VERSIONS.json; upstream license/notice files are copied into licenses/.
  PyInstaller6.22.3 builds the executable using its distribution exception; its
  installed license is included as well. These components retain their own
  licenses, independently of the MIT application. No proprietary SDK is included.
- **NotoSans-Regular.ttf:** unmodified official notofonts/noto-fonts archived
  repository, `hinted/ttf/NotoSans/NotoSans-Regular.ttf`, retrieved 25 Oct 2026.
  https://github.com/notofonts/noto-fonts/blob/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf
  SHA-256 `b85c38ecea8a7cfb39c24e395a4007474fa5a4fc864f6ee33309eb4948d232d5`.
  Copyright 2018 The Noto Project Authors; SIL Open Font License 1.1,
  preserved verbatim at assets/NotoSans-LICENSE.txt. This font remains under OFL;
  the MIT code license does not relicense it. No endorsement claimed.

Examples contain invented names, organizations, invoices and allocations.

- **Browser PDF viewer:** adapted with permission from Shtops Receipt Review,
  MIT, own public work repository monthly-receipt-pack-20261022-shtops,
  base viewer001ea1fe86944ec9bde5ae23e493c2b99422dce4 and relative URL delta
  from local receipt-review-site-20261025. Our version accepts loaded original
  and accounting-copy bytes, with no client sample routes from that product.
- **pdfjs-dist 6.4.299 legacy browser assets:** unchanged vendored PDF.js assets
  from the existing verified source bundle, Apache-2.0. Original vendor/PROVENANCE.json
  and LICENSE-pdfjs.txt retained. MIT core-js notice retained separately.
  CMap notices and Foxit/Liberation standard-font licenses remain adjacent to
  their unchanged files. PDF.js itself, its worker and these assets are served
  locally; no CDN or WASM download is used.
