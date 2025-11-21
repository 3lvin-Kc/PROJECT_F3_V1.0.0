"""
Test script for the JSON-based prompt system.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.prompts import PromptLoader

def test_json_prompts():
    """Test that the JSON prompt system works correctly."""
    print("Testing JSON prompt system...")
    
    try:
        # Test loading all prompts
        prompts = PromptLoader.load()
        print("✓ JSON prompts loaded successfully")
        print(f"  Agents found: {list(prompts['agents'].keys())}")
        
        # Test getting specific prompts
        intent_prompt = PromptLoader.get('intent_classifier', 'classification')
        print("✓ Intent classifier prompt loaded")
        print(f"  Intent prompt length: {len(intent_prompt)} characters")
        
        chat_prompt = PromptLoader.get('chat_agent', 'response')
        print("✓ Chat agent prompt loaded")
        print(f"  Chat prompt length: {len(chat_prompt)} characters")
        
        design_prompt = PromptLoader.get('designing_agent', 'scaffold')
        print("✓ Designing agent prompt loaded")
        print(f"  Design prompt length: {len(design_prompt)} characters")
        
        coding_prompt = PromptLoader.get('coding_agent', 'generate_code')
        print("✓ Coding agent prompt loaded")
        print(f"  Coding prompt length: {len(coding_prompt)} characters")
        
        # Test formatting a prompt with variables
        design_files_str = "- lib/main.dart\n- lib/widgets/test_widget.dart"
        formatted_prompt = coding_prompt.format(
            design_files=design_files_str,
            message="Create a test widget"
        )
        print("✓ Coding prompt formatted successfully")
        print(f"  Formatted prompt length: {len(formatted_prompt)} characters")
        
        # Show a snippet of the formatted prompt
        print("\nFormatted prompt snippet:")
        print(formatted_prompt[:300] + "..." if len(formatted_prompt) > 300 else formatted_prompt)
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing JSON prompts: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("Testing JSON-based prompt system...\n")
    
    success = test_json_prompts()
    
    print("\n" + "="*50)
    print("TEST RESULT:")
    print(f"JSON prompt system: {'✓ PASS' if success else '✗ FAIL'}")
    print("="*50)
    
    if success:
        print("JSON prompt system is working correctly!")
    else:
        print("JSON prompt system has issues. Please check the errors above.")

if __name__ == "__main__":
    main()