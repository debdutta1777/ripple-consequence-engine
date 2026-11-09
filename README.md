# Ripple — The Consequence Engine

**Don't just compare what changed. Discover who it changes.**

An evidence-first hackathon prototype for the Clocked Build Challenge. Compare two scholarship-policy versions, see which **synthetic** applicants change eligibility, investigate precise rule thresholds, and try counterfactuals. Built specifically for the challenge, with a narrow deterministic rules engine rather than broad, unverifiable AI conclusions.

> **Not an actual scholarship decision service.** This prototype supports only an explicit minimum GPA and an explicit maximum annual household income. Missing, ambiguous, contradictory, exception-bearing, or otherwise unsupported policy requirements must be sent to human review. All names, cases, and policies in the default demonstration are invented.

## Features

- Light-first responsive impact dashboard with an optional persistent dark-mode toggle, no JS build step and system-font fallbacks.
- Filterable applicant cards, a direct **Explore decision flips** journey, and plain-language explanations with source navigation.
- Honest UX that signals when policy text has been edited but not re-analyzed, and disables paid live analysis until securely enabled.
- One-click sample with 16 fictional applicants and two fictional policy versions.
- Live Clocked API pathway via a backend-managed secret (`ENABLE_LIVE=true`), never embedding an API key in the browser.
- Clocked **Extract**: reads verbatim threshold evidence from each policy.
- Clocked **Compare**: identifies duplications and conflicts between policy versions; the raw API response is available through **Inspect API trace**.
- Clocked **Rerank**: ranks the relevance of rule excerpts to eligibility changes.
- Deterministic old/new evaluation + five explicit outcomes: lost, gained, retained, excluded, needs review.
- Interactive case what-if controls (GPA and income) with *client-side* deterministic recalculation; no hidden paid API calls.
- Raw evidence JSON download and a clear synthetic vs. live status badge.
- Testable, fail-closed logic: unsupported or unverified rules are not silently classified as eligible.

## Running locally

Requires Python 3.9+.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. The synthetic demo works without a key.

### Enable actual Clocked calls

```bash
# Linux / macOS
export CLOCKED_API_KEY='your-real-secret'
export ENABLE_LIVE=true
export MAX_LIVE_ANALYSES=1  # controlled test only
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
$env:CLOCKED_API_KEY='your-real-secret'
$env:ENABLE_LIVE='true'
$env:MAX_LIVE_ANALYSES='1'  # controlled test only
uvicorn app.main:app --reload
```

In the dashboard, choose **Run Clocked analysis** to process the policy texts using Clocked. `GET /api/health` exposes whether live integration is enabled, without revealing the key.

The SDK is pinned to `clocked-sdk==0.7.0` as documented at https://pypi.org/project/clocked-sdk/.

### API routes

- `GET /` — static app
- `GET /api/demo` — offline deterministic fixture (never calls Clocked)
- `GET /api/health` — health and live-enabled flag
- `POST /api/analyze` — live Clocked extraction/comparison/reranking + deterministic impact on provided applicants

Example live request:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "old_policy": "Eligibility requires a minimum cumulative GPA of 3.2. Annual household income must not exceed $50,000.",
    "new_policy": "Eligibility requires a minimum cumulative GPA of 3.5. Annual household income must not exceed $60,000.",
    "applicants": [{"id":"A01","name":"Applicant 01","gpa":3.3,"income":36000}]
  }'
