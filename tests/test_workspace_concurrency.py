from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient
from backend.app import main


def test_concurrent_same_account_writes_never_silently_discard_one(tmp_path, monkeypatch):
    app = main.create_app(f"sqlite:///{tmp_path / 'concurrent.db'}", "secret")
    with TestClient(app) as client:
        client.post('/api/auth/register', json={'email': 'same@example.test', 'password': 'long-test-password'})
        client.get('/api/workspace')
        barrier = Barrier(2)
        original = main.workspace_from_dict

        def synchronized(data):
            result = original(data)
            barrier.wait(timeout=5)
            return result

        with monkeypatch.context() as patch:
            patch.setattr(main, 'workspace_from_dict', synchronized)
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda name: client.post('/api/candidates/paste', json={'name': name, 'text': 'Python'}), ['First', 'Second']))
        assert sorted(r.status_code for r in results) == [201, 409]
        conflict = next(r for r in results if r.status_code == 409)
        assert 'changed' in conflict.json()['detail'].lower()
        assert len(client.get('/api/workspace').json()['candidates']) == 1


def test_delete_and_upload_conflict_preserves_successful_operation(tmp_path, monkeypatch):
    app = main.create_app(f"sqlite:///{tmp_path / 'delete-upload.db'}", "secret")
    with TestClient(app) as client:
        client.post('/api/auth/register', json={'email': 'owner@example.test', 'password': 'long-test-password'})
        jd = client.post('/api/jds/paste', json={'title': 'QA', 'text': 'Required: Python'}).json()
        barrier = Barrier(2)
        original = main.workspace_from_dict

        def synchronized(data):
            result = original(data)
            barrier.wait(timeout=5)
            return result

        with monkeypatch.context() as patch:
            patch.setattr(main, 'workspace_from_dict', synchronized)
            with ThreadPoolExecutor(max_workers=2) as pool:
                delete = pool.submit(client.delete, f"/api/jds/{jd['id']}")
                upload = pool.submit(client.post, '/api/candidates/paste', json={'name': 'Test Candidate', 'text': 'Python'})
                deleted, added = delete.result(), upload.result()
        assert sorted([deleted.status_code, added.status_code]) in ([200, 409], [201, 409])
        workspace = client.get('/api/workspace').json()
        assert (not workspace['jds']) == (deleted.status_code == 200)
        assert bool(workspace['candidates']) == (added.status_code == 201)


def test_old_browser_version_cannot_overwrite_newer_edit(tmp_path):
    app = main.create_app(f"sqlite:///{tmp_path / 'stale.db'}", "secret")
    with TestClient(app) as client, TestClient(app) as second_tab:
        client.post('/api/auth/register', json={'email': 'owner@example.test', 'password': 'long-test-password'})
        assert second_tab.post('/api/auth/login', json={'email': 'owner@example.test', 'password': 'long-test-password'}).status_code == 200
        jd = client.post('/api/jds/paste', json={'title': 'QA', 'text': 'Required: Python'}).json()
        old_version = second_tab.get('/api/workspace').json()['revision']
        payload = {'title': 'QA', 'required': ['Python'], 'preferred': []}
        assert client.patch(f"/api/jds/{jd['id']}", headers={'X-Workspace-Revision': str(old_version)}, json=payload).status_code == 200
        payload['required'] = ['SQL']
        stale = second_tab.patch(f"/api/jds/{jd['id']}", headers={'X-Workspace-Revision': str(old_version)}, json=payload)
        assert stale.status_code == 409
        assert client.get('/api/workspace').json()['jds'][0]['required'] == ['Python']
