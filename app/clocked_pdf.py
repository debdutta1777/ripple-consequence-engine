"""Optional protected PDF evidence pack through the official Clocked Compare API.

Never invoked by the public demo. The only permitted inputs are the bundled
synthetic policies. If an SDK result lacks a marked PDF, report that honestly.
"""
import json
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.clocked_adapter import _root_json, _usage_record
from app.pdf_ingest import parse_policy_pdf


def create_marked_comparison(client, previous_pdf: bytes, updated_pdf: bytes) -> tuple[bytes, dict]:
    # Text-based only, under the exact same limits as the preview endpoint.
    before = parse_policy_pdf(previous_pdf)
    after = parse_policy_pdf(updated_pdf)
    result = client.compare(
        documents=[
            {"id": "previous", "pdf": previous_pdf},
            {"id": "current", "pdf": updated_pdf},
        ],
        return_text=True,
        return_pdf="highlight",
    )
    data = _root_json(result)
    usage = _usage_record("compare_pdf", result)
    manifest = {
        "mode": "clocked_live_pdf_compare",
        "source": "two bundled fictional scholarship-policy PDF documents",
        "verdict": data.get("verdict"),
        "conflict_count": len(data.get("conflicts") or []) if isinstance(data.get("conflicts"), list) else None,
        "usage": usage,
        "documents": {
            "previous": {"pages": before["page_count"], "highlighted": False},
            "current": {"pages": after["page_count"], "highlighted": False},
        },
        "notice": "Marked PDFs are actual Clocked outputs only when the SDK supplies them. A missing marked PDF is not recreated or fabricated.",
    }
    marked = {}
    for name in ("previous", "current"):
        try:
            payload = result.marked_pdf(document=name)
        except (AttributeError, KeyError, ValueError, TypeError):
            continue
        if isinstance(payload, bytes) and payload.startswith(b"%PDF-") and len(payload) <= 4 * 1024 * 1024:
            marked[name] = payload
            manifest["documents"][name]["highlighted"] = True
    bundle = BytesIO()
    with ZipFile(bundle, "w", ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        for name, raw in marked.items():
            archive.writestr(f"{name}-clocked-highlighted.pdf", raw)
    return bundle.getvalue(), manifest