# Ripple build checkpoint — update after every completed phase

**Last verified:** 2026-11-09  
**Last completed microphase:** `P03.1b` (production secret metadata verification + usage-safe default + telemetry; P03 live endpoint verification pending)  
**Current phase:** `P03` — live Clocked contract validation (key exists securely; gated by disabled mode and zero default budget)  
**Suggested resume command:** `python -m pytest -q && node --check web/app.js && CHROMIUM_PATH=/usr/bin/chromium python -m scripts.browser_smoke`  
**Core status file:** `checkpoint.json`  
**Full microphase plan:** `docs/PHASE_PLAN.md`

## Verified completion log

### P00 — Baseline audit [complete]
- Reused the previous Ripple starter, inspected `app/`, `web/`, and `tests/`.
- Verified sample data: 16 **fictional** applicants; old/new policies contain explicit GPA and household-income thresholds.
- Initial `python -m pytest -q`: **12 passed**.
- Identified lack of live-key verification, PDF evidence flow, and precise flip-path interaction.

### P01 — Checkpoint discipline and secret-safe setup [complete]
- Created this file, `checkpoint.json`, `docs/PHASE_PLAN.md`, `docs/SECURE_API_SETUP.md`, and `AGENTS.md` for reliable cross-session resumption.
- Added `python-dotenv` to local backend dependencies; `.env` is loaded by FastAPI without overriding provider environment variables.
- Expanded `.gitignore` to exclude `.env.*` except sanitized `.env.example`.
- No API keys were requested or stored in the repository.
- Verified via regression suite below.

### P02 — Decision Flip Explorer [complete]
- Added `app.rules.flip_path`: computes the precise *minimum threshold changes* required under the **new** modeled policy (GPA, income, or both), using deterministic arithmetic; refuses to guess if rules/facts are absent.
- Added flip paths to the data returned for every synthetic or live applicant case.
- Added an interactive flip-path panel and **Try these thresholds** button; the button moves the what-if sliders to exact target boundaries.
- Added **Find GPA** / **Find income** buttons linking verbatim evidence to a text selection in the original policy editor.
- Added four unit tests for single/double failures, inclusive boundaries, unknowns and impact integration.
- `python -m pytest -q`: **16 passed**; `node --check web/app.js`: **passed**.
- Caveat: browser visual QA still pending; live API fields have only been mocked.

### UI-01 — Light-first dashboard redesign [complete; 2026-11-09]
- User requested a major interface overhaul; **light mode is now the default**, with manual dark-mode toggle and guarded local preference storage.
- Rebuilt navigation, topbar, impact cards, policy delta, responsive outcome cards, evidence panel, simulator and a cohesive explanatory hero. No build-tool dependency was added.
- Added outcome filters (all/lost/gained/unchanged/review), quick jump to a lost case, exact case explanation, changed-input warning, and an explicit disabled live-analysis state when a server key is not configured.
- `python -m pytest -q`: **20 passed**; `node --check web/app.js`: **passed**; `CHROMIUM_PATH=/usr/bin/chromium python -m scripts.browser_smoke`: **passed** with mock API.
- Browser checks: 390/768/1024/1280/1440 widths, dark toggle, filters, exact flip path, verbatim evidence selector, no JS page errors or horizontal overflow. Actual HTTP server route calls to `/`, `/assets/`, `/api/health`, `/api/demo` returned 200; Chromium HTTP localhost navigation blocked by environment policy, so actual HTTP browser E2E still pending.
- User supplied production URL `https://ripple-consequence-engine.vercel.app/`. Vercel project listed through search, but project details and deployment listings returned API errors (404/403). Automatic production redeploy **not yet confirmed**.

