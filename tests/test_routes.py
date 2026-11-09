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
    assert response.status_code == 404
    assert response.json()['detail'] == 'Not found'


def test_root_and_assets_served():
    client = TestClient(app)
    landing = client.get('/')
    assert landing.status_code == 200
    assert 'A single rule can' in landing.text
    assert 'href="/studio"' in landing.text
    assert 'href="/try"' in landing.text
    assert 'Explore Demo' in landing.text
    assert 'Try It Yourself' in landing.text
    assert landing.text.index('href="/studio"') < landing.text.index('href="/try"')
    studio = client.get('/studio')
    assert studio.status_code == 200
    assert 'Decision flips' in studio.text
    assert client.get('/assets/landing.css').status_code == 200
    assert client.get('/assets/landing.js').status_code == 200
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
    assert response.status_code == 404
    monkeypatch.setenv('MAX_LIVE_ANALYSES', 'nonsense')
    assert live_budget() == 0
    monkeypatch.setenv('MAX_LIVE_ANALYSES', '1')
    assert live_budget() == 1 and live_ready()
    monkeypatch.setenv('MAX_LIVE_ANALYSES', '100000')
    assert live_budget() == 25


def test_no_public_live_endpoint_even_with_budget(monkeypatch):
    monkeypatch.setenv('CLOCKED_API_KEY', 'fake-unit-test-value')
    monkeypatch.setenv('ENABLE_LIVE', 'true')
    monkeypatch.setenv('MAX_LIVE_ANALYSES', '10')
    response = TestClient(app).post('/api/analyze', json={'old_policy': 'a', 'new_policy': 'b'})
    assert response.status_code == 404
    assert TestClient(app).get('/api/health').json()['live_enabled'] is False


def test_verification_requires_expiring_token(monkeypatch):
    from time import time
    monkeypatch.setenv('RIPPLE_VERIFY_TOKEN', 'a' * 40)
    monkeypatch.setenv('ENABLE_VERIFICATION', 'true')
    monkeypatch.setenv('RIPPLE_VERIFY_UNTIL', str(int(time()) + 3600))
    client = TestClient(app)
    assert client.post('/api/internal/verify-clocked').status_code == 404
    assert client.post('/api/internal/verify-clocked', headers={'x-ripple-verify': 'bad'}).status_code == 404
    monkeypatch.setenv('RIPPLE_VERIFY_UNTIL', str(int(time()) - 1))
    assert client.post('/api/internal/verify-clocked', headers={'x-ripple-verify': 'a' * 40}).status_code == 404
    monkeypatch.setenv('RIPPLE_VERIFY_UNTIL', 'not-a-number')
    assert client.post('/api/internal/verify-clocked', headers={'x-ripple-verify': 'a' * 40}).status_code == 404


def test_protected_synthetic_clocked_verification(monkeypatch):
    import sys
    import types
    from time import time
    from tests.test_adapter import FakeClocked

    class FakeSDK(FakeClocked):
        def __init__(self, **kwargs):
            super().__init__()
            assert kwargs['max_attempts'] == 1
        def __enter__(self): return self
        def __exit__(self, *args): return False

    monkeypatch.setitem(sys.modules, 'clocked_sdk', types.SimpleNamespace(Clocked=FakeSDK))
    monkeypatch.setenv('RIPPLE_VERIFY_TOKEN', 'b' * 40)
    monkeypatch.setenv('ENABLE_VERIFICATION', 'true')
    monkeypatch.setenv('RIPPLE_VERIFY_UNTIL', str(int(time()) + 3600))
    response = TestClient(app).post('/api/internal/verify-clocked', headers={'x-ripple-verify': 'b' * 40})
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'verified'
    assert result['mode'] == 'live'
    assert result['usage']['request_count'] == 4
    assert result['cohort_counts']['lost'] == 4
    assert 'extraction' not in result
    assert 'RIPPLE_VERIFY_TOKEN' not in str(result)


def test_security_headers_and_hidden_administration_routes():
    client = TestClient(app)
    response = client.get('/api/demo')
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['Referrer-Policy'] == 'no-referrer'
    paths = client.get('/openapi.json').json()['paths']
    assert '/api/analyze' not in paths
    assert '/api/internal/verify-clocked' not in paths
    assert '/api/internal/pdf-proof' not in paths