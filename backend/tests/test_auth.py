# backend/tests/test_auth.py

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.database_test import client, session # Import fixtures

# A sample user for testing
TEST_USER = {"email": "test@example.com", "password": "a-secure-password"}

def test_create_user(client: TestClient):
    """
    Tests the user registration endpoint.
    """
    response = client.post("/users/register", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert "id" in data

def test_login_for_access_token(client: TestClient):
    """
    Tests the user login endpoint and token generation.
    """
    # First, create the user to ensure they exist in the test database
    client.post("/users/register", json=TEST_USER)

    # Now, attempt to log in
    login_data = {"username": TEST_USER["email"], "password": TEST_USER["password"]}
    response = client.post("/token", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_read_users_me_with_token(client: TestClient):
    """
    Tests accessing a protected endpoint with a valid JWT.
    """
    # Create the user
    client.post("/users/register", json=TEST_USER)

    # Log in to get a token
    login_data = {"username": TEST_USER["email"], "password": TEST_USER["password"]}
    response = client.post("/token", data=login_data)
    token = response.json()["access_token"]

    # Access the protected /users/me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]