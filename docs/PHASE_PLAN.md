# Ripple — phase-by-phase build roadmap

One checkpoint per completed phase; code and status must be committed together. All results must be marked accurately as **offline mock**, **real backend route**, or **real Clocked API**.

| Phase | Name | State | Acceptance evidence |
|---|---|---|---|
| P00 | Starter audit | Complete | Reused synthetic data and found project gaps |
| P01 | Project checkpoints + secret safety | Complete | `checkpoint.json`, human logs, safe environment setup |
| P02 | Decision Flip Explorer | Complete | Exact two-rule counterfactual, evidence buttons, unit tests |
| LP-01 | Public landing page | Complete, local browser QA | Marketing overview, interactive fiction preview, mobile/dark checks; public deployment pending |
| UI-01 | Light-first redesign | Complete | User confirmed Vercel site; saved dark-mode toggle, responsive tests |
| P03.1 | Secure Clocked secret metadata | Complete | Sensitive Production key confirmed without decryption |
| P03.1b | Credit safety + telemetry | Complete | Public paid route gated; credits only from SDK metadata |
| P03.2 | Protected Clocked smoke | Pending real API run | Four authenticated SDK responses, sanitized output, no secrets |
| P03.3 | Live contract remediation | Pending smoke | Real field shapes, verdict, rerank scores, billing trace |
| P04.1 | PDF text extraction | Complete | 2MB/12page/12k limits, mock UI + error tests |
| P04.2 | PDF source lens | Complete (offline) | Local page offsets, original PDF navigation, highlighted exact text |
| P04.3 | Clocked PDF annotation code | Implemented, mock-tested | Protected optional `return_pdf="highlight"` flow; genuine marked file requires live test |
| P05.1 | Consequence Map | Complete | Interactive, accessible SVG lines based on deterministic outcomes |
| P05.2 | Policy Rule Lab | Complete | Instant whole-cohort recalculation, no Clocked calls, two presets |
| P05.3 | Guided judge tour | Complete | Four-step tour and browser checks |
| P05.4 | Proof card / JSON export | Complete | Standalone case HTML and evidence JSON, provenance disclaimer |
| P06.1 | Automated tests | Complete offline | 37 pytest tests, Node check, Chromium smoke across five widths |
| P06.2 | Secure public mode | Complete prototype | No public paid calls, expiring admin verifier, safe response headers |
| P06.3 | Real network and live QA | Pending real deployment confirmation | Actual deployed site, PDF flow, authenticated Clocked output |
| P07.1 | Public repository | Complete | GitHub history with roadmap/checkpoints |
| P07.2 | Production deployment | Complete for core release | GitHub commit `5f93b5f` confirmed Vercel Production READY and stable alias assigned |
| P07.3 | Submission docs and demo | Complete docs; video pending | `docs/SUBMISSION.md` and `docs/JUDGE_DEMO.md` |
| P07.4 | Submit to organizer | User action pending | Submission receipt/link; do not claim submission before confirmed |

## Exact next steps after this release

1. Push and verify release commit, run GitHub Actions check, verify Vercel Production Ready, and confirm `/api/health` and `/api/demo` on the public URL. If tools cannot read runtime routes, record that limitation.
2. Attempt one controlled real Clocked smoke only with a short-lived secret-based verifier and narrow fictional inputs. Stop after success or a clear blocker; do not run repeated paid retries.
3. If real Clocked proof exists, save sanitized evidence and exact usage in `docs/VERIFICATION_RESULTS.md`. If no real call was possible, leave the status unverified.
4. Verify a demo video or publish a narration script, then complete the external challenge submission form and check confirmation.

The case data is fictional. Ripple is a narrow decision simulator, **not** a production scholarship eligibility service.