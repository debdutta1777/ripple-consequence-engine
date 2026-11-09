# Ripple deployment on Vercel

**Public website:** https://ripple-consequence-engine.vercel.app/  
**GitHub source:** https://github.com/debdutta1777/ripple-consequence-engine  
**Framework:** FastAPI, with entrypoint `main.py` re-exporting `app.main:app`.

The user created a Vercel project and confirmed the light-mode site is publicly accessible. The latest release must still be checked after each main-branch GitHub commit, because a successful push is not proof of a successful production build.

## Standard path

1. Vercel → Project → Git → confirm the linked GitHub repository and `main` branch.
2. Vercel → Deployments → verify the latest commit SHA is Ready, Production, and assigned to the stable public alias.
3. Vercel → Settings → Environment Variables → retain `CLOCKED_API_KEY` as **Sensitive** / Production. Keep `ENABLE_LIVE=false`, `MAX_LIVE_ANALYSES=0` and `ENABLE_VERIFICATION=false` unless performing an explicitly planned, short, authorized test.
4. Visit `/`, `/api/health` and `/api/demo` in a fresh browser. Test a fictional sample PDF upload and check no paid requests were made.
5. If the deployment failed, read its **Build Logs** and **Runtime Logs**; do not post raw environment values or logs with secrets into issues or chat.

See [SECURE_API_SETUP.md](SECURE_API_SETUP.md) for one-time protected Clocked verification. See [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for known limitations.

## Reproducing locally

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --check web/app.js
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The public site requires no login and no API key to explore the fictional scenario.