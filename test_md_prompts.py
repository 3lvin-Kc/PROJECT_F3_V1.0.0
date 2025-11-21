"""
Test script for the Markdown-based prompt system.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.prompts import PromptLoader

def test_md_prompts():
    """Test that the Markdown prompt system works correctly."""
    print("Testing Markdown prompt system...")
    
    try:
        # Test loading all prompts
        prompts = PromptLoader.load()
        print("✓ Markdown prompts loaded successfully")
        print(f"  Agents found: {list(prompts.keys())}")
        
        # Test getting specific prompts
        intent_prompt = PromptLoader.get('intent_classifier')
        print("✓ Intent classifier prompt loaded")
        print(f"  Intent prompt length: {len(intent_prompt)} characters")
        
        chat_prompt = PromptLoader.get('chat_agent')
        print("✓ Chat agent prompt loaded")
        print(f"  Chat prompt length: {len(chat_prompt)} characters")
        
        design_prompt = PromptLoader.get('designing_agent')
        print("✓ Designing agent prompt loaded")
        print(f"  Design prompt length: {len(design_prompt)} characters")
        
        coding_prompt = PromptLoader.get('coding_agent')
        print("✓ Coding agent prompt loaded")
        print(f"  Coding prompt length: {len(coding_prompt)} characters")
        
        # Show a snippet of each prompt
        print("\nPrompt snippets:")
        print("Intent classifier:", intent_prompt[:100] + "..." if len(intent_prompt) > 100 else intent_prompt)
        print("Chat agent:", chat_prompt[:100] + "..." if len(chat_prompt) > 100 else chat_prompt)
        print("Designing agent:", design_prompt[:100] + "..." if len(design_prompt) > 100 else design_prompt)
        print("Coding agent:", coding_prompt[:100] + "..." if len(coding_prompt) > 100 else coding_prompt)
        
        # Test formatting a prompt with variables
        design_files_str = "- lib/main.dart\n- lib/widgets/test_widget.dart"
        formatted_prompt = coding_prompt.format(
            design_files=design_files_str,
            message="Create a test widget"
        )
        print("✓ Coding prompt formatted successfully")
        print(f"  Formatted prompt length: {len(formatted_prompt)} characters")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing Markdown prompts: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("Testing Markdown-based prompt system...\n")
    
    success = test_md_prompts()
    
    print("\n" + "="*50)
    print("TEST RESULT:")
    print(f"Markdown prompt system: {'✓ PASS' if success else '✗ FAIL'}")
    print("="*50)
    
    if success:
        print("Markdown prompt system is working correctly!")
    else:
        print("Markdown prompt system has issues. Please check the errors above.")

if __name__ == "__main__":
    main()