### P04.1 — PDF text ingestion + source page mapping [complete; 2026-11-09]
- Implemented request-only `/api/parse-pdf` with `pypdf`, `python-multipart`, strict PDF signature/extension/type validation, **2 MB max file**, **12 pages max**, and **12,000 chars max**; rejects encrypted/scanned/blank/invalid PDFs with clear messages.
- Added two version-specific upload selectors; populates policy text for manual review and exposes original per-page character offsets. Uploading uses **zero Clocked calls**. Source-evidence jumps are blocked when document edits make results stale.
- Published two clearly fictional, downloadable sample PDF documents. The API does not persist uploaded PDFs to project storage or call Clocked in the preview step. Future PDF annotation remains separate and unverified.
- Tests: `python -m pytest -q` **27 passed**; JS syntax check **passed**; isolated Chromium smoke **passed** including upload, dirty warning, filters, theme, and responsive widths. Generated sample PDF was visually rendered and reviewed.
- This is a **partial P04 milestone**, not P04 completion. PDF Clocked-mode integration, annotation, and live page spans remain pending on the API key.
- User confirmed earlier UI-01 light mode is visible on Vercel; the new PDF changes have not yet been verified on production.

## Current blockers

**P03.1 has been verified:** Vercel's project environment-variable listing (with `decrypt=false`) shows a `CLOCKED_API_KEY` entry of type `sensitive`, target `production`. No value was retrieved or stored. `ENABLE_LIVE` and `MAX_LIVE_ANALYSES` were not found in the project metadata, so live analysis stays off by design. P03.2–P03.4 remain unverified: the key's validity and actual endpoint responses have not been tested. Never expose the secret in logs, traces or screenshots.

## Partial work completed in later phases (NOT marked complete)

### P03.5 — Directional parsing safety [partial]
- Hardened `app/clocked_adapter.py` to reject inverted GPA/income restrictions, unspecified income currency, and repeated snippets without verified positions. Unsupported clauses become `review`.
- Added four corresponding tests. Suite now **20 passed**.
- Created `scripts/smoke_clocked.py`: explicit `--run` flag, exactly four real requests against synthetic sample only, sanitized summary. **Not run** with a key.

### P06.3 — Isolated Chromium visual smoke [partial]
- Added `scripts/browser_smoke.py` for Chromium verification with a synthetic API stub (no live network).
- Confirmed case rendering, applying the GPA flip path, highlighting source text in the editor, no JavaScript page errors, and no horizontal overflow at 390px.
- Generated `fixtures/screenshots/ripple-desktop.png`, `ripple-mobile.png`, and `ripple-evidence-jump.png`.
- **This is not full HTTP end-to-end testing** and does not verify Clocked connectivity. Full browser/deployment QA remains in P06.

## Next exact steps

1. Confirm the PDF upload commit redeploys from GitHub to the user-provided Vercel URL; text preview should cost no Clocked credits.
2. Check that the protected production deployment accepts the new fail-closed `MAX_LIVE_ANALYSES=0` default. This is an offline/config check and costs no credits.
3. Before running actual Clocked calls, implement durable usage protection or temporarily enable the backend for a supervised test; do not leave the anonymous endpoint open based only on the in-memory budget.
4. Test `P03.2–P03.4` using fictional policy text with the real SDK, inspect and sanitize responses, and record actual credit totals. Four requests are planned for the complete flow.
5. Continue P04.2 PDF evidence spans when the real API response shapes are known.

## Checkpoint maintenance protocol

After **every** phase: update both this human-readable file and `checkpoint.json`, record tests with exact results and links/paths to artifacts, note unresolved work, and identify the *next one or two concrete actions*. Avoid marking a phase complete if a required live verification is blocked.


