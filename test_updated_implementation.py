"""
Test script for the updated implementation with JSON structure generation.
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.prompts import PromptLoader
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

def test_prompt():
    """Test that the updated prompt works correctly."""
    print("Testing updated prompt...")
    
    try:
        # Get the updated prompt template
        prompt_template = PromptLoader.get('coding_agent', 'generate_code')
        print("✓ Prompt template loaded successfully")
        
        # Format the design files for the prompt
        design_files_str = "\n".join([f"- {file}" for file in test_design_plan["files"]])
        
        # Try to format the prompt
        prompt = prompt_template.format(
            design_files=design_files_str,
            message=test_message
        )
        print("✓ Prompt formatted successfully")
        print(f"Prompt length: {len(prompt)} characters")
        return True
        
    except Exception as e:
        print(f"✗ Error testing prompt: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_coding_agent():
    """Test the coding agent with JSON structure generation."""
    print("\nTesting coding agent...")
    
    try:
        event_count = 0
        async for event in run_coding_agent(test_design_plan, test_message):
            event_count += 1
            print(f"Event {event_count}: {event.get('event', 'unknown')}")
            
            # If we get a structure completion event, show a snippet of the structure
            if event.get("event") == "structure.completed":
                structure = event.get("structure")
                print(f"✓ JSON Structure Generated (showing first file):")
                if structure and "files" in structure and len(structure["files"]) > 0:
                    first_file = structure["files"][0]
                    print(f"  Path: {first_file.get('path', 'N/A')}")
                    print(f"  Type: {first_file.get('type', 'N/A')}")
                    print(f"  Components: {len(first_file.get('components', []))}")
                
        print(f"✓ Coding agent test completed with {event_count} events")
        return True
        
    except Exception as e:
        print(f"✗ Error during coding agent test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Testing updated implementation...\n")
    
    # Test prompt
    prompt_success = test_prompt()
    
    # Test coding agent
    agent_success = asyncio.run(test_coding_agent())
    
    # Summary
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print(f"Prompt test: {'✓ PASS' if prompt_success else '✗ FAIL'}")
    print(f"Coding agent test: {'✓ PASS' if agent_success else '✗ FAIL'}")
    print("="*50)
    
    if prompt_success and agent_success:
        print("All tests passed! The implementation is working correctly.")
    else:
        print("Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()