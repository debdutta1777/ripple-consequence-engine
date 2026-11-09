# Actual Clocked API verification results

**Status: NOT YET VERIFIED.** The `CLOCKED_API_KEY` Vercel variable has been confirmed as a Sensitive Production secret by metadata, but no authenticated SDK response is established by the current local test suite.

- Requests paid by this repository's development tests: **0** (all tests are offline and mock-dependent).
- Intended controlled run: Extract ×2, Compare ×1, Rerank ×1 = four SDK requests.
- Optional separate PDF highlight test: Compare PDF ×1.
- Billing values: unknown until the actual SDK reports them.
- Do **not** interpret a local `FakeClocked` test as production Clocked verification.

This file should be updated only after an authenticated, controlled test has actually succeeded. If the test fails, record the failure and recommended remediation instead.