### P03.1b — Secure key confirmation and usage instrumentation [complete; 2026-11-09]
- Queried Vercel's `filter_project_envs(decrypt=false)` by project **name**; `CLOCKED_API_KEY` is a Sensitive Production variable. The integration returned only metadata and no secret value was accessed.
- Neither `ENABLE_LIVE` nor `MAX_LIVE_ANALYSES` was present; no authenticated live-analysis request was initiated.
- Changed the backend to fail closed unless a positive per-process budget is explicitly configured. Default `MAX_LIVE_ANALYSES=0` and `ENABLE_LIVE=false` in `.env.example`. Even a positive in-process budget **is not a durable spending limit on Vercel**.
- Added SDK credit/cost/latency metadata to a live response, provided the SDK reports it; also show credits in the UI only when present. This instrumentation does not create extra Clocked calls.
- `python -m pytest -q`: **30 passed**; `node --check web/app.js`: **passed**; `CHROMIUM_PATH=/usr/bin/chromium python -m scripts.browser_smoke`: **passed** with mock API. No real Clocked credits consumed.
- Real SDK contract/latency/billing values are still unknown, so P03.2 onward remains incomplete.

### P05 — Consequence-first judge experience [COMPLETE LOCALLY; 2026-11-09]
- Added the interactive, keyboard-selectable **Consequence Map**, recalculated directly from the underlying two-rule evaluator; 16 line paths corresponding to 16 fictional applicants.
- Added a **Rule Lab** to adjust the updated GPA and income limits and recalculate all applicant transitions instantly. Includes **Tighter rules** and **Wider access** presets and Reset. Explicitly labels rules as hypothetical; leaves original source evidence untouched. No Clocked requests.
- Added a four-step guided tour and dynamic badges; the hero remains light-mode first, with optional saved dark mode.
- Added a page-aware **Source Lens** that highlights exact textual source clauses and can open the locally uploaded original PDF at its source page, when the source is current and uniquely matched.
- Added an exportable, self-contained printable HTML proof card for a single case. Escapes dynamic text and flags hypothetical rules; no real applicant data in the default sample.
- Chromium offline smoke tested flow paths, keyboard selection, both policy presets, theme, tour, PDF ingestion, source lens, evidence selection and proof HTML download, across mobile through desktop widths.

### P03.2a / P04.3 — Protected live verification and PDF annotation [IMPLEMENTED; NOT LIVE VERIFIED]
- Public `/api/analyze` now requires an expiring, server-only verifier key on top of its separate LIVE gate; the public site continues to report `live_enabled: false` and **cannot** trigger API charges by clicking sliders or upload controls.
- Added `POST /api/internal/verify-clocked`, which (only when explicitly unlocked) performs Extract ×2 + Compare ×1 + Rerank ×1 against the fixed fictional sample, with `Clocked(max_attempts=1)`. Output contains limited sanitized threshold/usage metadata and no raw secrets.
- Added `POST /api/internal/pdf-proof`: one separate optional Clocked Compare request with `return_pdf="highlight"` on the bundled synthetic PDFs. It exports only the real SDK `marked_pdf()` bytes, otherwise writes a manifest identifying missing annotations. The flow is fake-SDK tested but **not authenticated on real Clocked**.
- The token must be 32+ characters; an explicit future timestamp and `ENABLE_VERIFICATION=true` are both required. Invalid auth fails with 404. Protected routes are hidden from public OpenAPI descriptions.
- Added `Cache-Control: no-store` to API routes, frame denial, referrer policy and `nosniff`. Added negative tests for gate, token expiry, missing PDF annotations, invalid PDF-before-billing, and route headers.

### P06 — Offline QA and submission handoff [COMPLETE OFFLINE; LIVE CHECK REMAINS]
- `python -m pytest -q`: **37 passed**.
- `node --check web/app.js`: **passed**.
- `CHROMIUM_PATH=/usr/bin/chromium python -m scripts.browser_smoke`: **passed** (isolated synthetic fetch stub, NOT live HTTP or real Clocked).
- Wrote judge walkthrough, submission draft, security review, SDK integration contract, deployment instructions, explicit real-verification results placeholder and GitHub Actions offline CI workflow.
- No real Clocked call was made as part of the above tests; token/key was never accessed.

## Pending at end of P05/P06 local work

