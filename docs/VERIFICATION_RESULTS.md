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
