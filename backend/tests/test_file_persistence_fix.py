"""
Test suite for file persistence functionality after fix is implemented.
This test suite will verify that files are properly saved to and loaded from the database.
"""

import os
import sys
import tempfile
import pytest
import asyncio
from unittest.mock import Mock, patch

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
    return "test_proj_fixed_12345"

@pytest.mark.asyncio
async def test_files_persisted_after_fix(temp_database, test_project_id):
    """
    Verify files are saved to database after code generation.
    This test will fail until the persistence fix is implemented.
    """
    # Create project first
    temp_database.create_project(test_project_id)
    
    # Mock request for code generation
    request = MockRequest(test_project_id, "Build a login button component")
    
    # Run pipeline
    events = []
    async for event in run_agent_pipeline(request):
        events.append(event)
    
    # After the fix is implemented, files should be saved to the database
    # This test will initially fail (demonstrating the bug) and pass after the fix
    
    files = temp_database.get_files_by_project(test_project_id)
    
    # This assertion will fail until the fix is implemented
    # Once the fix is in place, this assertion should pass
    assert len(files) > 0, "Files should be persisted to database after the fix is implemented"
    
    # Verify that each file has associated code
    for file_record in files:
        file_id = file_record['id']
        code_record = temp_database.get_code_by_file(file_id)
        assert code_record is not None, f"No code found for file {file_record['file_path']}"
        assert len(code_record['code_content']) > 0, f"Code content is empty for file {file_record['file_path']}"

@pytest.mark.asyncio
async def test_file_content_integrity(temp_database, test_project_id):
    """
    Verify that file content is correctly saved and retrieved.
    This test will fail until the persistence fix is implemented.
    """
    # Create project first
    temp_database.create_project(test_project_id)
    
    # Mock request for code generation
    request = MockRequest(test_project_id, "Create a simple counter widget")
    
    # Collect file content during streaming
    file_contents_during_streaming = {}
    
    # Run pipeline and collect file content
    events = []
    async for event in run_agent_pipeline(request):
        events.append(event)
        
        # Collect file content as it's streamed
        if event.get('event') == 'code.chunk' and 'file' in event and 'content' in event:
            file_path = event['file']
            content = event['content']
            if file_path:
                if file_path not in file_contents_during_streaming:
                    file_contents_during_streaming[file_path] = ""
                file_contents_during_streaming[file_path] += content
    
    # After the fix, verify that the content saved to DB matches what was streamed
    files = temp_database.get_files_by_project(test_project_id)
    
    # This assertion will fail until the fix is implemented
    assert len(files) > 0, "Files should be persisted to database after the fix is implemented"
    
    # Verify content integrity for each file
    for file_record in files:
        file_path = file_record['file_path']
        file_id = file_record['id']
        
        # Get content from database
        code_record = temp_database.get_code_by_file(file_id)
        db_content = code_record['code_content'] if code_record else ""
        
        # Get content from streaming (what should have been saved)
        streamed_content = file_contents_during_streaming.get(file_path, "")
        
        # After fix: content should match
        # Before fix: this will fail because db_content will be empty
        assert len(db_content) > 0, f"File {file_path} should have content in database"
        assert db_content == streamed_content, f"Database content for {file_path} should match streamed content"

@pytest.mark.asyncio
async def test_project_summary_includes_files(temp_database, test_project_id):
    """
    Verify that project summary includes file information.
    This test will fail until the persistence fix is implemented.
    """
    # Create project first
    temp_database.create_project(test_project_id)
    
    # Mock request for code generation
    request = MockRequest(test_project_id, "Build a profile card component")
    
    # Run pipeline
    events = []
    async for event in run_agent_pipeline(request):
        events.append(event)
    
    # Get project summary
    summary = temp_database.get_project_summary(test_project_id)
    
    # This assertion will fail until the fix is implemented
    assert summary is not None, "Project summary should be available"
    assert 'project' in summary, "Project summary should include project info"
    assert 'files' in summary, "Project summary should include files"
    assert 'file_count' in summary, "Project summary should include file count"
    
    # After fix: file count should be greater than 0
    # Before fix: file count will be 0
    assert summary['file_count'] > 0, "Project should have files after code generation"

if __name__ == "__main__":
    pytest.main([__file__])