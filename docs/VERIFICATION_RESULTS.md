# Actual Clocked API verification results

**Status: NOT YET VERIFIED.** The `CLOCKED_API_KEY` Vercel variable has been confirmed as a Sensitive Production secret by metadata, but no authenticated SDK response is established by the current local test suite.

- Requests paid by this repository's development tests: **0** (all tests are offline and mock-dependent).
- Intended controlled run: Extract ×2, Compare ×1, Rerank ×1 = four SDK requests.
- Optional separate PDF highlight test: Compare PDF ×1.
- Billing values: unknown until the actual SDK reports them.
- Do **not** interpret a local `FakeClocked` test as production Clocked verification.

This file should be updated only after an authenticated, controlled test has actually succeeded. If the test fails, record the failure and recommended remediation instead.

## Full release audit — 2026-11-09

- `python -m pytest -q`: **45 passed**.
- `CHROMIUM_PATH=/usr/bin/chromium python -m scripts.browser_smoke`: **PASS**, isolated mock API browser test.
- `CHROMIUM_PATH=/usr/bin/chromium python -m scripts.fullstack_smoke`: **PASS**, browser events routed through actual local FastAPI TestClient handlers, with successful PDF parse and strict offline preview.
- `node --check web/app.js`: **PASS**.
- `CLOCKED_API_KEY` Sensitive Production existence verified from Vercel environment variable *metadata only*; actual decrypted secret not accessed.
- Actual Clocked SDK request: **NOT EXECUTED**. Protected route requires short-lived administrator verifier secret. The connected Vercel deployment HTTP fetch returned authorization errors. This report must not claim success.
- Production release metadata must be checked again after the audit fix commit. A previous release was READY at the stable alias; direct public HTTP route fetch from tools is blocked.