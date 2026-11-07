from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_jd_deletion_is_owner_scoped_and_selects_remaining_jd(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'ownership.db'}", "test-secret")
    with TestClient(app) as alice, TestClient(app) as bob:
        for client, email in ((alice, "alice@example.test"), (bob, "bob@example.test")):
            assert client.post('/api/auth/register', json={'email': email, 'password': 'long-test-password'}).status_code == 201
        first = alice.post('/api/jds/paste', json={'title': 'First', 'text': 'Required: Python'}).json()
        second = alice.post('/api/jds/paste', json={'title': 'Second', 'text': 'Required: SQL'}).json()
        assert bob.delete(f"/api/jds/{second['id']}").status_code == 404
        assert alice.delete(f"/api/jds/{second['id']}").status_code == 200
        workspace = alice.get('/api/workspace').json()
        assert [jd['id'] for jd in workspace['jds']] == [first['id']]
        assert workspace['selected_jd_id'] == first['id']
