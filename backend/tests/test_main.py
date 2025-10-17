# backend/tests/test_main.py

from fastapi.testclient import TestClient
from backend.main import app

# Import the fixtures we created
from backend.database_test import session, client

def test_health_check(client: TestClient):
    """
    Tests if the /health endpoint is working correctly.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}