1. Confirm the final main-branch push and Vercel Ready Production deployment. The user confirmed an earlier light-mode deployment, not this release.
2. Perform at most one protected four-call live Clocked smoke if a short-lived verifier can be configured and securely invoked; otherwise leave status UNVERIFIED.
3. If possible, verify Clocked's genuine `return_pdf="highlight"` marked PDF output (one additional protected call). No fabricated source highlight will be called Clocked output.
4. Record the challenge's external submission result separately; code deployment alone is **not** submission.

### P07.2 — Verified Vercel release and judge media [COMPLETE, 2026-11-09]
- GitHub release commit: `5f93b5fa167e7efd4171d997e23aad2a5deaad63`.
- Vercel deployment `dpl_4R9pBSYatPqqagjnPAeTUrRtDSQY` was reported `READY`, target `production`, with matching commit SHA. The platform returned the stable `ripple-consequence-engine.vercel.app` alias for that deployment.
- Local offline suite: 37 pytest tests, Node syntax check, Chromium UI smoke (map, presets, evidence, proof export, mobile/light/dark). No paid calls made.
- Created a **61-second** silent screen walkthrough of the synthetic browser demo with an intro/outro slate and optional timed subtitles. This is not a live Clocked recording. Files delivered separately for upload to a video host or submission form.
- Direct HTTP checks of public `/api/health` and `/api/demo` and a real Clocked call are still outstanding. Do not claim either from deployment metadata alone.
- Code deployment is complete; **external hackathon submission is not yet confirmed**.


### P06.5 — Full release audit and credit-free policy preview [code complete; 2026-11-09]
- Audited production route protections, SDK adapter, upload limits, UI renderers, and Vercel secret metadata. Avoided retrieving the key.
- Confirmed a real UX gap: once a user uploaded new PDF text, the public site had no way to recalculate impacted cases while paid analysis was locked.
- Added `POST /api/preview` and a **Preview policy changes** action; strict offline-only rule extractor supports one minimum GPA and USD annual household income ceiling per policy, with additional requirements/ambiguity producing review instead of a fabricated positive decision.
- Added six new parser/route checks plus two ambiguity regression cases: **45 unit tests passing**, JS syntax passing.
- Ran isolated Chromium UI regression AND `scripts/fullstack_smoke.py`, which bridges Chromium interactions to real FastAPI TestClient handlers for PDF parsing, preview, and decision evidence. No external paid calls.
- Real Clocked authentication still not demonstrated: key exists as Vercel Sensitive metadata, but verification requires separate temporary admin token; Vercel web fetch denies deployment access. Do not publish a successful live claim.
- New source must be verified as Vercel READY after commit; do not conflate a prior production release with this new version.

- Audit release `469d3037f1271afead81f59ec0827ef6fcc994fb` verified READY Production with stable `ripple-consequence-engine.vercel.app` alias via Vercel metadata; actual public HTTP fetch and authenticated Clocked request remain blocked by access permissions.


### LP-01 — Public landing page [implemented locally; deploy pending 2026-11-09]
- Split `GET /` into a complete light-first landing page; preserved existing interactive studio at `GET /studio` without login. Both share theme preference, with light mode as default.
- Added interactive 2025/2026 policy preview driven by the real fictional `/api/demo` endpoint, not hardcoded impact data or paid Clocked calls.
- Created responsive illustrations, feature explanations, evidence example, source-code link, accessible navigation, reduced-motion support and app favicon.
- Repointed offline Chromium and demo recording to `web/studio.html`; added `scripts/landing_smoke.py` and assertions in route tests.
- Re-ran unit suite and browser checks (see release receipt). No real Clocked request was made in these tests.
- Vercel sandbox-backed secure HTTP verification was attempted but failed with **403 forbidden** to create sandbox; an alternative authorized invocation channel remains necessary to call protected Clocked endpoint. The Sensitive Production key exists but was not decrypted or copied.