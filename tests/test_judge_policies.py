"""Cross-check the fresh fictional PDFs against the public /try model.

No Clocked credits or network access required; the authenticated companion
is scripts.verify_try_live (manual-only GitHub Actions).
"""
from pathlib import Path
from fastapi.testclient import TestClient

from app.demo import APPLICANTS
from app.main import app
from app.pdf_ingest import parse_policy_pdf
from app.offline_preview import preview_policies

ROOT = Path(__file__).resolve().parents[1]


def test_fresh_policy_fixtures_have_real_extractable_content():
    previous = parse_policy_pdf((ROOT / 'web/samples/judge-policy-2025.pdf').read_bytes())
    current = parse_policy_pdf((ROOT / 'web/samples/judge-policy-2026.pdf').read_bytes())
    assert previous['page_count'] == current['page_count'] == 1
    assert 'minimum cumulative GPA of 3.25' in previous['text']
    assert 'not exceed $52,000' in previous['text']
    assert 'minimum cumulative GPA of 3.65' in current['text']
    assert 'not exceed $66,000' in current['text']
    assert 'FICTIONAL' in previous['text'] and 'FICTIONAL' in current['text']
    result = preview_policies(previous['text'], current['text'], APPLICANTS)
    assert result['mode'] == 'offline'
    assert result['api_calls'] == []
    assert result['impact']['total'] == 16
    assert result['impact']['counts'] == {'lost': 4, 'gained': 2, 'retained': 2, 'excluded': 8, 'review': 0}
    assert result['policies']['old']['min_gpa'] == 3.25
    assert result['policies']['new']['max_income'] == 66000


def test_fresh_policy_uploads_use_actual_fastapi_handlers():
    client = TestClient(app)
    documents = []
    for name in ('judge-policy-2025.pdf', 'judge-policy-2026.pdf'):
        data = (ROOT / 'web/samples' / name).read_bytes()
        res = client.post('/api/parse-pdf', files={'file': (name, data, 'application/pdf')})
        assert res.status_code == 200
        assert res.json()['clocked_calls'] == 0
        documents.append(res.json()['text'])
    result = client.post('/api/preview', json={'old_policy': documents[0], 'new_policy': documents[1], 'applicants': APPLICANTS})
    assert result.status_code == 200
    assert result.json()['impact']['counts']['lost'] == 4
    assert result.json()['impact']['counts']['gained'] == 2


def test_try_it_yourself_has_genuine_file_links_and_progress():
    client = TestClient(app)
    html = client.get('/try').text
    assert 'judge-policy-2025.pdf' in html
    assert 'judge-policy-2026.pdf' in html
    assert 'role="progressbar"' in html
    assert 'id="insight-headline"' in html
    for name in ('judge-policy-2025.pdf', 'judge-policy-2026.pdf'):
        res = client.get('/assets/samples/' + name)
        assert res.status_code == 200
        assert res.content.startswith(b'%PDF-')