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
    assert 'locked' in response.json()['detail']


def test_root_and_assets_served():
    client = TestClient(app)
    assert client.get('/').status_code == 200
    assert client.get('/assets/styles.css').status_code == 200
    assert client.get('/assets/app.js').status_code == 200


def test_live_budget_is_fail_closed(monkeypatch):
    from app.main import live_budget, live_ready
    monkeypatch.setenv('CLOCKED_API_KEY', 'test-placeholder-not-a-real-key')
    monkeypatch.setenv('ENABLE_LIVE', 'true')
    monkeypatch.delenv('MAX_LIVE_ANALYSES', raising=False)
    assert live_budget() == 0
    assert not live_ready()
    client = TestClient(app)
    assert client.get('/api/health').json()['live_enabled'] is False
    response = client.post('/api/analyze', json={'old_policy': 'a', 'new_policy': 'b'})
    assert response.status_code == 503
    monkeypatch.setenv('MAX_LIVE_ANALYSES', 'nonsense')
    assert live_budget() == 0
    monkeypatch.setenv('MAX_LIVE_ANALYSES', '1')
    assert live_budget() == 1 and live_ready()
    monkeypatch.setenv('MAX_LIVE_ANALYSES', '100000')
    assert live_budget() == 25