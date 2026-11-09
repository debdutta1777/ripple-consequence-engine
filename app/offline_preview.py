"""Strict credit-free preview for two explicitly supported scholarship rules.

This is NOT an LLM, not a Clocked response, and not a general policy engine.
Ambiguous, conditional, compound or unsupported policies result in REVIEW.
"""
import re

from app.rules import Policy, impact
from app.clocked_adapter import _number_exact, _supported_direction
from app.demo import APPLICANTS

# Deliberately conservative: additional conditions invalidate an automatic
# eligibility conclusion, rather than being silently ignored.
EXTRA_CONDITIONS = re.compile(
    r"\b(?:unless|except|exception|waiver|either|alternative|citizenship|citizen|"
    r"residency|resident|enrolled|enrollment|age|attendance|credit hours|"
    r"disability|work experience|interview|dependent|domicile|part-time|full-time)\b",
    re.I,
)


def _extract_one(text: str, *, gpa: bool):
    hits = []
    # One policy rule per line/sentence; decimal GPA points are not sentence separators.
    for line in text.splitlines():
        for piece in re.split(r"(?<=[!?])\s+|(?<=\.)\s+(?=[A-Z])", line):
            sentence = piece.strip()
            if not sentence:
                continue
            if gpa and not re.search(r"\bGPA\b", sentence, re.I):
                continue
            if not gpa and not re.search(r"\bincome\b", sentence, re.I):
                continue
            if not _supported_direction(sentence, gpa=gpa):
                continue
            number = _number_exact(sentence, gpa=gpa)
            if number is not None:
                hits.append((number, sentence))
    # Two valid rules might conflict even when their numbers agree. Review both.
    return hits[0] if len(hits) == 1 else (None, "")


def parse_explicit_policy(text: str, label: str) -> Policy:
    # A third eligibility rule invalidates a two-threshold decision, even if
    # the GPA/income fields are otherwise clearly identified.
    conditions = re.compile(
        r"\b(?:must|shall|required|requires|qualify|eligible|"
        r"submit|provide|deadline|application|minimum|maximum|at least|"
        r"no more than|not exceed|cannot exceed|not permitted)\b", re.I
    )
    for line in text.splitlines():
        clause = line.strip()
        if not clause or not conditions.search(clause):
            continue
        if re.search(r"applicant must satisfy both rules to qualify", clause, re.I):
            continue
        if re.search(r"\bGPA\b", clause, re.I) and _supported_direction(clause, gpa=True):
            continue
        if re.search(r"\bincome\b", clause, re.I) and _supported_direction(clause, gpa=False):
            continue
        return Policy(label, None, None, evidence_origin="local_preview_needs_review")
    if EXTRA_CONDITIONS.search(text):
        return Policy(label, None, None, evidence_origin="local_preview_needs_review")
    gpa, gpa_excerpt = _extract_one(text, gpa=True)
    income, income_excerpt = _extract_one(text, gpa=False)
    return Policy(label, gpa, income, gpa_excerpt, income_excerpt,
                  evidence_origin="local_rule_preview_not_clocked")


def preview_policies(before: str, after: str, people=None) -> dict:
    prev = parse_explicit_policy(before, "Previous policy")
    curr = parse_explicit_policy(after, "Updated policy")
    persons = APPLICANTS if people is None or not people else people
    return {
        "mode": "offline",
        "notice": "Credit-free local heuristic preview ONLY. This is not Clocked analysis or an official eligibility decision. Only one unambiguous minimum GPA and one USD annual income ceiling per policy are supported. All other conditions require review.",
        "documents": {"old": before, "new": after},
        "policies": {"old": prev.as_dict(), "new": curr.as_dict()},
        "comparison": {"verdict": "Local rule preview — not Clocked", "conflicts": [], "raw": None},
        "impact": impact(prev, curr, persons),
        "api_calls": [],
        "usage": {"request_count": 0, "credits": 0, "note": "No Clocked request was made."},
    }