from fastapi.testclient import TestClient
from backend.app.main import create_app


def test_departments_and_candidate_tags_are_owned_and_persist(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'metadata.db'}", 'secret')
    with TestClient(app) as alice, TestClient(app) as bob:
        for client, email in ((alice, 'alice@example.test'), (bob, 'bob@example.test')):
            assert client.post('/api/auth/register', json={'email': email, 'password': 'long-test-password'}).status_code == 201
        jd = alice.post('/api/jds/paste', json={'title': 'QA', 'text': 'Required: Python'}).json()
        cv = alice.post('/api/candidates/paste', json={'name': 'Example', 'text': 'Python'}).json()
        assert bob.patch(f"/api/jds/{jd['id']}/metadata", json={'department': 'Tech'}).status_code == 404
        assert bob.patch(f"/api/candidates/{cv['id']}/metadata", json={'tags': ['QA']}).status_code == 404
        assert alice.patch(f"/api/jds/{jd['id']}/metadata", json={'department': 'Tech'}).status_code == 200
        assert alice.patch(f"/api/candidates/{cv['id']}/metadata", json={'tags': ['QA', 'Automation']}).status_code == 200
        workspace = alice.get('/api/workspace').json()
        assert workspace['jds'][0]['department'] == 'Tech'
        assert workspace['candidates'][0]['tags'] == ['QA', 'Automation']
        assert bob.get('/api/workspace').json()['jds'] == []


def test_metadata_rejects_empty_duplicate_and_excessive_tags(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'limits.db'}", 'secret')) as client:
        client.post('/api/auth/register', json={'email': 'owner@example.test', 'password': 'long-test-password'})
        cv = client.post('/api/candidates/paste', json={'name': 'Example', 'text': 'Python'}).json()
        for tags in ([''], ['QA', 'qa'], ['x'] * 21, ['x' * 41]):
            assert client.patch(f"/api/candidates/{cv['id']}/metadata", json={'tags': tags}).status_code == 422


def test_manual_skill_change_recalculates_candidate_comparison(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'matching.db'}", 'secret')) as client:
        client.post('/api/auth/register', json={'email': 'owner@example.test', 'password': 'long-test-password'})
        jd = client.post('/api/jds/paste', json={'title': 'QA', 'text': 'Required: Python and SQL'}).json()
        client.post('/api/candidates/paste', json={'name': 'Example', 'text': 'Python experience'} )
        client.patch(f"/api/jds/{jd['id']}", json={'title': 'QA', 'required': ['Python'], 'preferred': []})
        assert client.get('/api/compare').json()['results'][0]['matched_required'] == ['Python']
        client.patch(f"/api/jds/{jd['id']}", json={'title': 'QA', 'required': ['SQL'], 'preferred': []})
        result = client.get('/api/compare').json()['results'][0]
        assert result['matched_required'] == []
        assert result['missing_required'] == ['SQL']
