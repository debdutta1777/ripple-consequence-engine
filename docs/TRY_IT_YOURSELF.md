# Try It Yourself — public policy comparison workflow

**URL:** `https://ripple-consequence-engine.vercel.app/try`

This workflow is separate from the preloaded `/studio` demonstration and does not require login. It is designed for judges to test *their own* previous and updated **text-based** policy PDFs.

## Experience

1. Upload a **previous policy PDF** and an **updated policy PDF** (up to 2 MB / 12 pages each, maximum 12,000 extracted characters).
2. Choose an applicant source: **16 clearly fictional samples**, or **a CSV with 1–100 applicants** using `id,name,gpa,income` columns. The cohort must be supplied for any population-specific claims; the two PDFs alone cannot reveal how many real applicants exist.
3. Click **Analyze policy impact**. Progress steps correspond to actual operations: parse each PDF, compare literal source lines / supported rules, then calculate each applicant outcome.
4. View total modeled cases, lost/gained/review outcomes, a donut chart, comparative threshold cards, a literal clause-change ledger, and a filtered case table. Inspect each applicant's verbatim supporting source text and open the uploaded PDF. Export modeled outcomes as CSV.
5. The landing page and Studio both link directly to `/try`. Fictional sample PDFs and a sample roster CSV are downloadable.

## Scope and data truth

- **Real user-supplied inputs:** Both PDFs are parsed by the actual FastAPI `/api/parse-pdf` handler. The server returns extracted plain text and page locations without persisting the PDF in project storage. The browser sends the text and applicant facts to `/api/preview` for deterministic evaluation.
- **Literal comparison:** The change ledger detects changed/added/deleted extracted text lines with `difflib.SequenceMatcher`. This is **not** a semantic, legal, or Clocked Compare verdict.
- **Eligibility outcomes:** The deterministic model supports only a single unambiguous minimum GPA and a single annual **USD** household income ceiling per policy. Other restrictions, exceptions, non-USD currencies, unclear thresholds, or missing applicant data produce **Needs review**, not invented eligible/ineligible results.
- **No applicant roster?** All counts are explicitly labeled as modeled *fictional* applicants; there is no claim about a real population. Providing a CSV makes the counts come from that provided roster.
- **No paid calls:** `/try` uses **zero Clocked credits**. The real Clocked Extract, Compare, Rerank and native highlighted-PDF integrations have been separately authenticated on fictional reference documents via the manual-only GitHub Actions workflows. Verified details: `docs/VERIFICATION_RESULTS.md`.
- **No logins required:** The sensitive Clocked key stays server-side; it is never sent to the browser. Uploaded data is handled transiently by the server and browser; avoid uploading real sensitive applicants or confidential policies without an appropriate privacy review.
- **Unsupported:** OCR/scanned PDFs, password-protected PDFs, complex conditional or multi-currency rules, unrestricted legal compliance checking, and automatic determination from policies alone without applicant facts.

## Quality gates

- `python -m pytest -q`: validates parsed policy changes, custom applicant cohort, safe review handling and limits.
- `CHROMIUM_PATH=/usr/bin/chromium python -m scripts.try_smoke`: exercises the live FastAPI `TestClient` through Chromium, with two real PDF upload requests and analysis POST. Asserts 16 fictional cases have 4 losses/4 gains; custom two-person CSV produces 1 loss/1 gain, filters and evidence work, export downloads, theme toggle works, 390/768/1024px layouts do not overflow, no JS exceptions, and no Clocked credit calls occur.
- Existing landing/Studio browser checks and GitHub CI remain required. CI syntax-checks the new JavaScript and runs backend tests; Chromium tests run locally to avoid adding fragile browser install requirements to the existing CI.