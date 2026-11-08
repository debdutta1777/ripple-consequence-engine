# Safely connect your Clocked API key

**Do not paste your API key into ChatGPT or a GitHub issue.** The current chat does not provide a dedicated secret-vault input that can be used for the local runtime. The key belongs only in a local ignored environment file, a process environment variable, or your deployment provider's secret settings.

## Windows PowerShell (recommended for this project)

1. Open a terminal in the `ripple-consequence-engine` project directory.
2. Copy the provided template: `Copy-Item .env.example .env`.
3. Open it locally with `notepad .env`. Set `CLOCKED_API_KEY=<your secret>` and `ENABLE_LIVE=true`. Save the file **on your computer only**.
4. Install dependencies: `py -m pip install -r requirements.txt`.
5. Start the backend: `py -m uvicorn app.main:app --reload`.
6. Visit `http://127.0.0.1:8000/api/health`. It should show `"live_enabled": true` without exposing the secret.
7. Open `http://127.0.0.1:8000` and use **Analyze live** only when ready to spend credits.

The local `.env` is ignored by Git, and `app/main.py` loads it at startup. This is practical local secret storage, though anyone with access to your local files/account could read it. For more restrictive security, use your OS's secret manager or transient process environment instead.

## Hosting

In Render, go to the web service's **Environment** settings; set `CLOCKED_API_KEY` as a secret and `ENABLE_LIVE=true`. Never commit or upload the `.env` file. Hosting environment values take priority over `.env`. Use `MAX_LIVE_ANALYSES` to limit the number of real runs the public demo process will accept (this is **not** a global durable rate limit).

## Safety checklist

- `.env` must never be included in the download ZIP, Git repo, screenshots, test snapshots or debug logs.
- Never add `CLOCKED_API_KEY` to the web frontend, frontend build variables, browser local storage or request bodies.
- Rotate the key in Clocked if you accidentally expose it.
- Live API behavior is **not yet validated**; integration must be tested after you configure the key.
