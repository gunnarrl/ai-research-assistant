# backend/tests/test_projects.py

import io
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from backend.database_test import client, session # Import fixtures

# Define two separate users for collaboration tests
TEST_USER_OWNER = {"email": "owner@example.com", "password": "password123"}
TEST_USER_MEMBER = {"email": "member@example.com", "password": "password456"}

def get_auth_headers(client: TestClient, user: dict) -> dict:
    """Helper function to register and log in a user to get auth headers."""
    client.post("/users/register", json=user)
    login_data = {"username": user["email"], "password": user["password"]}
    response = client.post("/token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_project(client: TestClient):
    """Test that a user can create a new project."""
    headers = get_auth_headers(client, TEST_USER_OWNER)
    response = client.post("/projects", headers=headers, json={"name": "My First Project"})
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My First Project"
    assert len(data["members"]) == 1
    assert data["members"][0]["email"] == TEST_USER_OWNER["email"]

def test_add_member_to_project(client: TestClient):
    """Test that a project owner can add a new member."""
    owner_headers = get_auth_headers(client, TEST_USER_OWNER)
    # Register the second user so they exist in the DB
    client.post("/users/register", json=TEST_USER_MEMBER)

    # Owner creates a project
    project_res = client.post("/projects", headers=owner_headers, json={"name": "Collaboration Space"})
    project_id = project_res.json()["id"]

    # Owner adds the member
    response = client.post(
        f"/projects/{project_id}/members",
        headers=owner_headers,
        json={"email": TEST_USER_MEMBER["email"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["members"]) == 2
    member_emails = [member["email"] for member in data["members"]]
    assert TEST_USER_OWNER["email"] in member_emails
    assert TEST_USER_MEMBER["email"] in member_emails

def test_add_document_to_project_and_verify_access(client: TestClient, mocker: MockerFixture):
    """
    Test a full collaboration flow:
    1. Owner uploads a document.
    2. Owner creates a project and adds a member.
    3. Owner adds the document to the project.
    4. Verify the member can now see the document in their list.
    """
    # 1. Setup users and project
    owner_headers = get_auth_headers(client, TEST_USER_OWNER)
    member_headers = get_auth_headers(client, TEST_USER_MEMBER)
    
    project_res = client.post("/projects", headers=owner_headers, json={"name": "Shared Docs Project"})
    project_id = project_res.json()["id"]
    
    client.post(f"/projects/{project_id}/members", headers=owner_headers, json={"email": TEST_USER_MEMBER["email"]})

    # 2. Owner uploads a document
    mock_add_task = mocker.patch("fastapi.BackgroundTasks.add_task")
    fake_pdf = ("doc.pdf", io.BytesIO(b"test pdf content"), "application/pdf")
    upload_res = client.post("/upload", headers=owner_headers, files={"file": fake_pdf})
    doc_id = upload_res.json()["document_id"]

    # 3. Owner adds the document to the project
    response = client.post(
        f"/projects/{project_id}/documents",
        headers=owner_headers,
        json={"document_id": doc_id}
    )
    assert response.status_code == 200
    assert len(response.json()["documents"]) == 1
    assert response.json()["documents"][0]["id"] == doc_id

    # 4. Verify the member can see the shared document
    response = client.get("/documents", headers=member_headers)
    assert response.status_code == 200
    member_docs = response.json()
    assert len(member_docs) == 1
    assert member_docs[0]["id"] == doc_id
    assert member_docs[0]["filename"] == "doc.pdf"