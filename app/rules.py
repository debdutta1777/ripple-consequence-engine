"""Small, deliberately limited eligibility evaluator.

Only the two explicit rule types represented in the UI are supported. Unsupported
or unextracted rules produce REVIEW instead of fabricated eligibility.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Policy:
    label: str
    min_gpa: Optional[float]
    max_income: Optional[int]
    gpa_evidence: str = ""
    income_evidence: str = ""
    evidence_origin: str = "fixture"

    def as_dict(self):
        return {
            "label": self.label,
            "min_gpa": self.min_gpa,
            "max_income": self.max_income,
            "gpa_evidence": self.gpa_evidence,
            "income_evidence": self.income_evidence,
            "evidence_origin": self.evidence_origin,
        }


def evaluate(policy: Policy, applicant: dict) -> dict:
    """Tri-state result; values strictly compared (no floating inference)."""
    if policy.min_gpa is None or policy.max_income is None:
        return {
            "status": "review",
            "reason": "A required eligibility threshold could not be verified in the document.",
            "conditions": [],
        }

    gpa = applicant.get("gpa")
    income = applicant.get("income")
    if not isinstance(gpa, (int, float)) or isinstance(gpa, bool) or not isinstance(income, (int, float)) or isinstance(income, bool):
        return {"status": "review", "reason": "Applicant details are incomplete.", "conditions": []}

    conditions = [
        {"key": "gpa", "met": gpa >= policy.min_gpa, "actual": gpa, "required": policy.min_gpa},
        {"key": "income", "met": income <= policy.max_income, "actual": income, "required": policy.max_income},
    ]
    bad = [c for c in conditions if not c["met"]]
    if not bad:
        return {"status": "eligible", "reason": "Meets both documented requirements.", "conditions": conditions}
    reasons = []
    if any(c["key"] == "gpa" for c in bad):
        reasons.append("GPA below the minimum")
    if any(c["key"] == "income" for c in bad):
        reasons.append("income above the maximum")
    return {"status": "ineligible", "reason": "; ".join(reasons) + ".", "conditions": conditions}


def classify(before: dict, after: dict) -> str:
    if "review" in (before["status"], after["status"]):
        return "review"
    if before["status"] == "eligible" and after["status"] == "ineligible":
        return "lost"
    if before["status"] == "ineligible" and after["status"] == "eligible":
        return "gained"
    if before["status"] == "eligible":
        return "retained"
    return "excluded"


def flip_path(policy: Policy, applicant: dict) -> dict:
    """Compute *componentwise* minimum changes needed to satisfy known rules.

    This is a threshold calculation, not a prediction that the applicant can
    achieve the changes or that a real scholarship would approve the case.
    Unknown or incomplete requirements produce review rather than advice.
    """
    assessment = evaluate(policy, applicant)
    if assessment["status"] == "review":
        return {"status": "review", "changes": [], "verified_after_change": False,
                "summary": "Policy or applicant information requires human review."}
    if assessment["status"] == "eligible":
        return {"status": "already_eligible", "changes": [], "verified_after_change": True,
                "summary": "This applicant already meets both modeled requirements."}

    changes = []
    revised = dict(applicant)
    if applicant["gpa"] < policy.min_gpa:
        revised["gpa"] = policy.min_gpa
        changes.append({"field": "gpa", "current": applicant["gpa"],
                        "target": policy.min_gpa,
                        "delta": round(policy.min_gpa - applicant["gpa"], 2),
                        "evidence": policy.gpa_evidence})
    if applicant["income"] > policy.max_income:
        revised["income"] = policy.max_income
        changes.append({"field": "income", "current": applicant["income"],
                        "target": policy.max_income,
                        "delta": policy.max_income - applicant["income"],
                        "evidence": policy.income_evidence})

    verified = evaluate(policy, revised)["status"] == "eligible"
    return {"status": "changes_required", "changes": changes,
            "verified_after_change": verified,
            "summary": ("Meet every listed threshold to satisfy the two modeled "
                        "requirements. This is not an award prediction.")}


def impact(old: Policy, new: Policy, applicants: list[dict]) -> dict:
    cases = []
    counts = {"lost": 0, "gained": 0, "retained": 0, "excluded": 0, "review": 0}
    for app in applicants:
        before = evaluate(old, app)
        after = evaluate(new, app)
        transition = classify(before, after)
        counts[transition] += 1
        cases.append({**app, "old": before, "new": after,
                      "transition": transition, "flip_path": flip_path(new, app)})
    return {"counts": counts, "cases": cases, "total": len(cases)}
