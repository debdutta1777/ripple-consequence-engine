# Ripple build checkpoint — update after every completed phase

**Last verified:** 2026-11-09  
**Last completed phase:** `P02`  
**Current phase:** `P03` — live Clocked contract validation (blocked on secure key configuration)  
**Suggested resume command:** `python -m pytest -q && node --check web/app.js`  
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

## 2026-11-09 deployment preparation (P07 partial, NOT complete)
- Vercel connection confirmed: Ripple project not present. Attempted project creation in the available team; received **403 Forbidden**. No project or deployment was created. Local CLI fallback is unavailable in this environment.
- Added root `main.py` FastAPI export for Vercel framework detection.
- Added `.vercel/` to `.gitignore` and `docs/VERCEL_DEPLOYMENT.md` with dashboard instructions, secret handling, and public-API safety caveats.
- Full regression suite: **20 passed** (`python -m pytest -q`).
- Next action: User creates/imports the Vercel project from a GitHub repo (or adjusts connection permissions), then sets the API key as a Sensitive server-side environment variable.

## Current blockers

**P03 requires a real Clocked key** in the local/server environment. The key is intentionally not accepted in chat. Follow `docs/SECURE_API_SETUP.md`. Once set, run an authenticated Extract request and examine the returned field structures before asserting the live UI works. Never include secret values in recordings or trace exports.

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

1. Complete `P03.1` secret setup. Confirm only `/api/health` reports `live_enabled: true` (no key shown).
2. Test `P03.2–P03.4` using the two synthetic policy texts, inspect real Clocked responses, and adjust response parser if needed.
3. Add negative semantic checks for misleading GPA/income directions and ambiguous clauses (`P03.5`), then tests.
4. Capture desktop and mobile visual evidence for the new flip path (`P06.3`) when practical.

## Checkpoint maintenance protocol

After **every** phase: update both this human-readable file and `checkpoint.json`, record tests with exact results and links/paths to artifacts, note unresolved work, and identify the *next one or two concrete actions*. Avoid marking a phase complete if a required live verification is blocked.
