# Actual Clocked API verification results

**Status: VERIFIED for the fictional text and annotated-PDF fixtures.**
Public visitor analysis remains intentionally credit-free and is **not** a live Clocked workflow. Live results below come from authenticated, isolated GitHub Actions jobs using a repository Actions secret. No API key was printed or committed.

## P03.2 — Live text analysis (2026-11-10 IST)

- [Successful workflow run 42693887137](https://github.com/debdutta1777/ripple-consequence-engine/actions/runs/42693887137).
- **Four authenticated SDK requests:** Extract ×2, Compare ×1, Rerank ×1.
- Previous policy: minimum GPA **3.2**, maximum household income **USD 50,000**.
- Current policy: minimum GPA **3.5**, maximum household income **USD 60,000**.
- All four extracted thresholds matched the fictional source documents exactly.
- Compare verdict: `conflicts`, with **1** conflict. Rerank returned **4** results.
- SDK-reported usage: **24 credits**.

## P04 — Native annotated PDF Compare (2026-11-10 IST)

- [Successful workflow run 42695749607](https://github.com/debdutta1777/ripple-consequence-engine/actions/runs/42695749607), job **129427019985**.
- **One authenticated Clocked Compare request**, using only bundled fictional `web/samples/previous-policy.pdf` and `updated-policy.pdf`, SDK `return_pdf="highlight"`, `return_text=True`.
- Compare verdict: `conflicts`; **1** conflict.
- SDK-reported usage: **9 credits**, **USD 0.001793**, **200.551425 ms model time**.
- The previous PDF contained **1** genuine PDF `/Highlight` annotation; the current PDF contained **4**. Both outputs were valid single-page PDFs and retained their original policy text.
- Verified SHA-256, previous marked PDF: `79a2aa9689cf48b5692b9b275301cd6a374c8a893a92c95b7594cf92e0d43a75`.
- Verified SHA-256, current marked PDF: `fb13c095ddf0ca4d12a39d5788d855076dcd34ed6af0a317655abfdd8c6f47fa`.
- GitHub Actions artifact `ripple-real-clocked-pdf-proof` (artifact ID `13707534934`) contains the **actual annotated PDFs** and `verification-report.json`. Retention expires **2026-11-16**.
- The artifact was downloaded, inspected with `pypdf`, and the marked PDF was rendered for visual QA. All five annotations were `/Highlight` objects; the current PDF's four lines were visibly highlighted.
- The verified request uses `scripts/verify_clocked_pdf.py`. The corresponding workflow is available on `main` as **manual-only** `.github/workflows/verify-clocked-pdf.yml`, preventing automatic paid runs.

## Credit summary

| Verified activity | Authenticated calls | SDK-reported credits |
|---|---:|---:|
| Text Extract/Compare/Rerank | 4 | 24 |
| Native PDF Compare/Highlight | 1 | 9 |
| **Total** | **5** | **33** |

## Scope and remaining limitations

- These successes verify real Clocked authentication, text extraction, cross-document comparison, relevance reranking, and SDK-native marked PDF output **on fictional fixtures**.
- They do **not** prove correct handling of arbitrary uploaded policy documents, exceptions, scanned PDFs, or a public live Clocked analysis flow.
- The public site at `https://ripple-consequence-engine.vercel.app/` still uses its deterministic offline preview. Its source navigation is not presented as an SDK-native annotated PDF.
- The official hackathon submission/receipt remains unconfirmed. No sensitive credential is included in the proof artifact.

## Earlier offline quality checks

Before live verification, 45 backend tests, Javascript syntax checks, and desktop/mobile Chromium tests were recorded as passed. Those checks alone did not authenticate with Clocked. GitHub's offline CI subsequently passed after fixing the pinned `actions/checkout` SHA.


## TRY-03 — Real public PDF upload + authenticated Clocked, fresh 2025/2026 policies (2026-11-10 IST)

- **Final successful workflow:** [GitHub Actions run 42713532903](https://github.com/debdutta1777/ripple-consequence-engine/actions/runs/42713532903), job 129489052863. The workflow was invoked on an isolated verification branch using the repository's secret `CLOCKED_API_KEY`; no key was printed or committed.
- Two **new fictional, text-based PDF documents** were served at `/assets/samples/judge-policy-2025.pdf` and `/assets/samples/judge-policy-2026.pdf`.
- The hosted production application accepted both real PDF uploads through `POST /api/parse-pdf`, returning complete selectable text and one page each. `POST /api/preview` returned the expected thresholds and transitions. These endpoints are deterministic: they do *not* invoke Clocked.
- New thresholds: prior minimum GPA **3.25**, maximum annual income **USD 52,000**; current minimum GPA **3.65**, maximum annual income **USD 66,000**. Across **16 fictional applicants**: **4 lost**, **2 gained**, **2 remained eligible**, **8 remained ineligible**, **0 review**. Every value matched.
- **Genuine Clocked SDK:** The same PDF-extracted source text went through authenticated **Extract ×2, Compare ×1, Rerank ×1**. All four values matched the public upload results. Compare verdict `conflicts`; Rerank returned **4** results. **SDK-reported credits: 16** for the text suite.
- A fifth real SDK request invoked Compare on the PDF bytes with `return_pdf="highlight"`. It returned `conflicts` but no markup spans for either of these formatted PDFs. **SDK-reported credits: 3**. PDF highlighting is therefore **not verified on this fresh pair**; do not invent annotated files.
- Separate PDF-marking diagnostics on the formatted pair returned `marked.spans=0`, `marked.marked=0`, and no marked document. A compact-text version showed the same provider result. This is not a frontend defect; the returned Compare evidence lacks spans to annotate. It does **not** invalidate earlier native annotation verification on the original, simpler fictional PDFs (see P04 above).
- The final successful test reported **19 SDK credits** across its five Clocked requests. Earlier troubleshooting and failed workflow runs may have incurred additional credits; do not infer the account's total remaining balance from this figure.
- Verified artifacts: GitHub Actions `ripple-fresh-policy-live-proof` ID `13716113325` (contains sanitized `verification-report.json`, expires 2026-11-16). Browser QA used the same two PDFs via the actual FastAPI handlers; 53 Python tests and responsive Chromium smoke scripts passed.
- The `main` workflow `.github/workflows/verify-try-live.yml` is **manual-only**, not triggered by ordinary commits, to avoid recurring paid calls.
- **Boundary:** The visitor-facing `/try` remains a bounded deterministic GPA/USD income evaluator. Real Clocked runs are validated out of band. Unsupported rules are flagged for review; neither universal legal analysis nor automatic highlights for arbitrary PDFs are promised.

