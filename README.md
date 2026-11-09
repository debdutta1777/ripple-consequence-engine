# Ripple — The Consequence Engine

> **Don't just compare what changed. Discover who it changes.**

[Live demo](https://ripple-consequence-engine.vercel.app/) · [Two-minute judge walkthrough](docs/JUDGE_DEMO.md) · [Submission draft](docs/SUBMISSION.md) · [Build checkpoints](docs/BUILD_CHECKPOINT.md)

A **consequence-first** experiment for the 2026 Clocked Build Challenge. Ripple compares two fictional scholarship policies and shows how a rule edit changes decisions for a synthetic cohort. Unlike a text-only diff, it makes those changes inspectable as interactive paths, testable what-ifs, and traceable evidence. **The app defaults to light mode**, with optional dark mode.

## What you can try without an account or credits

- **Consequence Map:** Every connecting line is an applicant's old-to-new outcome. Select a path to investigate the case.
- **Rule Lab:** Adjust the proposed GPA requirement or household-income ceiling; choose *Tighter rules* or *Wider access* to see instant, explicitly hypothetical whole-cohort results.
- **Decision Flip Explorer:** Identify a lost or gained case, inspect its reasons, and try the exact modeled threshold changes that would satisfy the updated rules.
- **Source Lens:** Highlight the verbatim clause from the previous or updated policy. With a user-uploaded PDF, the browser can open the original document at the relevant page when verified evidence is available.
- **Bounded PDF text preview:** Upload text-based PDF policies up to 2 MB / 12 pages, preview extracted text and page offsets without calling Clocked. Scanned or encrypted PDFs need manual review.
- **Proof cards:** Download a printable, standalone HTML report for a selected fictional case, with original source clauses and explicit simulation provenance.
- **Guided tour:** A four-step, interactive walkthrough for hackathon judges. Synthetic data, no sign-in.

**Trust boundary:** All sample policies and applicants are fictional. The demo models **only** a minimum GPA and maximum USD annual household income. Other requirements or unsupported language force **Needs review**. Rule Lab changes are *not* source-backed policy amendments or official scholarship decisions.

## Clocked integration

The backend implements Clocked's official Python SDK ([`clocked-sdk==0.7.0`](https://pypi.org/project/clocked-sdk/0.7.0/)):

| API | Purpose |
|---|---|
| **Extract ×2** | Copy minimum GPA and maximum household income evidence, one request per policy |
| **Compare ×1** | Detect cross-version conflicts/duplicates |
| **Rerank ×1** | Prioritize the four evidence clauses by relevance |
| **Compare PDF ×1 (optional)** | Generate a ZIP of genuinely Clocked-highlighted synthetic PDFs, if the SDK supplies marked files |

The **deterministic rule engine** in [`app/rules.py`](app/rules.py) computes the cohort outcomes. Clocked is not presented as a general policy-rule compiler. Read the precise [integration contract](docs/CLOCKED_INTEGRATION.md) and [live-verification status](docs/VERIFICATION_RESULTS.md).

Visitors and judges **do not need user accounts or login**. Separately, Clocked itself requires an authenticated API key on the server. The public demonstration does **not** call the paid API. The owner's real `CLOCKED_API_KEY` lives in Vercel as a Sensitive Production environment variable, not in this repository. Real requests require an additional, short-lived admin-only verifier; the token cannot be obtained from the UI. In-process counters alone are not a safe global credit cap on Vercel.

## Local development

Python 3.9+; Node.js for JavaScript syntax checks. The frontend has no package-build step.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/ for the landing page and http://127.0.0.1:8000/studio for the interactive workspace. Synthetic demo endpoints and all sliders work with **no API key**.

```bash
python -m pytest -q
node --check web/app.js
node --check web/landing.js
# Optional local browser smoke, if Chromium is installed:
CHROMIUM_PATH=/usr/bin/chromium python -m scripts.browser_smoke
CHROMIUM_PATH=/usr/bin/chromium python -m scripts.landing_smoke
```

`pytest` uses mocked SDK responses, including missing-billing metadata and missing PDF annotations. Only a real protected Clocked invocation establishes the live contract. The test suite has **zero billable Clocked calls**. GitHub Actions runs an offline-only test workflow on commits.

## API routes

- `GET /` — light-first public landing page, including a real interactive fictional policy preview.
- `GET /studio` — complete interactive Ripple workspace with optional dark mode.
- `GET /assets/*` — CSS/JS, favicon and fictional sample PDF files.
- `GET /api/demo` — deterministic fictional cohort; no Clocked calls.
- `GET /api/health` — safe health status; public live mode deliberately disabled.
- `POST /api/parse-pdf` — request-only constrained PDF text extraction; no Clocked calls.
- `/api/analyze`, `/api/internal/verify-clocked`, `/api/internal/pdf-proof` — *protected administrative API*. An expiring verifier token is required and all are excluded from public OpenAPI docs. The latter two consume credits **only when privately authorized**.

Read [security and credit controls](docs/SECURITY_REVIEW.md) before invoking these routes. Do not put secret tokens in screenshots, GitHub, logs, documentation, or the frontend.

## Design and engineering

- Single FastAPI service deployed to Vercel; accessible without login. Optional alternate `render.yaml` provided.
- Responsive light-first UI, with deliberate keyboard activation, saved dark-mode preference and reduced-motion support.
- Only explicit, supported requirements create automatic decisions. Unknown values and unsupported scope/exception clauses become `review`.
- API responses are separated from deterministic calculations; any SDK-reported credits are shown only when actually available.
- JSON evidence report and standalone HTML case reports. Source evidence is never faked from hypothetical Rule Lab values.
- Persistent development checkpoints in `checkpoint.json` and `docs/BUILD_CHECKPOINT.md`. Coding agents should start with `AGENTS.md`.

## Current verification status

**Automated local tests and offline browser checks:** passed (see the current checkpoint).  
**Public site:** user-confirmed light-mode UI; latest GitHub production commit must be checked after each push.  
**Live Clocked responses:** the key exists as Sensitive Vercel metadata; authenticated responses remain **unverified** unless `docs/VERIFICATION_RESULTS.md` states otherwise.  
**Challenge submission:** *not yet submitted by the assistant.* See the [submission checklist](docs/SUBMISSION.md).

**Responsible-use note:** This is a prototype demonstrating the consequences of *fictional* policy changes. It must not be used for actual scholarship awards, legal decisions, benefits determinations, or financial decisions without substantially more validation, governance, review, and controls.

## Optional one-minute screen capture

`python -m scripts.record_demo` records a **synthetic offline** browser walkthrough on a Linux desktop with `xvfb-run`, Chromium and `ffmpeg`. Use:

```bash
xvfb-run -a -s "-screen 0 1440x900x24" env CHROMIUM_PATH=/usr/bin/chromium python -m scripts.record_demo
```

The separately delivered `Ripple_Judge_Walkthrough.mp4` is a 61-second visual demonstration with no voiceover; `docs/JUDGE_DEMO.md` provides a spoken narration. This is not evidence of authenticated Clocked responses.

## Credit-free custom policy preview (audited 2026-11-09)

The public **Preview policy changes** action updates the fictional cohort using the user's uploaded or pasted policy texts without an external Clocked request. It supports only **one explicitly worded minimum GPA and one USD annual household-income ceiling per document**. Unknown rules, extra requirements and ambiguities produce **Needs review**. This heuristic is not Clocked extraction; do not represent its results as authenticated API evidence. Run `python -m pytest -q` (45 passing tests) and `CHROMIUM_PATH=/usr/bin/chromium python -m scripts.fullstack_smoke` to exercise the real FastAPI handlers through the browser without paid calls.

For actual authenticated Clocked verification, follow `docs/SECURE_API_SETUP.md`: temporary privately configured verifier, controlled requests against fictional policy data, then immediate disablement. No real response has been confirmed yet.