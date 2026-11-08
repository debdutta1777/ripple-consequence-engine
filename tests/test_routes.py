from fastapi.testclient import TestClient
from app.main import app


def test_demo_route_has_explicit_mode():
    client = TestClient(app)
    result = client.get('/api/demo')
    assert result.status_code == 200
    data = result.json()
    assert data['mode'] == 'fixture'
    assert data['impact']['total'] == 16


def test_live_requires_opt_in(monkeypatch):
    monkeypatch.delenv('CLOCKED_API_KEY', raising=False)
    monkeypatch.delenv('ENABLE_LIVE', raising=False)
    client = TestClient(app)
    response = client.post('/api/analyze', json={
        'old_policy': 'GPA 3.2', 'new_policy': 'GPA 3.6', 'applicants': []
    })
    assert response.status_code == 503
    assert 'disabled' in response.json()['detail']


def test_root_and_assets_served():
    client = TestClient(app)
    assert client.get('/').status_code == 200
    assert client.get('/assets/styles.css').status_code == 200
    assert client.get('/assets/app.js').status_code == 200
