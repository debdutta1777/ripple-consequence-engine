# Secure Clocked connection and one-time verification

The real `CLOCKED_API_KEY` is stored as a **Sensitive** Production environment variable in the user's Vercel project. Its **metadata was verified without decrypting the key**. Never paste it into ChatGPT, GitHub, terminal output, the client-side JavaScript or a downloadable artifact.

## Public site defaults

```dotenv
CLOCKED_API_KEY=               # real value only in Vercel's Sensitive secret UI
ENABLE_LIVE=false
MAX_LIVE_ANALYSES=0
ENABLE_VERIFICATION=false
RIPPLE_VERIFY_TOKEN=           # independently generated 32+ character secret, not public
RIPPLE_VERIFY_UNTIL=0          # UNIX epoch seconds, short window
```

The site intentionally reports `live_enabled: false` in `/api/health`, because the public demo is credit-free. Even if an owner enables `ENABLE_LIVE`, the costly `/api/analyze` route still requires the same expiring administrator verification token. **A per-server-process counter is not a global Vercel billing quota**; do not treat it as one.

## Controlled one-time Clocked smoke

1. Generate a high-entropy random token privately (e.g. Python `secrets.token_urlsafe(40)`) and store it as a Vercel **Sensitive** Production variable named `RIPPLE_VERIFY_TOKEN`. Never commit or print it.
2. Set `ENABLE_VERIFICATION=true` (Config) and `RIPPLE_VERIFY_UNTIL=<current epoch + 10 min>` (Config) in Production.
3. Redeploy the current reviewed source to make variables effective.
4. The authorized owner issues **one** `POST /api/internal/verify-clocked` with header `X-Ripple-Verify: <token>` using a trusted client. It sends only the two fictional sample policies and 16 fictional applicants. Four potential billable calls: Extract ×2, Compare ×1, Rerank ×1. SDK retries are disabled for this short test.
5. Record the sanitized result (rule thresholds, endpoint result counts, `credits`/`cost_usd` if reported). If any part is missing, record `needs_review`—**do not fabricate a successful result**.
6. Optional: issue one further `POST /api/internal/pdf-proof` with the same header to obtain ZIP output from Clocked Compare PDF with `return_pdf="highlight"`. That may consume an additional request. Marked PDFs are included only if the SDK genuinely returned them.
7. Immediately set `ENABLE_VERIFICATION=false` and redeploy. A short token expiration is a safety net; it is not a durable global consumption quota.

If private HTTP execution or Vercel environment permissions are unavailable, **do not** retrieve the user's key to compensate. Leave live verification pending and keep the public demo safe. The user may carry out the one-time protected test from their own authenticated environment.

## Local development

In an untracked local `.env` file, set the key without sharing it. Use `python -m pytest -q` and `python -m scripts.browser_smoke` freely: neither makes real Clocked calls. The direct `python -m scripts.smoke_clocked --run` script makes four real calls and requires explicit approval; omit `--run` for its safe dry-run.

## After a successful run

Update `docs/VERIFICATION_RESULTS.md`, `checkpoint.json` and `docs/BUILD_CHECKPOINT.md`. Ensure screenshots, public JSON and Git commits include **no secrets**. Rotate the verifier token or revoke it; do not make it a permanent admin credential.