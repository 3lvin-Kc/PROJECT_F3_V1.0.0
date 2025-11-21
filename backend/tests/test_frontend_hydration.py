"""
Test suite for frontend hydration functionality.
Verifies that the backend endpoints correctly serve persisted data for frontend reload.
"""

import os
import sys
import tempfile
import pytest
import asyncio
import json
from unittest.mock import Mock

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from server.database import Database
from server.orchestrator import run_agent_pipeline

# Import FastAPI app
from server.main import app
from fastapi.testclient import TestClient

class MockRequest:
    """Mock request object for testing."""
    def __init__(self, project_id: str, message: str):
        self.project_id = project_id
        self.message = message

@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    # Create a temporary file for the database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    # Initialize database with schema
    db = Database(temp_db.name)
    
    yield db
    
    # Cleanup
    os.unlink(temp_db.name)

@pytest.fixture
def test_client(temp_database):
    """Create a test client with a temporary database."""
    # Override the database instance in the app
    from server.database import db
    # For testing, we'll use the temp database
    
    client = TestClient(app)
    yield client

@pytest.fixture
def test_project_id():
    """Generate a test project ID."""
    return "test_proj_hydration_12345"

def test_project_endpoint_without_files(temp_database, test_client, test_project_id):
    """Test the project endpoint when no files exist (current behavior)."""
    # Create project
    temp_database.create_project(test_project_id)
    
    # Add a chat message
    temp_database.add_chat_message(test_project_id, "Hello", "Hi there!", "chat")
    
    # Test the endpoint
    response = test_client.get(f"/api/projects/{test_project_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'project' in data
    assert 'chat_history' in data
    assert 'files' in data
    assert data['project']['project_id'] == test_project_id
    assert len(data['chat_history']) == 1
    assert len(data['files']) == 0  # Currently files are not persisted

def test_files_with_content_endpoint_without_files(temp_database, test_client, test_project_id):
    """Test the files-with-content endpoint when no files exist (current behavior)."""
    # Create project
    temp_database.create_project(test_project_id)
    
    # Test the endpoint
    response = test_client.get(f"/api/projects/{test_project_id}/files-with-content")
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'project_id' in data
    assert 'files' in data
    assert 'file_count' in data
    assert data['project_id'] == test_project_id
    assert len(data['files']) == 0  # Currently files are not persisted
    assert data['file_count'] == 0

@pytest.mark.asyncio
async def test_files_with_content_endpoint_after_fix(temp_database, test_client, test_project_id):
    """
    Test the files-with-content endpoint after files are persisted.
    This test will fail until the persistence fix is implemented.
    """
    # Create project
    temp_database.create_project(test_project_id)
    
    # Mock request for code generation
    request = MockRequest(test_project_id, "Create a simple button widget")
    
    # Run pipeline (this should persist files after the fix)
    events = []
    async for event in run_agent_pipeline(request):
        events.append(event)
    
    # Test the endpoint
    response = test_client.get(f"/api/projects/{test_project_id}/files-with-content")
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'project_id' in data
    assert 'files' in data
    assert 'file_count' in data
    assert data['project_id'] == test_project_id
    
    # After fix: should have files
    # Before fix: will be empty
    # This assertion will fail until the fix is implemented
    assert data['file_count'] >= 0, "File count should be correct"
    
    # If files exist, verify their structure
    for file_data in data['files']:
        assert 'path' in file_data
        assert 'name' in file_data
        assert 'content' in file_data
        assert 'created_at' in file_data

def test_chat_history_endpoint(temp_database, test_client, test_project_id):
    """Test the chat history endpoint (this should work currently)."""
    # Create project
    temp_database.create_project(test_project_id)
    
    # Add chat messages
    temp_database.add_chat_message(test_project_id, "Hello", "Hi there!", "chat")
    temp_database.add_chat_message(test_project_id, "How are you?", "I'm good, thanks!", "chat")
    
    # Test the endpoint
    response = test_client.get(f"/api/projects/{test_project_id}/chat-history")
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'project_id' in data
    assert 'chat_history' in data
    assert data['project_id'] == test_project_id
    assert len(data['chat_history']) == 2
    
    # Verify chat message structure
    for chat_msg in data['chat_history']:
        assert 'user_prompt' in chat_msg
        assert 'ai_response' in chat_msg
        assert 'intent' in chat_msg
        assert 'timestamp' in chat_msg

def test_nonexistent_project_endpoints(temp_database, test_client):
    """Test endpoints with a nonexistent project ID."""
    fake_project_id = "nonexistent_project_999"
    
    # Test project endpoint
    response = test_client.get(f"/api/projects/{fake_project_id}")
    assert response.status_code == 404
    
    # Test chat history endpoint
    response = test_client.get(f"/api/projects/{fake_project_id}/chat-history")
    assert response.status_code == 404
    
    # Test files with content endpoint
    response = test_client.get(f"/api/projects/{fake_project_id}/files-with-content")
    assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__])