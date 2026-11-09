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