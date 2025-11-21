"""
Test script for the coding agent with JSON structure generation.
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.agents.coding_agent import run_coding_agent

# Test design plan
test_design_plan = {
    "files": [
        "lib/main.dart",
        "lib/widgets/sample_widget.dart",
        "lib/preview/sample_widget_preview.dart",
        "pubspec.yaml",
        "README.md"
    ]
}

# Test message
test_message = "Create a simple counter widget with increment and decrement buttons"

async def test_coding_agent():
    """Test the coding agent with JSON structure generation."""
    print("Testing coding agent with JSON structure generation...")
    
    try:
        async for event in run_coding_agent(test_design_plan, test_message):
            print(f"Event: {event}")
            
            # If we get a structure completion event, show the structure
            if event.get("event") == "structure.completed":
                print("JSON Structure Generated:")
                print(event.get("structure"))
                
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_coding_agent())