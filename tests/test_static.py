from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_built_frontend_and_health(tmp_path):
    dist = Path(__file__).resolve().parents[1] / "frontend" / "dist" / "index.html"
    if not dist.exists():
        pytest.skip("Build frontend first with npm run build")
    with TestClient(create_app(f"sqlite:///{tmp_path / 'static.db'}", "test-key")) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert "RoleTrace" in client.get("/").text
        assert "RoleTrace" in client.get("/compare").text
        assert client.get("/api/missing").status_code == 404
