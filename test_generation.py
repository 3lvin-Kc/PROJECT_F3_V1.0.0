import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.orchestrator import run_agent_pipeline
from backend.server.database import db

# Create a mock request object
class MockRequest:
    def __init__(self, project_id, message):
        self.project_id = project_id
        self.message = message

async def test_generation():
    # Create the project if it doesn't exist
    project_id = 'proj_1763573158247_uprzix6gj'
    db.create_project(project_id)
    
    # Create a mock request
    request = MockRequest(project_id, 'build a profile card.')
    
    print("Starting code generation test...")
    print(f"Project ID: {project_id}")
    print(f"Prompt: {request.message}")
    
    # Run the agent pipeline
    try:
        async for event in run_agent_pipeline(request):
            print(f"Event: {event}")
            
            # Check if we have any errors
            if 'error' in event:
                print(f"Error occurred: {event['error']}")
                break
                
    except Exception as e:
        print(f"Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generation())