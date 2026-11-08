"""Fully synthetic sample data. Not real scholarship rules or real persons."""
from app.rules import Policy, impact

OLD_TEXT = """FICTIONAL BRIGHT FUTURES SCHOLARSHIP — 2025 (DEMO ONLY)
Eligibility requires a minimum cumulative GPA of 3.2.
Annual household income must not exceed $50,000.
An applicant must satisfy both rules to qualify.
"""
NEW_TEXT = """FICTIONAL BRIGHT FUTURES SCHOLARSHIP — 2026 (DEMO ONLY)
Eligibility requires a minimum cumulative GPA of 3.5.
Annual household income must not exceed $60,000.
An applicant must satisfy both rules to qualify.
"""
OLD = Policy("2025 policy", 3.2, 50000, "Eligibility requires a minimum cumulative GPA of 3.2.", "Annual household income must not exceed $50,000.")
NEW = Policy("2026 policy", 3.5, 60000, "Eligibility requires a minimum cumulative GPA of 3.5.", "Annual household income must not exceed $60,000.")

APPLICANTS = [
    {"id": "A01", "name": "Applicant 01", "gpa": 3.30, "income": 36000},
    {"id": "A02", "name": "Applicant 02", "gpa": 3.40, "income": 45000},
    {"id": "A03", "name": "Applicant 03", "gpa": 3.15, "income": 42000},
    {"id": "A04", "name": "Applicant 04", "gpa": 3.85, "income": 57000},
    {"id": "A05", "name": "Applicant 05", "gpa": 3.70, "income": 53000},
    {"id": "A06", "name": "Applicant 06", "gpa": 3.60, "income": 32000},
    {"id": "A07", "name": "Applicant 07", "gpa": 3.25, "income": 58000},
    {"id": "A08", "name": "Applicant 08", "gpa": 3.90, "income": 72000},
    {"id": "A09", "name": "Applicant 09", "gpa": 3.50, "income": 60000},
    {"id": "A10", "name": "Applicant 10", "gpa": 3.48, "income": 49000},
    {"id": "A11", "name": "Applicant 11", "gpa": 3.78, "income": 47000},
    {"id": "A12", "name": "Applicant 12", "gpa": 2.90, "income": 25000},
    {"id": "A13", "name": "Applicant 13", "gpa": 3.53, "income": 55000},
    {"id": "A14", "name": "Applicant 14", "gpa": 3.22, "income": 41000},
    {"id": "A15", "name": "Applicant 15", "gpa": 3.95, "income": 45000},
    {"id": "A16", "name": "Applicant 16", "gpa": 3.30, "income": 65000},
]


def make_demo():
    return {
        "mode": "fixture",
        "notice": "Illustrative, entirely synthetic rules and applicants. These results do not represent a live Clocked API request or an actual scholarship.",
        "documents": {"old": OLD_TEXT, "new": NEW_TEXT},
        "policies": {"old": OLD.as_dict(), "new": NEW.as_dict()},
        "comparison": {"verdict": "synthetic demonstration", "conflicts": [], "raw": None},
        "impact": impact(OLD, NEW, APPLICANTS),
        "api_calls": [],
    }
