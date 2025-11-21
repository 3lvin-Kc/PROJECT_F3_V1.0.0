"""
Debug script for prompt loading.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.prompts import PromptLoader

# Test design plan
test_files = [
    "lib/main.dart",
    "lib/widgets/sample_widget.dart",
    "lib/preview/sample_widget_preview.dart",
    "pubspec.yaml",
    "README.md"
]

# Format the design files for the prompt
design_files_str = "\n".join([f"- {file}" for file in test_files])

# Test message
test_message = "Create a simple counter widget with increment and decrement buttons"

def test_prompt():
    """Test the prompt loading and formatting."""
    print("Testing prompt loading and formatting...")
    
    try:
        # Get the prompt template for generating JSON structure
        prompt_template = PromptLoader.get('coding_agent', 'generate_structure')
        print("Prompt template loaded successfully")
        print("Template keys:", [key for key in prompt_template.split('{') if '}' in key])
        
        # Try to format the prompt
        prompt = prompt_template.format(
            design_files=design_files_str,
            message=test_message
        )
        print("Prompt formatted successfully")
        print("Prompt preview:")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prompt()