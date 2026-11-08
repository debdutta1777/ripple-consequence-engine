from app.rules import Policy, impact, evaluate, flip_path
from app.demo import OLD, NEW, APPLICANTS


def test_loss_and_gain():
    result = impact(OLD, NEW, APPLICANTS)
    by_id = {c["id"]: c for c in result["cases"]}
    assert by_id["A01"]["transition"] == "lost"
    assert by_id["A04"]["transition"] == "gained"
    assert sum(result["counts"].values()) == len(APPLICANTS)


def test_rule_boundary_inclusive():
    result = evaluate(NEW, {"gpa": 3.5, "income": 60000})
    assert result["status"] == "eligible"


def test_missing_rule_fails_closed():
    p = Policy("ambiguous", None, 60000)
    assert evaluate(p, {"gpa": 4.0, "income": 0})["status"] == "review"


def test_no_invented_applicant_facts():
    assert evaluate(OLD, {"gpa": None, "income": 40000})["status"] == "review"


def test_flip_path_single_gpa_threshold():
    path = flip_path(NEW, {"gpa": 3.3, "income": 36000})
    assert path["status"] == "changes_required"
    assert path["verified_after_change"] is True
    assert path["changes"] == [{
        "field": "gpa", "current": 3.3, "target": 3.5,
        "delta": 0.2, "evidence": NEW.gpa_evidence,
    }]


def test_flip_path_requires_both_failing_conditions():
    path = flip_path(NEW, {"gpa": 3.0, "income": 67000})
    assert [item["field"] for item in path["changes"]] == ["gpa", "income"]
    assert [item["delta"] for item in path["changes"]] == [0.5, -7000]
    assert path["verified_after_change"] is True


def test_flip_path_inclusive_boundaries_and_unknowns():
    at_boundary = flip_path(NEW, {"gpa": 3.5, "income": 60000})
    assert at_boundary["status"] == "already_eligible"
    unknown = flip_path(Policy("Unknown", None, 60000), {"gpa": 4.0, "income": 30000})
    assert unknown["status"] == "review" and not unknown["changes"]


def test_impact_contains_explainable_flip_paths():
    cases = impact(OLD, NEW, APPLICANTS)["cases"]
    lost = next(item for item in cases if item["id"] == "A01")
    gained = next(item for item in cases if item["id"] == "A04")
    assert lost["flip_path"]["changes"][0]["field"] == "gpa"
    assert gained["flip_path"]["status"] == "already_eligible"
