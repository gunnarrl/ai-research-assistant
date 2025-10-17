# backend/tests/test_chat.py

import io
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

# Import fixtures
from backend.database_test import client, session 

# A sample user for testing
TEST_USER = {"email": "chatter@example.com", "password": "password"}

# Helper function from another test file, useful here too
def get_auth_headers(client: TestClient, user: dict) -> dict:
    client.post("/users/register", json=user)
    login_data = {"username": user["email"], "password": user["password"]}
    response = client.post("/token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_chat_with_document(client: TestClient, mocker: MockerFixture):
    """
    Tests the /chat endpoint, mocking the search and Gemini services.
    """
    # 1. Setup user and a document ID
    headers = get_auth_headers(client, TEST_USER)
    # In a real test, you'd create a document first. For this mock, we just need an ID.
    doc_id = 1 
    
    # 2. Mock the service functions
    mocker.patch(
        "backend.main.find_relevant_chunks", 
        return_value=["mocked context chunk 1", "mocked context chunk 2"]
    )
    
    # Create an async generator to mock the streaming response from Gemini
    async def mock_gemini_stream():
        yield "This "
        yield "is a "
        yield "mocked answer."

    mocker.patch(
        "backend.main.get_answer_from_gemini", 
        return_value=mock_gemini_stream()
    )
    
    # We also need to mock the access check dependency
    mocker.patch(
        "backend.main.get_document_if_user_has_access",
        return_value=type('MockDoc', (), {'id': doc_id})() # Return a simple mock object
    )

    # 3. Call the chat endpoint
    response = client.post(
        "/chat",
        headers=headers,
        json={"document_id": doc_id, "question": "What is this about?"}
    )

    # 4. Assert the response
    assert response.status_code == 200
    
    # The response is a stream, so we check the concatenated content
    assert response.text == "This is a mocked answer."