# backend/tests/test_documents.py

import io
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

# Import the fixtures we created
from backend.database_test import client, session 

# A sample user for testing
TEST_USER = {"email": "test@example.com", "password": "a-secure-password"}

def get_auth_headers(client: TestClient, user: dict) -> dict:
    """Helper function to register and log in a user to get auth headers."""
    client.post("/users/register", json=user)
    login_data = {"username": user["email"], "password": user["password"]}
    response = client.post("/token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_upload_pdf(client: TestClient, mocker: MockerFixture):
    """
    Tests the /upload endpoint, mocking the background task.
    """
    # 1. Create a user and log in to get an auth token
    client.post("/users/register", json=TEST_USER)
    login_data = {"username": TEST_USER["email"], "password": TEST_USER["password"]}
    response = client.post("/token", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Mock the background_tasks.add_task function
    # This prevents the real, slow processing task from running.
    mock_add_task = mocker.patch("fastapi.BackgroundTasks.add_task")

    # 3. Simulate a file upload
    # Create a fake PDF file in memory
    fake_pdf_content = b"%PDF-1.5 fake content"
    file_to_upload = ("test.pdf", io.BytesIO(fake_pdf_content), "application/pdf")
    
    response = client.post(
        "/upload", 
        headers=headers, 
        files={"file": file_to_upload}
    )

    # 4. Assert the response and that the background task was scheduled
    assert response.status_code == 200
    assert "File upload started" in response.json()["message"]
    
    # Assert that add_task was called exactly once
    mock_add_task.assert_called_once()

def test_delete_document(client: TestClient, mocker: MockerFixture):
    """Tests that a user can delete their own document."""
    # 1. Setup user and upload a document
    headers = get_auth_headers(client, {"email": "delete@test.com", "password": "password"})
    mocker.patch("fastapi.BackgroundTasks.add_task")
    
    # Create a document by calling the upload endpoint
    upload_res = client.post(
        "/upload", 
        headers=headers, 
        files={"file": ("test_del.pdf", io.BytesIO(b"content"), "application/pdf")}
    )
    doc_id = upload_res.json()["document_id"]

    # 2. List documents to confirm it exists
    list_res = client.get("/documents", headers=headers)
    assert len(list_res.json()) == 1
    
    # 3. Delete the document
    delete_res = client.delete(f"/documents/{doc_id}", headers=headers)
    assert delete_res.status_code == 204 # 204 No Content is the expected success code

    # 4. List documents again to confirm it's gone
    final_list_res = client.get("/documents", headers=headers)
    assert len(final_list_res.json()) == 0


def test_import_from_arxiv(client: TestClient, mocker: MockerFixture):
    """Tests the import-from-url endpoint by mocking the arXiv and download services."""
    headers = get_auth_headers(client, {"email": "import@test.com", "password": "password"})
    
    # Mock the background task so no real processing happens
    mock_add_task = mocker.patch("fastapi.BackgroundTasks.add_task")
    
    # Mock the download service to avoid a real network call
    mocker.patch(
        "backend.main.download_and_create_document", 
        return_value=(
            # The first element of the return tuple is a mock Document object
            type('MockDoc', (), {'id': 99, 'filename': 'Test ArXiv Paper'})(), 
            # The second is the file_bytes
            b"fake pdf bytes"
        )
    )

    # Call the import endpoint
    response = client.post(
        "/import-from-url",
        headers=headers,
        json={"pdf_url": "http://fake.arxiv.org/pdf/1234.5678", "title": "Test ArXiv Paper"}
    )

    assert response.status_code == 200
    assert "File import started" in response.json()["message"]
    # Verify the background task was scheduled
    mock_add_task.assert_called_once()


def test_start_literature_review(client: TestClient, mocker: MockerFixture):
    """Tests that the literature review agent can be started."""
    headers = get_auth_headers(client, {"email": "agent@test.com", "password": "password"})
    
    # Mock the agent workflow itself so it doesn't actually run
    mock_agent_workflow = mocker.patch("backend.main._agent_workflow")

    response = client.post(
        "/agent/literature-review",
        headers=headers,
        json={"topic": "testing with pytest"}
    )
    
    assert response.status_code == 202 # 202 Accepted
    data = response.json()
    assert data["topic"] == "testing with pytest"
    assert data["status"] == "PENDING"
    
    # Verify the background task for the agent was scheduled
    mock_agent_workflow.assert_called_once()