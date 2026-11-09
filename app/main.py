"""Ripple app: one-service deployment, no frontend build step."""
import os
import threading
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv
from app.demo import make_demo, APPLICANTS
from app.clocked_adapter import analyze_live
from app.pdf_ingest import parse_policy_pdf, PdfInputError, MAX_PDF_BYTES

ROOT = Path(__file__).resolve().parent.parent
# Local configuration only; never serve or commit the real .env file.
# Environment variables supplied by the hosting provider take precedence.
load_dotenv(ROOT / ".env", override=False)
app = FastAPI(title="Ripple Consequence Engine", version="0.1.0")
app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")

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

@app.get("/api/health")
def health():
    return {"status": "ok", "live_enabled": live_ready()}

@app.get("/api/demo")
def demo():
    return make_demo()

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

@app.post("/api/analyze")
async def analyze(request: Request, payload: AnalyzeRequest):
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