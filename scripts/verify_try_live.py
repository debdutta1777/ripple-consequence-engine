"""One controlled, real Clocked verification on the exact fresh Try It Yourself PDFs.

Runs only in manually authorized GitHub Actions with a repository secret.
Uploads PDFs through the public website endpoints, then authenticates against
Clocked with the SAME extracted text. Only fictional data is used; no secrets
or raw upstream responses are printed or included in the proof artifact.
"""
from __future__ import annotations

import json
import os
import sys
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import uuid4
from zipfile import ZipFile

from pypdf import PdfReader

from app.clocked_adapter import analyze_live
from app.clocked_pdf import create_marked_comparison
from app.demo import APPLICANTS
from app.pdf_ingest import parse_policy_pdf
from app.offline_preview import preview_policies

BASE_URL = os.getenv("RIPPLE_BASE_URL", "https://ripple-consequence-engine.vercel.app").rstrip("/")
EXPECTED_RULES = (3.25, 52000, 3.65, 66000)
EXPECTED_COUNTS = {"lost": 4, "gained": 2, "retained": 2, "excluded": 8, "review": 0}
FILES = [
    ("previous", Path("web/samples/judge-policy-2025.pdf")),
    ("updated", Path("web/samples/judge-policy-2026.pdf")),
]


def post_pdf(path: Path) -> dict:
    boundary = uuid4().hex
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        "Content-Type: application/pdf\r\n\r\n"
    ).encode("ascii") + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("ascii")
    req = Request(
        BASE_URL + "/api/parse-pdf", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": "Ripple-verification/1.0"}
    )
    with urlopen(req, timeout=45) as response:
        if response.status != 200:
            raise ValueError("Deployed PDF parser did not return 200")
        return json.load(response)


def post_preview(previous: str, updated: str) -> dict:
    body = json.dumps({"old_policy": previous, "new_policy": updated, "applicants": APPLICANTS}).encode("utf-8")
    req = Request(
        BASE_URL + "/api/preview", data=body, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "Ripple-verification/1.0"}
    )
    with urlopen(req, timeout=45) as response:
        if response.status != 200:
            raise ValueError("Deployed preview did not return 200")
        return json.load(response)


def policies_tuple(result: dict) -> tuple:
    return (
        result["policies"]["old"]["min_gpa"], result["policies"]["old"]["max_income"],
        result["policies"]["new"]["min_gpa"], result["policies"]["new"]["max_income"],
    )


