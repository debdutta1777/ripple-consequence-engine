"""One-shot real Clocked PDF comparison proof using two fictional policy PDFs.
Run only in a reviewed GitHub Actions workflow with CLOCKED_API_KEY as a secret.
Outputs sanitized metadata and only annotated fictional PDFs. Exactly one SDK
Compare call, no retries, no user documents or API keys in reports.
"""
from __future__ import annotations

import hashlib
import json
import os
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from pypdf import PdfReader

from app.clocked_pdf import create_marked_comparison


def main() -> None:
    if not os.environ.get("CLOCKED_API_KEY"):
        raise SystemExit("FAIL: CLOCKED_API_KEY repository Actions secret not available.")
    from clocked_sdk import Clocked

    samples = Path("web/samples")
    previous = (samples / "previous-policy.pdf").read_bytes()
    current = (samples / "updated-policy.pdf").read_bytes()
    with Clocked(timeout=90, max_attempts=1) as client:
        bundle, manifest = create_marked_comparison(client, previous, current)

    outdir = Path("pdf-proof-output")
    outdir.mkdir(exist_ok=True)
    evidence = []
    with ZipFile(BytesIO(bundle)) as archive:
        filenames = set(archive.namelist())
        for label in ("previous", "current"):
            name = f"{label}-clocked-highlighted.pdf"
            if name not in filenames:
                evidence.append({"document": label, "marked_pdf": False, "annotations": 0})
                continue
            payload = archive.read(name)
            if not payload.startswith(b"%PDF-"):
                raise SystemExit(f"FAIL: {label} marked output is not a PDF.")
            reader = PdfReader(BytesIO(payload))
            annotation_count = 0
            for page in reader.pages:
                annotation_refs = page.get("/Annots")
                if annotation_refs:
                    refs = annotation_refs.get_object() if hasattr(annotation_refs, "get_object") else annotation_refs
                    annotation_count += len(refs)
            (outdir / name).write_bytes(payload)
            evidence.append({
                "document": label,
                "marked_pdf": True,
                "pages": len(reader.pages),
                "annotations": annotation_count,
                "sha256": hashlib.sha256(payload).hexdigest(),
            })

    safe_report = {
        "source": "Bundled fictional scholarship-policy PDFs only",
        "api": "Clocked Compare",
        "sdk_calls": 1,
        "pdf_highlight_mode": "highlight",
        "verdict": manifest.get("verdict"),
        "conflict_count": manifest.get("conflict_count"),
        "usage": manifest.get("usage"),
        "documents": evidence,
        "verified": any(item["annotations"] > 0 for item in evidence),
    }
    (outdir / "verification-report.json").write_text(json.dumps(safe_report, indent=2), encoding="utf-8")
    print("REAL CLOCKED NATIVE PDF PROOF")
    print("Compare verdict:", safe_report["verdict"])
    print("Conflicts:", safe_report["conflict_count"])
    print("SDK-reported credits:", (safe_report.get("usage") or {}).get("credits"))
    print("Marked-PDF validation:", json.dumps(evidence))
    if not safe_report["verified"]:
        raise SystemExit("FAIL: Clocked response did not yield a PDF containing annotations.")
    print("PASS: Real Clocked produced at least one valid PDF with native annotations.")


if __name__ == "__main__":
    main()