```

API calls are made only on explicit live analysis, not on every slider change. The backend validates input lengths, applicant ranges, and a process-level live request budget (`MAX_LIVE_ANALYSES`, default **0 (locked)**). For a production public service add persistent per-IP rate limiting and access control. The cost guard is deliberately simple and resets on process restart; deployment concurrency may multiply the budget.

## Evidence integrity and limitations

Clocked's **Compare** endpoint detects cross-document conflicts and duplicates; it is not a general-purpose policy compiler. **Extract** is asked for two *verbatim* threshold phrases. Our adapter rejects extracted text absent from the source and rejects fields with multiple candidate numbers. The engine evaluates *only* these two requirements and stops when a field is not verified. Exceptions, disjunctions, alternate currencies, temporal conditions, differing scales, and scope restrictions are **out of scope**. A production-ready version needs a typed rule schema, explicit verification of exceptions and currencies, human approval, adversarial tests, and true source-span highlighting.

Clocked returns evidence positions and marked PDFs on supported endpoints; this starter uses text excerpts and the raw trace because it accepts plain text. PDF uploads and annotated-PDF previews are the next milestone.

> **Live API calls have not been verified against the user's Clocked account.** The API key was confirmed present as a Sensitive Vercel Production variable on November 9, 2026, but live mode is still locked and no authenticated response has been inspected. The module is written to the public SDK examples, and unit tests use mocked responses. Before submission, run with a real key, inspect the raw field shapes, and adjust extraction parsing if the live response differs.

## Browser visual smoke test

The browser test is isolated from the real API; it stubs the `/api/demo` fixture but exercises actual Chromium UI interactions (theme, filters, decision flips, evidence selection and responsive widths):

```bash
pip install -r requirements-dev.txt
CHROMIUM_PATH=/usr/bin/chromium python -m scripts.browser_smoke
```

`fixtures/screenshots/` contains local visual captures. Actual live Clocked verification remains a separate blocked task until a backend-only key is configured.

## Testing

```bash
pip install pytest
PYTHONPATH=. pytest -q
```

Tests cover loss and gain, inclusive boundaries, review on missing evidence, rejection of fabricated source values, and the four expected Clocked method invocations.

## Deployment

The site is structured for a single FastAPI deployment on Vercel (`main.py` exports the app) and retains `render.yaml` as an alternative. GitHub changes can automatically trigger Vercel deployments when the integration is correctly connected. Keep the key in hosting environment settings, never in source control. For a planned one-off test, explicitly set `ENABLE_LIVE=true` and a positive `MAX_LIVE_ANALYSES` in deployment settings, then redeploy. **Do not leave an unauthenticated public live endpoint enabled**: the in-memory counter is not a reliable spending cap across serverless instances. Add proper authentication and durable rate enforcement before allowing public judge-triggered live analysis. If live isn't configured, the sample remains fully usable without login.

## Hackathon entry checklist

- [ ] Publish a public repository **with genuine commit history dated within the hackathon window**. Only submit work genuinely developed during the allowed timeframe.
- [ ] Connect a real Clocked key and demonstrate the `Clocked Extract`, `Compare`, and `Rerank` calls.
- [ ] Add a second, more challenging policy scenario and relevant tests.
- [ ] Implement PDF uploads and click-to-highlight, if time allows.
- [ ] Test desktop and mobile, export, error handling, live endpoint latency, and rate limits.
- [ ] Deploy without judge login, or provide working test access if login is necessary.
- [ ] Record a concise video: old/new policies → changed cohort → single case → source proof → counterfactual → API trace.
- [ ] Include setup instructions, source citations, all team details, and a clear explanation of which endpoint outputs affect outcomes.
- [ ] Submit through the Clocked challenge page by **November 10, 2026, 11:59 PM Eastern (November 11, 10:29 AM India)**.

## Project structure

```text
app/
  main.py             # Routes, status, execution budget
  demo.py             # Explicitly fictional dataset
  rules.py            # Transparent deterministic evaluator
  clocked_adapter.py  # Official SDK integrations & evidence validation
web/
  index.html          # Visual product
  styles.css          # UI and responsive design
  app.js              # Interactive flows, what-if and export
fixtures/              # Visual QA screenshots (when generated)
tests/                 # Unit and mocked-integration tests
render.yaml            # One-click deployment blueprint
```

Built for Clocked Build Challenge 2026. License: MIT, see LICENSE.


## PDF text preview (P04.1, independently tested)

On the Impact Studio page you can now choose **Upload previous PDF** or **Upload updated PDF**. A PDF is accepted only when it is a selectable-text PDF of at most **2 MB**, at most **12 pages**, and at most **12,000 extracted characters**. It is extracted transiently by `/api/parse-pdf`; the original PDF is not stored in the project's database, and **preview consumes zero Clocked API calls**. Scanned/image PDFs and password-protected PDFs return an explicit error (OCR is not available yet).

Downloadable, wholly fictional PDF examples are provided in `web/samples/`. The extracted text is shown in the normal policy editors for human review. **Uploading a PDF does not recompute the eligibility outcomes**. If text changes, Ripple shows a stale-analysis warning and blocks evidence jumps until a new analysis is performed. That separate live action currently makes **up to four Clocked API requests** (Extract twice, Compare, Rerank) only when the server secret and `ENABLE_LIVE=true` are configured.

This milestone does not yet include Clocked PDF-mode extraction, PDF annotations/highlights, or any real Clocked endpoint validation. `MAX_LIVE_ANALYSES` is a per-process safety limit, **not** a global hard budget across Vercel serverless instances; keep live analysis disabled until you are ready to monitor API usage. Never upload real student personal data to the hackathon demo.


## P03.1 — Vercel secret metadata confirmed, usage guard strengthened

The `CLOCKED_API_KEY` variable exists as a **Sensitive** value in Vercel Production. The secret itself has never been viewed or copied. For safety, the default `MAX_LIVE_ANALYSES` is now **0** and the dashboard will not enable live analysis until `ENABLE_LIVE=true` and an explicit positive budget are both configured. This is a local/process soft budget only and does not securely limit total expenditure across Vercel serverless instances.

When Clocked analysis is deliberately run, the server records SDK-reported `credits`, `cost_usd`, and `model_ms` per endpoint. The UI and evidence trace display credits only if metadata is actually returned; otherwise it reports an unknown cost instead of making one up. No additional Clocked requests are needed for this telemetry.