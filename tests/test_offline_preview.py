from fastapi.testclient import TestClient
from app.main import app
from app.offline_preview import parse_explicit_policy
from app.demo import OLD_TEXT, NEW_TEXT


def test_free_preview_parses_two_explicit_rules_and_no_clocked_calls():
    response = TestClient(app).post('/api/preview', json={'old_policy': OLD_TEXT,'new_policy':NEW_TEXT})
    assert response.status_code == 200
    data = response.json()
    assert data['mode'] == 'offline'
    assert data['policies']['old']['min_gpa'] == 3.2
    assert data['policies']['old']['max_income'] == 50000
    assert data['policies']['new']['min_gpa'] == 3.5
    assert data['policies']['new']['max_income'] == 60000
    assert data['impact']['total'] == 16
    assert data['impact']['counts']['lost'] == 4
    assert data['api_calls'] == [] and data['usage']['credits'] == 0


def test_unrecognized_rules_trigger_review():
    old = 'GPA must be 3.2 or higher. Household income may qualify under certain circumstances.'
    p = parse_explicit_policy(old, 'demo')
    assert p.min_gpa is None and p.max_income is None


def test_exceptions_fail_closed():
    p = parse_explicit_policy(OLD_TEXT + 'Unless the student lives outside the state.', 'demo')
    assert p.min_gpa is None and p.max_income is None


def test_multiple_rules_fail_closed():
    p = parse_explicit_policy(OLD_TEXT + 'GPA must be at least 3.0.','demo')
    assert p.min_gpa is None


def test_pdf_extracted_text_can_be_previewed():
    from app.pdf_ingest import parse_policy_pdf
    from pathlib import Path
    text = parse_policy_pdf((Path(__file__).parents[1] / 'web/samples/updated-policy.pdf').read_bytes())['text']
    p = parse_explicit_policy(text,'uploaded')
    assert p.min_gpa == 3.5 and p.max_income == 60000


def test_no_external_clocked_request_even_when_enabled(monkeypatch):
    monkeypatch.setenv('CLOCKED_API_KEY', 'fake-not-a-real-key')
    monkeypatch.setenv('ENABLE_LIVE','true')
    result = TestClient(app).post('/api/preview',json={'old_policy':OLD_TEXT,'new_policy':NEW_TEXT})
    assert result.status_code == 200
    assert result.json()['mode'] == 'offline'


def test_hidden_additional_requirement_never_grants_eligibility():
    policy = OLD_TEXT + "Applicants must submit two faculty recommendations.\n"
    result = parse_explicit_policy(policy, 'demo')
    assert result.min_gpa is None and result.max_income is None


def test_application_deadline_requires_human_review():
    policy = OLD_TEXT + "Applications shall be submitted before March 1.\n"
    result = parse_explicit_policy(policy, 'demo')
    assert result.min_gpa is None and result.max_income is None