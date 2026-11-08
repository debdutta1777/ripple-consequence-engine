# Ripple: Vercel deployment and secure Clocked configuration

## Status

Vercel connection was confirmed on 2026-11-09, but programmatic project
creation returned 403 Forbidden. The project has **not** been deployed.

## Deployment source

The project root now contains `main.py` exporting `app` from `app.main`,
which allows Vercel's FastAPI framework detection while preserving the
existing `uvicorn app.main:app` local workflow. The static frontend is
served by the same FastAPI application at `/` and `/assets/*`.

## Required one-time Vercel dashboard steps

1. Visit https://vercel.com/new and import the Ripple GitHub repository
   once the repository is created. Choose the **FastAPI** framework and
   leave Root Directory at the repository root.
2. In Project > Settings > Environment Variables, add `CLOCKED_API_KEY` as
   a **Sensitive** value for Production (and Preview only if needed). Never
   paste the key in a chat, commit, screenshot, or logs.
3. Set `ENABLE_LIVE=false` at first. When ready for authentic testing, set
   `ENABLE_LIVE=true` only for controlled tests, and keep `MAX_LIVE_ANALYSES`
   conservative. A process-local request counter is not sufficient for
   production budget control under serverless concurrency.
4. Trigger a new deployment after changing environment variables.
5. Check `/api/health`; it must never return the key. Exercise `/api/demo`
   first, then a controlled `/api/analyze` request with synthetic policies.
6. Before exposing publicly, implement durable rate limits and protect
   the live endpoint from untrusted users, since each live call costs credits.

## Secrets and deployments

`.env`, `.env.*`, and `.vercel/` are git-ignored. Vercel environment
variables remain server-side: do not use a public `NEXT_PUBLIC_` prefix.
The browser must never receive the Clocked secret. Do not print full
API errors or live request headers into public logs.

## Current limitation

Clocked integration is present but NOT yet validated against a real key;
PDF upload/annotation remains a later phase. This document intentionally
makes no claim of a successful Vercel deployment.