def run() -> dict:
    if not os.getenv("CLOCKED_API_KEY"):
        raise RuntimeError("CLOCKED_API_KEY Actions secret is not configured")
    payloads = {name: path.read_bytes() for name, path in FILES}

    print("STAGE: public PDF upload")
    # Verify the public Try It Yourself endpoints, not only a TestClient mock.
    remote = {name: post_pdf(path) for name, path in FILES}
    local = {name: parse_policy_pdf(payloads[name]) for name, _ in FILES}
    for name in local:
        if remote[name]["text"] != local[name]["text"] or remote[name]["page_count"] != 1:
            raise ValueError(f"Public PDF extraction mismatch for {name}")
    print("STAGE: public PDF extraction passed; evaluating policies")
    deployed_result = post_preview(remote["previous"]["text"], remote["updated"]["text"])
    local_result = preview_policies(local["previous"]["text"], local["updated"]["text"], APPLICANTS)
    if deployed_result["mode"] != "offline" or policies_tuple(deployed_result) != EXPECTED_RULES:
        raise ValueError("Public Try It Yourself preview produced unexpected thresholds")
    if deployed_result["impact"]["counts"] != EXPECTED_COUNTS or local_result["impact"]["counts"] != EXPECTED_COUNTS:
        raise ValueError("Applicant transition counts do not match the fresh PDFs")

    print("STAGE: public two-PDF preview passed; invoking Clocked")
    # Same documents, separate controlled paid Clocked call: do not label the
    # public endpoint as Clocked-powered, as it explicitly uses local rules.
    from clocked_sdk import Clocked
    with Clocked(timeout=90, max_attempts=1) as client:
        live = analyze_live(client, remote["previous"]["text"], remote["updated"]["text"], APPLICANTS)
        zip_bytes, manifest = create_marked_comparison(client, payloads["previous"], payloads["updated"])

    print("STAGE: Clocked SDK calls returned; checking evidence")
    if policies_tuple(live) != EXPECTED_RULES:
        raise ValueError("Real Clocked extraction did not match policy text")
    if live["impact"]["counts"] != EXPECTED_COUNTS:
        raise ValueError("Real Clocked-derived impact differs from public deterministic preview")
    if not live["comparison"].get("verdict") or not live.get("relevance"):
        raise ValueError("Clocked Compare or Rerank returned insufficient evidence")

    print("STAGE: Clocked extracted rules and applicant impacts match")
    artifact_dir = Path("try-live-proof")
    artifact_dir.mkdir(exist_ok=True)
    annotations = {}
    with ZipFile(BytesIO(zip_bytes)) as archive:
        for name in ("previous", "current"):
            doc_name = f"{name}-clocked-highlighted.pdf"
            if doc_name not in archive.namelist():
                annotations[name] = None
                continue
            content = archive.read(doc_name)
            reader = PdfReader(BytesIO(content))
            n = 0
            for page in reader.pages:
                refs = page.get("/Annots") or []
                refs = refs.get_object() if hasattr(refs, "get_object") else refs
                n += len(refs)
            annotations[name] = n
            (artifact_dir / doc_name).write_bytes(content)
    marked_available = any(n and n > 0 for n in annotations.values())
    if not marked_available:
        print("NOTICE: Clocked Compare returned no native highlight spans for these formatted PDFs.")

    credits_text = (live.get("usage") or {}).get("credits")
    credits_pdf = (manifest.get("usage") or {}).get("credits")
    report = {
        "source": "Fresh fictional scholarship policy PDFs used in the public /try page",
        "url": BASE_URL + "/try",
        "public_preview_mode": "offline, no Clocked credits",
        "policies": {"old_gpa": EXPECTED_RULES[0], "old_income_usd": EXPECTED_RULES[1], "new_gpa": EXPECTED_RULES[2], "new_income_usd": EXPECTED_RULES[3]},
        "applicant_counts": EXPECTED_COUNTS,
        "public_pdf_parses": 2,
        "public_rule_previews": 1,
        "real_clocked_operations": ["Extract", "Extract", "Compare", "Rerank", "Compare PDFs with highlight"],
        "real_clocked_verdict": live["comparison"].get("verdict"),
        "real_clocked_reranked": len(live.get("relevance") or []),
        "pdf_compare_verdict": manifest.get("verdict"),
        "annotated_pdf_counts": annotations,
        "native_highlight_available_for_fresh_pair": marked_available,
        "sdk_credits_text": credits_text,
        "sdk_credits_pdf": credits_pdf,
        "notes": "Authenticated Clocked was run separately from the visitor-facing /try preview on the same PDF contents. No claim of public Clocked billing.",
    }
    (artifact_dir / "verification-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        result = run()
        print("PASS: PUBLIC TWO-PDF UPLOAD AND AUTHENTICATED CLOCKED TEXT QA")
        print("Policy thresholds:", result["policies"])
        print("Applicant transitions:", result["applicant_counts"])
        print("Clocked verdict:", result["real_clocked_verdict"])
        print("Native annotations:", result["annotated_pdf_counts"])
        print("SDK reported credits:", result["sdk_credits_text"], "+", result["sdk_credits_pdf"])
    except Exception as exc:
        # Never include upstream exception messages or secrets in public logs.
        messages = {
            "Deployed PDF parser did not return 200", "Public PDF extraction mismatch for previous",
            "Public PDF extraction mismatch for updated", "Deployed preview did not return 200",
            "Public Try It Yourself preview produced unexpected thresholds",
            "Applicant transition counts do not match the fresh PDFs",
            "Real Clocked extraction did not match policy text",
            "Real Clocked-derived impact differs from public deterministic preview",
            "Clocked Compare or Rerank returned insufficient evidence",
            "Clocked did not return any annotated PDFs",
        }
        message = str(exc)
        print("FAIL:", message if message in messages else type(exc).__name__)
        sys.exit(1)