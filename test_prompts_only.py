"""
Test script for prompt loading only.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.prompts import PromptLoader

def test_prompt_loading():
    """Test that all prompts load correctly."""
    print("Testing prompt loading...")
    
    try:
        # Load all prompts
        prompts = PromptLoader.load()
        print("✓ All prompts loaded successfully")
        print(f"  Agents found: {list(prompts.keys())}")
        
        # Test each agent prompt
        for agent in ['intent_classifier', 'chat_agent', 'designing_agent', 'coding_agent']:
            prompt = PromptLoader.get(agent)
            print(f"✓ {agent} prompt loaded ({len(prompt)} characters)")
            
            # Test formatting if it has format placeholders
            if '{message}' in prompt or '{design_files}' in prompt:
                try:
                    if agent == 'coding_agent':
                        formatted = prompt.format(
                            design_files="- lib/main.dart\n- lib/widgets/test.dart",
                            message="test message"
                        )
                    elif agent == 'designing_agent':
                        formatted = prompt.format(message="test message")
                    else:
                        formatted = prompt.format(message="test message")
                    print(f"  Formatted successfully ({len(formatted)} characters)")
                except Exception as e:
                    print(f"  Formatting error: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading prompts: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("Testing prompt loading only...\n")
    
    success = test_prompt_loading()
    
    print("\n" + "="*50)
    print("TEST RESULT:")
    print(f"Prompt loading: {'✓ PASS' if success else '✗ FAIL'}")
    print("="*50)
    
    if success:
        print("All prompts are loading correctly!")
    else:
        print("There are issues with prompt loading.")

if __name__ == "__main__":
    main()