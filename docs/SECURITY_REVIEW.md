# Security and credit-usage review

_Last reviewed: November 9, 2026. This is a hackathon prototype and not a production scholarship adjudication service._

## Deployment secrets

`CLOCKED_API_KEY` exists only in Vercel's Sensitive Production environment and optionally in untracked local `.env`. Source control ignores `.env*` files except the blank `.env.example`. Never put credentials in static JavaScript, error messages, screenshots, logs, JSON fixtures, GitHub Actions, or download artifacts.

## Paid usage by design

- `GET /api/demo`, Rule Lab sliders, applicant what-ifs, evidence navigation, and report downloads make **zero** Clocked calls.
- PDF previews use local `pypdf` extraction (maximum 2 MB, 12 pages, and 12,000 text characters) and make **zero** Clocked calls.
- The ordinary public visitor **cannot** call the expensive `/api/analyze` endpoint. It requires a private, expiring administrator token even if the owner sets `ENABLE_LIVE=true` and a positive soft budget.
- `POST /api/internal/verify-clocked` reads **only bundled fictional policy data** and makes four potential billable requests (Extract ×2, Compare ×1, Rerank ×1) after successful administrator authentication.
- `POST /api/internal/pdf-proof` reads **only bundled fictional PDF data** and makes one potential billable Compare request with `return_pdf="highlight"`. The ZIP contains genuine annotated files only if Clocked returns them.
- Both protected routes require all three non-default server environment values: `ENABLE_VERIFICATION=true`, a random `RIPPLE_VERIFY_TOKEN` of 32+ characters, and `RIPPLE_VERIFY_UNTIL` (a future UNIX epoch timestamp). An expired or incorrect token yields a generic 404; the route does not run an SDK request.
- SDK requests are made with `max_attempts=1` for protected tests. The four-request verifier returns **sanitized** evidence and SDK-reported credits; it never invents usage metrics.

**Important:** `MAX_LIVE_ANALYSES` is a *per-process* guard, not a durable, global spend limit. Never enable unrestricted public paid analysis without a persistent atomic quota and effective abuse controls (e.g., a durable Redis limiter). Immediately disable `ENABLE_VERIFICATION` after the controlled verification run. Vercel environment changes require a new deployment to take effect.

## Input and evidence safety

- `pydantic` validates policy text lengths (maximum 12,000 per version) and applicant sizes/ranges.
- PDF upload checks the file signature, extension, MIME, encrypted status, page count and extracted character limit. Scanned PDFs are rejected rather than silently OCR'd or misrepresented.
- Clocked's raw extraction output cannot produce a rule unless the extracted phrase is present verbatim in the source and passes the strict directional and currency checks. Unsupported policies fail toward `needs review`.
- All user-supplied text displayed in dynamic HTML is escaped or assigned through `textContent`. Downloadable proof cards are locally generated and labeled fictional; simulated thresholds are never represented as sourced clauses.
- API responses carry `Cache-Control: no-store`; headers include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: no-referrer`.

## Known limits and accepted risks

- This is not a full policy compiler, legal interpretation service, privacy-regulated student information system, or an OCR service.
- No persistent database, global billing ledger, or authenticated user accounts are implemented. These would be necessary for a real-world public SaaS product.
- Clocked PDF annotations and live response formats are mock-tested locally but **not yet authenticated against the production SDK**, unless and until `docs/VERIFICATION_RESULTS.md` records a genuine run.
- Vercel's public deployment needs post-push verification of the commit and route health, rather than assuming GitHub deployment always succeeds.