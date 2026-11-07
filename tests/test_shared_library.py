from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.auth import WorkspaceRecord
from backend.app.sample_data import sample_workspace
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from backend.app import main


def test_share_copy_revoke_and_delete_are_isolated(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'library.db'}", 'secret')
    with TestClient(app) as alice, TestClient(app) as bob, TestClient(app) as guest:
        for client, email in ((alice, 'alice@example.test'), (bob, 'bob@example.test')):
            assert client.post('/api/auth/register', json={'email': email, 'password': 'long-test-password'}).status_code == 201
        jd = alice.post('/api/jds/paste', json={'title': 'QA', 'text': 'Required: Python'}).json()
        assert guest.get('/api/library').status_code == 401
        assert bob.get('/api/library').json()['items'] == []
        assert bob.post(f"/api/library/share/jd/{jd['id']}").status_code == 404
        published = alice.post(f"/api/library/share/jd/{jd['id']}")
        assert published.status_code == 201
        shared_id = published.json()['id']
        assert len(bob.get('/api/library').json()['items']) == 1
        assert b'Required: Python' in bob.get(f'/api/library/{shared_id}/download').content
        assert bob.delete(f'/api/library/{shared_id}').status_code == 404
        copy = bob.post(f'/api/library/{shared_id}/copy').json()
        assert copy['id'] != jd['id']
        assert alice.delete(f'/api/library/{shared_id}').status_code == 200
        assert bob.get(f'/api/library/{shared_id}/download').status_code == 404
        assert len(bob.get('/api/workspace').json()['jds']) == 1
        assert alice.post(f"/api/library/share/jd/{jd['id']}").status_code == 201
        assert alice.delete(f"/api/jds/{jd['id']}").status_code == 200
        assert bob.get('/api/library').json()['items'] == []


def test_shared_upload_download_preserves_original_file(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'files.db'}", 'secret')
    with TestClient(app) as owner, TestClient(app) as reader:
        for client, email in ((owner, 'owner@example.test'), (reader, 'reader@example.test')):
            client.post('/api/auth/register', json={'email': email, 'password': 'long-test-password'})
        raw = b'Python and SQL synthetic CV'
        cv = owner.post('/api/candidates/upload', files={'file': ('sample.txt', raw, 'text/plain')}).json()
        shared = owner.post(f"/api/library/share/candidate/{cv['id']}").json()
        response = reader.get(f"/api/library/{shared['id']}/download")
        assert response.status_code == 200
        assert response.content == raw
        assert 'sample.txt' in response.headers['content-disposition']


def test_shared_pasted_document_preserves_original_whitespace(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'pasted.db'}", 'secret')
    with TestClient(app) as owner, TestClient(app) as reader:
        for client, email in ((owner, 'owner@example.test'), (reader, 'reader@example.test')):
            client.post('/api/auth/register', json={'email': email, 'password': 'long-test-password'})
        original = '  Python\n\n  SQL\n'
        jd = owner.post('/api/jds/paste', json={'title': 'QA', 'text': original}).json()
        shared = owner.post(f"/api/library/share/jd/{jd['id']}").json()
        assert reader.get(f"/api/library/{shared['id']}/download").content == original.encode()


def test_removing_legacy_sample_revokes_its_shared_copy(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'legacy.db'}", 'secret')
    with TestClient(app) as owner, TestClient(app) as reader:
        uid = owner.post('/api/auth/register', json={'email': 'owner@example.test', 'password': 'long-test-password'}).json()['id']
        reader.post('/api/auth/register', json={'email': 'reader@example.test', 'password': 'long-test-password'})
        owner.get('/api/workspace')
        with app.state.auth.session_factory() as session:
            session.get(WorkspaceRecord, uid).payload = asdict(sample_workspace())
            session.commit()
        shared = owner.post('/api/library/share/jd/data-engineer').json()['id']
        assert owner.delete('/api/workspace/sample-data').status_code == 200
        assert reader.get(f'/api/library/{shared}').status_code == 404


def test_copy_rechecks_revocation_before_committing(tmp_path, monkeypatch):
    app = create_app(f"sqlite:///{tmp_path / 'race.db'}", 'secret')
    with TestClient(app) as owner, TestClient(app) as reader:
        for client, email in ((owner, 'owner@example.test'), (reader, 'reader@example.test')):
            client.post('/api/auth/register', json={'email': email, 'password': 'long-test-password'})
        jd = owner.post('/api/jds/paste', json={'title': 'QA', 'text': 'Python'}).json()
        shared = owner.post(f"/api/library/share/jd/{jd['id']}").json()['id']
        reader.get('/api/workspace')
        paused, resume = Event(), Event()
        original = main.workspace_from_dict
        def gated(data):
            result = original(data)
            if data.get('jds') and data.get('selected_jd_id') == '' and data['jds'][0]['id'] != jd['id']:
                paused.set()
                assert resume.wait(timeout=5)
            return result
        with monkeypatch.context() as patch:
            patch.setattr(main, 'workspace_from_dict', gated)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(reader.post, f'/api/library/{shared}/copy')
                assert paused.wait(timeout=5)
                assert owner.delete(f'/api/library/{shared}').status_code == 200
                resume.set()
                assert future.result().status_code == 404
        assert reader.get('/api/workspace').json()['jds'] == []
