"""Create two obviously fictional, selectable-text QA policies for the Ripple demo.

Requires reportlab (development-only); generated files are public fictional fixtures.
The two policies deliberately cause both gains and losses in Ripple's sample cohort.
"""
from pathlib import Path
from io import BytesIO

POLICIES = {
    2025: {"gpa": "3.25", "income": "$52,000", "revision": "BFS-2025-R2", "caption": "Previous policy"},
    2026: {"gpa": "3.65", "income": "$66,000", "revision": "BFS-2026-R1", "caption": "Updated policy"},
}


def build_policy(year: int) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    p = POLICIES[year]
    out = BytesIO()
    c = canvas.Canvas(out, pagesize=(612, 792), pageCompression=1, invariant=1)
    c.setTitle(f"Bright Futures Scholarship Policy {year} (Fictional QA)")
    c.setAuthor("Ripple Consequence Engine - Fictional QA")
    c.setFillColor(HexColor("#f8f9fd"))
    c.rect(0, 0, 612, 792, fill=1, stroke=0)
    c.setFillColor(HexColor("#20243f"))
    c.rect(0, 637, 612, 155, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(HexColor("#babcfb"))
    c.drawString(48, 747, "BRIGHT FUTURES  /  FICTIONAL SCHOLARSHIP")
    c.setFont("Helvetica-Bold", 28)
    c.setFillColorRGB(1,1,1)
    c.drawString(48, 695, f"Scholarship Policy {year}")
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#d5ddfa"))
    c.drawString(48, 665, f"{p['caption']}  |  Reference {p['revision']}")
    c.setFillColor(HexColor("#ffffff"))
    c.roundRect(43, 350, 526, 239, 16, fill=1, stroke=0)
    c.setFillColor(HexColor("#5b56d8"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(67, 548, "RULE 01  /  ACADEMIC REQUIREMENT")
    c.setFillColor(HexColor("#242841"))
    c.setFont("Helvetica", 13)
    c.drawString(67, 520, f"Eligibility requires a minimum cumulative GPA of {p['gpa']}.")
    c.setStrokeColor(HexColor("#e6e8f2"))
    c.line(67, 488, 546, 488)
    c.setFillColor(HexColor("#5b56d8"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(67, 463, "RULE 02  /  FINANCIAL REQUIREMENT")
    c.setFillColor(HexColor("#242841"))
    c.setFont("Helvetica", 13)
    c.drawString(67, 436, f"Annual household income must not exceed {p['income']}.")
    c.setStrokeColor(HexColor("#e6e8f2"))
    c.line(67, 407, 546, 407)
    c.setFillColor(HexColor("#3e4665"))
    c.setFont("Helvetica", 11)
    c.drawString(67, 383, "An applicant must satisfy both rules to qualify.")
    c.setFillColor(HexColor("#f1f0ff"))
    c.roundRect(43, 247, 526, 73, 12, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#4a48b3"))
    c.drawString(62, 292, "TEST-DOCUMENT NOTICE")
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#4b526b"))
    c.drawString(62, 272, "This is an invented policy for testing Ripple with sample applicants.")
    c.drawString(62, 256, "It is not issued by a government, university, or scholarship provider.")
    c.setStrokeColor(HexColor("#dfe2ee"))
    c.line(43, 105, 569, 105)
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#69718c"))
    c.drawString(43, 85, "RIPPLE / POLICY IMPACT TEST FIXTURE")
    c.drawRightString(569, 85, f"{year}  |  1 / 1")
    c.showPage()
    c.save()
    return out.getvalue()


def write_policies(target: Path) -> list[Path]:
    target.mkdir(parents=True, exist_ok=True)
    outputs = []
    for year in POLICIES:
        path = target / f"judge-policy-{year}.pdf"
        path.write_bytes(build_policy(year))
        outputs.append(path)
    return outputs


if __name__ == "__main__":
    paths = write_policies(Path(__file__).resolve().parent.parent / "web" / "samples")
    for p in paths:
        print(f"{p.name}: {p.stat().st_size} bytes")