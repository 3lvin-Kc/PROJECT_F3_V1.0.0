"""
Test suite for data persistence functionality.
Verifies that generated content is properly saved to and loaded from the database.
"""

import os
import sys
import tempfile
import pytest
import asyncio
import sqlite3
from unittest.mock import Mock

# Add the server directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from server.database import Database
from server.orchestrator import run_agent_pipeline

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
def test_project_id():
    """Generate a test project ID."""
    return "test_proj_12345"

@pytest.mark.asyncio
async def test_chat_messages_persisted(temp_database, test_project_id):
    """Verify chat messages are saved to database after chat interaction."""
    # Create project first
    temp_database.create_project(test_project_id)
    
    # Mock request for chat
    request = MockRequest(test_project_id, "Hello, how are you?")
    
    # Run pipeline
    events = []
    async for event in run_agent_pipeline(request):
        events.append(event)
    
    # Verify chat message was saved
    chat_history = temp_database.get_chat_history(test_project_id)
    assert len(chat_history) > 0, "No chat messages persisted to database"
    
    # Verify the content
    latest_message = chat_history[-1]
    assert latest_message['project_id'] == test_project_id
    assert latest_message['user_prompt'] == "Hello, how are you?"
    assert latest_message['intent'] == "chat"
    assert 'ai_response' in latest_message
    assert len(latest_message['ai_response']) > 0

@pytest.mark.asyncio
async def test_files_not_persisted_yet(temp_database, test_project_id):
    """Verify that files are NOT currently being saved to database (demonstrates the bug)."""
    # Create project first
    temp_database.create_project(test_project_id)
    
    # Mock request for code generation
    request = MockRequest(test_project_id, "Build a login button component")
    
    # Run pipeline
    events = []
    async for event in run_agent_pipeline(request):
        events.append(event)
    
    # Verify files are NOT saved (this demonstrates the current bug)
    files = temp_database.get_files_by_project(test_project_id)
    assert len(files) == 0, "Files should NOT be persisted yet (this is the bug we're testing)"
    
    # Verify code is NOT saved
    # Since there are no files, there should be no code records
    # This test will pass while the bug exists, and fail once it's fixed
    conn = temp_database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM code')
    code_count = cursor.fetchone()[0]
    conn.close()
    
    assert code_count == 0, "Code should NOT be persisted yet (this is the bug we're testing)"

@pytest.mark.asyncio
async def test_database_schema_integrity(temp_database):
    """Verify that database schema is correct and all tables exist."""
    conn = temp_database.get_connection()
    cursor = conn.cursor()
    
    # Check that all expected tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = {'projects', 'chat_history', 'files', 'code'}
    assert expected_tables.issubset(set(tables)), f"Missing tables: {expected_tables - set(tables)}"
    
    # Check projects table structure
    cursor.execute("PRAGMA table_info(projects)")
    project_columns = [row[1] for row in cursor.fetchall()]
    expected_project_columns = {'id', 'project_id', 'created_at', 'updated_at'}
    assert expected_project_columns.issubset(set(project_columns)), f"Projects table missing columns"
    
    # Check files table structure
    cursor.execute("PRAGMA table_info(files)")
    file_columns = [row[1] for row in cursor.fetchall()]
    expected_file_columns = {'id', 'project_id', 'file_path', 'file_name', 'created_at', 'updated_at'}
    assert expected_file_columns.issubset(set(file_columns)), f"Files table missing columns"
    
    # Check code table structure
    cursor.execute("PRAGMA table_info(code)")
    code_columns = [row[1] for row in cursor.fetchall()]
    expected_code_columns = {'id', 'file_id', 'code_content', 'created_at', 'updated_at'}
    assert expected_code_columns.issubset(set(code_columns)), f"Code table missing columns"
    
    conn.close()

def test_database_crud_operations(temp_database, test_project_id):
    """Test basic CRUD operations for the database."""
    # Test project creation
    project = temp_database.create_project(test_project_id)
    assert project is not None
    assert project['project_id'] == test_project_id
    
    # Test project retrieval
    retrieved_project = temp_database.get_project(test_project_id)
    assert retrieved_project is not None
    assert retrieved_project['project_id'] == test_project_id
    
    # Test file creation
    file_record = temp_database.create_file(test_project_id, "lib/main.dart", "main.dart")
    assert file_record is not None
    assert file_record['project_id'] == test_project_id
    assert file_record['file_path'] == "lib/main.dart"
    assert file_record['file_name'] == "main.dart"
    
    # Test file retrieval
    files = temp_database.get_files_by_project(test_project_id)
    assert len(files) == 1
    assert files[0]['file_path'] == "lib/main.dart"
    
    # Test code saving
    code_record = temp_database.save_code(file_record['id'], "void main() {}")
    assert code_record is not None
    assert code_record['file_id'] == file_record['id']
    assert code_record['code_content'] == "void main() {}"
    
    # Test code retrieval
    retrieved_code = temp_database.get_code_by_file(file_record['id'])
    assert retrieved_code is not None
    assert retrieved_code['code_content'] == "void main() {}"

if __name__ == "__main__":
    pytest.main([__file__])