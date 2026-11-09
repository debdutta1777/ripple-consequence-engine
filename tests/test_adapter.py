from app.clocked_adapter import _extract_supported_rule, _number_exact, analyze_live


def test_extract_verbatim():
    text = "Eligibility requires a minimum cumulative GPA of 3.2."
    fields = {"minimum_gpa": {"value": "3.2", "start": text.index("3.2")}}
    number, source = _extract_supported_rule(fields, "minimum_gpa", text, gpa=True)
    assert number == 3.2 and source == "3.2"


def test_hallucinated_value_not_accepted():
    text = "Eligibility requires a minimum GPA of 3.2."
    fields = {"minimum_gpa": {"value": "3.6", "start": 0}}
    number, source = _extract_supported_rule(fields, "minimum_gpa", text, gpa=True)
    assert number is None


def test_multiple_numbers_not_accepted():
    assert _number_exact("GPA from 3.2 to 3.6", gpa=True) is None


def test_inverted_gpa_clause_does_not_become_minimum():
    source = "Eligibility requires a maximum GPA of 3.2."
    val, evidence = _extract_supported_rule({"minimum_gpa": "3.2"}, "minimum_gpa", source, gpa=True)
    assert val is None and evidence == ""


def test_inverted_income_clause_does_not_become_ceiling():
    source = "Annual household income must be at least $50,000."
    val, evidence = _extract_supported_rule({"maximum_household_income": "$50,000"}, "maximum_household_income", source, gpa=False)
    assert val is None and evidence == ""


def test_ambiguous_currency_requires_review():
    source = "Annual household income must not exceed 50,000."
    val, evidence = _extract_supported_rule({"maximum_household_income": "50,000"}, "maximum_household_income", source, gpa=False)
    assert val is None and evidence == ""


def test_duplicate_unpositioned_rule_requires_review():
    source = "Minimum GPA is 3.2. Minimum GPA is 3.2."
    val, evidence = _extract_supported_rule({"minimum_gpa": "3.2"}, "minimum_gpa", source, gpa=True)
    assert val is None and evidence == ""

class FakeClocked:
    def __init__(self): self.calls=[]
    def extract(self, text, **kw):
        self.calls.append("extract")
        import re
        gpa = re.search(r"\b3\.[25]\b", text).group()
        amt = re.search(r"\$[\d,]+", text).group()
        return {"fields": {"minimum_gpa": {"value": gpa}, "maximum_household_income": {"value": amt}}}
    def compare(self, documents):
        self.calls.append("compare")
        return {"verdict": "conflict", "conflicts": [{"document_ids": ["previous", "current"]}]}
    def rerank(self, query, documents, top_n):
        self.calls.append("rerank")
        return {"results": [{"id": "prev-gpa", "action": "use", "relevance_score": .9}]}


def test_live_path_calls_clocked_endpoints():
    client = FakeClocked()
    from app.demo import OLD_TEXT, NEW_TEXT, APPLICANTS
    response = analyze_live(client, OLD_TEXT, NEW_TEXT, APPLICANTS)
    assert response["mode"] == "live"
    assert client.calls == ["extract", "extract", "compare", "rerank"]
    assert response["impact"]["counts"]["lost"] > 0
    assert response["impact"]["counts"]["gained"] > 0


def test_unsupported_extra_conditions_force_review():
    client = FakeClocked()
    from app.demo import OLD_TEXT, NEW_TEXT
    old = OLD_TEXT + 'Applicant must also be a resident of the state.\n'
    result = analyze_live(client, old, NEW_TEXT, [{"id": "A01", "name": "Applicant 01", "gpa": 3.8, "income": 30000}])
    assert result["impact"]["cases"][0]["transition"] == "review"


def test_clocked_sdk_usage_totals_are_reported_if_available():
    from app.demo import OLD_TEXT, NEW_TEXT, APPLICANTS

    class Recorded(dict):
        def __init__(self, raw, credits, cost_usd):
            super().__init__(raw)
            self.credits = credits
            self.cost_usd = cost_usd
            self.model_ms = credits * 25

    class MeteredClocked(FakeClocked):
        def extract(self, text, **kwargs):
            return Recorded(super().extract(text, **kwargs), 2, 0.0001)
        def compare(self, **kwargs):
            return Recorded(super().compare(**kwargs), 5, 0.0003)
        def rerank(self, **kwargs):
            return Recorded(super().rerank(**kwargs), 3, 0.0002)

    result = analyze_live(MeteredClocked(), OLD_TEXT, NEW_TEXT, APPLICANTS)
    usage = result['usage']
    assert usage['request_count'] == 4
    assert usage['credits'] == 12
    assert usage['cost_usd'] == 0.0007
    assert len(usage['records']) == 4
    assert usage['records'][0]['endpoint'] == 'extract_previous'


def test_usage_unknown_when_sdk_exposes_no_billing_metadata():
    from app.demo import OLD_TEXT, NEW_TEXT, APPLICANTS
    result = analyze_live(FakeClocked(), OLD_TEXT, NEW_TEXT, APPLICANTS)
    assert result['usage']['credits'] is None
    assert result['usage']['cost_usd'] is None
    assert result['usage']['request_count'] == 4