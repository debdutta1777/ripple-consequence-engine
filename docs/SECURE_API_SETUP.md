# Safely connect your Clocked API key

**Do not paste your API key into ChatGPT or a GitHub issue.** The current chat does not provide a dedicated secret-vault input that can be used for the local runtime. The key belongs only in a local ignored environment file, a process environment variable, or your deployment provider's secret settings.

## Windows PowerShell (recommended for this project)

1. Open a terminal in the `ripple-consequence-engine` project directory.
2. Copy the provided template: `Copy-Item .env.example .env`.
3. Open it locally with `notepad .env`. Set `CLOCKED_API_KEY=<your secret>`. Keep `ENABLE_LIVE=false` and `MAX_LIVE_ANALYSES=0` until a controlled live test is approved. Save the file **on your computer only**.
4. Install dependencies: `py -m pip install -r requirements.txt`.
5. Start the backend: `py -m uvicorn app.main:app --reload`.
6. Visit `http://127.0.0.1:8000/api/health`. It should show `"live_enabled": false` until you explicitly opt into a test with `ENABLE_LIVE=true` and a positive `MAX_LIVE_ANALYSES` value.
7. Open `http://127.0.0.1:8000` and use **Analyze live** only when ready to spend credits.

The local `.env` is ignored by Git, and `app/main.py` loads it at startup. This is practical local secret storage, though anyone with access to your local files/account could read it. For more restrictive security, use your OS's secret manager or transient process environment instead.

## Hosting

On Vercel, set `CLOCKED_API_KEY` as a **Sensitive** Production environment variable. Keep `ENABLE_LIVE=false` while testing the free demo. Only briefly turn on `ENABLE_LIVE=true` with `MAX_LIVE_ANALYSES=1` for a planned test; disable it immediately afterward and redeploy so the change takes effect. Never commit `.env`. Hosting values take priority over local `.env`.

**Important:** `MAX_LIVE_ANALYSES` is an in-process convenience guard, not a global or durable spending cap; Vercel can create fresh serverless instances. Never leave a public, unauthenticated live endpoint enabled relying on this counter alone. Use an authenticated endpoint and durable quota enforcement for any ongoing public live traffic.

## Safety checklist

- `.env` must never be included in the download ZIP, Git repo, screenshots, test snapshots or debug logs.
- Never add `CLOCKED_API_KEY` to the web frontend, frontend build variables, browser local storage or request bodies.
- Rotate the key in Clocked if you accidentally expose it.
- Live API behavior is **not yet validated**; integration must be tested after you configure the key.