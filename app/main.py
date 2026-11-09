"""Ripple app: one-service deployment, no frontend build step."""
import os
import threading
import hmac
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv
from app.demo import make_demo, APPLICANTS, OLD_TEXT, NEW_TEXT
from app.clocked_adapter import analyze_live
from app.pdf_ingest import parse_policy_pdf, PdfInputError, MAX_PDF_BYTES
from app.clocked_pdf import create_marked_comparison
from app.offline_preview import preview_policies

ROOT = Path(__file__).resolve().parent.parent
# Local configuration only; never serve or commit the real .env file.
# Environment variables supplied by the hosting provider take precedence.
load_dotenv(ROOT / ".env", override=False)
app = FastAPI(title="Ripple Consequence Engine", version="0.1.0")
app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

class Applicant(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    gpa: float = Field(ge=0, le=4)
    income: int = Field(ge=0, le=50_000_000)

class AnalyzeRequest(BaseModel):
    old_policy: str = Field(min_length=1, max_length=12_000)
    new_policy: str = Field(min_length=1, max_length=12_000)
    applicants: list[Applicant] = Field(default_factory=list, max_length=30)

_lock = threading.Lock()
_usage = {"total": 0}


def live_budget() -> int:
    """A fail-closed, per-process soft cap. This is NOT a global serverless quota."""
    try:
        return max(0, min(25, int(os.getenv("MAX_LIVE_ANALYSES", "0"))))
    except (ValueError, TypeError):
        return 0


def live_ready() -> bool:
    return bool(os.getenv("CLOCKED_API_KEY")) and os.getenv("ENABLE_LIVE") == "true" and live_budget() > 0

@app.get("/")
def index():
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/studio")
def studio():
    return FileResponse(ROOT / "web" / "studio.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "live_enabled": False, "demo_only": True, "version": "0.9.0"}

@app.get("/api/demo")
def demo():
    return make_demo()

@app.post("/api/preview")
def local_preview(payload: AnalyzeRequest):
    """Free deterministic preview. Never uses or exposes Clocked credentials."""
    people = [p.model_dump() for p in payload.applicants] or APPLICANTS
    return preview_policies(payload.old_policy, payload.new_policy, people)


@app.post("/api/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    """Preview selectable PDF text without using Clocked credits or storing it."""
    try:
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(415, "Choose a PDF file with a .pdf extension.")
        if file.content_type not in ("application/pdf", "application/octet-stream", None):
            raise HTTPException(415, "Only PDF files are supported.")
        payload = await file.read(MAX_PDF_BYTES + 1)
        try:
            return parse_policy_pdf(payload)
        except PdfInputError as exc:
            raise HTTPException(422, str(exc)) from exc
    finally:
        await file.close()

def require_verifier(request: Request) -> None:
    """Private admin-only verification gate; never enable for public visitors.

    Clocked API credits are protected by a secret and a short, explicit window.
    This is *not* a persistent global rate limiter. Only fictional sample data
    can be sent from this route, so no user-supplied private policy is exposed.
    """
    key = os.getenv("RIPPLE_VERIFY_TOKEN", "")
    supplied = request.headers.get("x-ripple-verify", "")
    try:
        expires = int(os.getenv("RIPPLE_VERIFY_UNTIL", "0"))
    except ValueError:
        expires = 0
    if (
        os.getenv("ENABLE_VERIFICATION") != "true"
        or not key or len(key) < 32
        or not supplied or not hmac.compare_digest(key, supplied)
        or expires <= int(time.time())
    ):
        raise HTTPException(404, "Not found")


@app.post("/api/internal/verify-clocked", include_in_schema=False)
async def verify_clocked(request: Request):
    """Runs four billed requests only with a temporary, private verifier key.

    The administrator must explicitly enable the short verification window in
    Vercel. After inspecting the sanitized results, disable the flag. This
    endpoint is never reachable with the public website alone.
    """
    require_verifier(request)
    try:
        from clocked_sdk import Clocked
        def run():
            with Clocked(timeout=90, max_attempts=1) as client:
                return analyze_live(client, OLD_TEXT, NEW_TEXT, APPLICANTS)
        result = await run_in_threadpool(run)
        policies = result["policies"]
        matched = (
            policies["old"].get("min_gpa") == 3.2
            and policies["old"].get("max_income") == 50000
            and policies["new"].get("min_gpa") == 3.5
            and policies["new"].get("max_income") == 60000
        )
        return {
            "status": "verified" if matched else "needs_review",
            "mode": "live",
            "endpoint_calls": result["api_calls"],
            "extracted_policies": {
                label: {"min_gpa": data["min_gpa"], "max_income": data["max_income"]}
                for label, data in policies.items()
            },
            "comparison_verdict": result["comparison"].get("verdict"),
            "comparison_conflicts": len(result["comparison"].get("conflicts", [])),
            "reranked_items": len(result.get("relevance", [])),
            "cohort_counts": result["impact"]["counts"],
            "usage": result["usage"],
            "disclaimer": "This verifies only the two fictional, explicit GPA/income policies; custom PDF interpretation remains unverified.",
        }
    except Exception as exc:
        # No upstream responses, credentials, or exception text leave this route.
        raise HTTPException(502, "Clocked verification failed. Examine secure server logs without revealing secrets.") from exc


@app.post("/api/internal/pdf-proof", include_in_schema=False)
async def verified_pdf_proof(request: Request):
    """One extra billed Compare request; restricted to static fictional PDFs."""
    require_verifier(request)
    try:
        from clocked_sdk import Clocked
        previous = (ROOT / "web" / "samples" / "previous-policy.pdf").read_bytes()
        updated = (ROOT / "web" / "samples" / "updated-policy.pdf").read_bytes()
        def run():
            with Clocked(timeout=90, max_attempts=1) as client:
                return create_marked_comparison(client, previous, updated)
        bundle, manifest = await run_in_threadpool(run)
        return Response(
            bundle,
            media_type="application/zip",
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": 'attachment; filename="ripple-clocked-pdf-proof.zip"',
                "X-Ripple-Marked-Count": str(sum(int(x["highlighted"]) for x in manifest["documents"].values())),
            },
        )
    except Exception as exc:
        raise HTTPException(502, "Could not create a Clocked PDF comparison pack. No unverified annotations were generated.") from exc


@app.post("/api/analyze", include_in_schema=False)
async def analyze(request: Request, payload: AnalyzeRequest):
    # No public paid endpoint without persistent global quota infrastructure.
    # Authenticated administrative calls are possible only in a short window.
    require_verifier(request)
    if not live_ready():
        raise HTTPException(503, "Live analysis is locked. The administrator must configure an API key, explicitly enable live mode, and set a positive analysis budget. The synthetic demo remains available.")
    with _lock:
        max_calls = live_budget()
        if _usage["total"] >= max_calls:
            raise HTTPException(429, "This public demo has reached its live-analysis budget. Try the fully working synthetic preview.")
        _usage["total"] += 1
    try:
        from clocked_sdk import Clocked
        people = [p.model_dump() for p in payload.applicants] or APPLICANTS
        def run():
            with Clocked() as client:
                return analyze_live(client, payload.old_policy, payload.new_policy, people)
        return await run_in_threadpool(run)
    except Exception as exc:
        # Never expose the Clocked key or service internals to public callers.
        raise HTTPException(502, "Clocked request failed or did not return usable evidence. Please retry using shorter policy text, or use the synthetic demo.") from exc