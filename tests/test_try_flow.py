from fastapi.testclient import TestClient
from app.main import app
from app.demo import OLD_TEXT, NEW_TEXT
from app.policy_diff import compare_policy_text


def test_self_service_page_and_assets():
    client = TestClient(app)
    response = client.get('/try')
    assert response.status_code == 200
    assert 'Upload previous policy' in response.text
    assert 'Upload updated policy' in response.text
    assert client.get('/assets/try.css').status_code == 200
    assert client.get('/assets/try.js').status_code == 200


def test_uploaded_policy_preview_is_dynamic_not_fixture():
    before = 'FICTIONAL POLICY 2025\nEligibility requires a minimum cumulative GPA of 3.0.\nAnnual household income must not exceed $45,000.\nAn applicant must satisfy both rules to qualify.'
    after = 'FICTIONAL POLICY 2026\nEligibility requires a minimum cumulative GPA of 3.7.\nAnnual household income must not exceed $70,000.\nAn applicant must satisfy both rules to qualify.'
    result = TestClient(app).post('/api/preview', json={'old_policy': before,'new_policy': after,'applicants':[
        {'id':'A1','name':'Case A','gpa':3.5,'income':40000},
        {'id':'A2','name':'Case B','gpa':3.8,'income':55000}]})
    assert result.status_code == 200
    data = result.json()
    assert data['impact']['total'] == 2
    assert data['impact']['counts']['lost'] == 1
    assert data['impact']['counts']['gained'] == 1
    assert data['mode'] == 'offline'
    assert data['document_diff']['total_changes'] >= 2
    assert data['policies']['new']['min_gpa'] == 3.7
    assert data['usage']['credits'] == 0


def test_unknown_policy_causes_review_but_reports_literal_changes():
    data = TestClient(app).post('/api/preview',json={
        'old_policy': OLD_TEXT,
        'new_policy': NEW_TEXT + '\nApplicant must be a resident of New York.',
        'applicants': [{'id':'X','name':'Test','gpa':3.6,'income':20000}]
    }).json()
    assert data['impact']['counts']['review'] == 1
    assert data['document_diff']['total_changes'] > 0
    assert any('resident' in ch['updated'] for ch in data['document_diff']['changes'])


def test_compare_multiple_changed_lines_capped():
    data = compare_policy_text('\n'.join(f'Rule A{i}' for i in range(65)), '\n'.join(f'Rule B{i}' for i in range(65)))
    assert data['total_changes'] == 65
    assert len(data['changes']) == 24
    assert data['truncated'] is True


def test_cohort_size_is_bounded():
    person={'id':'x','name':'Case','gpa':3.4,'income':45000}
    result=TestClient(app).post('/api/preview',json={'old_policy':OLD_TEXT,'new_policy':NEW_TEXT,'applicants':[person]*101})
    assert result.status_code == 422