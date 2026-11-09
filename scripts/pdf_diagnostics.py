"""Diagnostic-only one-request Clocked PDF marking metadata check; no key disclosure."""
from pathlib import Path
import os, sys
from clocked_sdk import Clocked
from app.clocked_adapter import _root_json
from app.pdf_ingest import parse_policy_pdf

samples=Path("web/samples")
inputs=[("previous",samples/"judge-policy-2025.pdf"),("current",samples/"judge-policy-2026.pdf")]
for name,p in inputs:
    src=parse_policy_pdf(p.read_bytes())
    print("SOURCE",name,"pages",src["page_count"],"characters",src["characters"])
if not os.environ.get("CLOCKED_API_KEY"):
    raise SystemExit("Missing Actions secret")
with Clocked(timeout=90,max_attempts=1) as client:
    res=client.compare(documents=[{"id":name,"pdf":p.read_bytes()} for name,p in inputs],return_text=True,return_pdf="highlight")
data=_root_json(res)
print("VERDICT",data.get("verdict"),"CONFLICTS",len(data.get("conflicts") or []),"CREDITS",getattr(res,"credits",None))
pdfs=data.get("pdf")
print("PDF_RESULTS_COUNT",len(pdfs) if isinstance(pdfs,list) else type(pdfs).__name__)
for p in pdfs if isinstance(pdfs,list) else []:
    m=p.get("marked") or {}
    print("MARKER",p.get("document"),"mode",p.get("mode"),"pages",p.get("pages"),"spans",m.get("spans"),"marked",m.get("marked"),"error",m.get("error"),"has_document",bool(m.get("document")))
    try:
        val=res.marked_pdf(document=p.get("document"))
        print("PDF_DECODED",p.get("document"),len(val) if isinstance(val,bytes) else "not_bytes")
    except (ValueError,TypeError,KeyError,AttributeError) as e:
        print("PDF_MISSING",p.get("document"),type(e).__name__)
