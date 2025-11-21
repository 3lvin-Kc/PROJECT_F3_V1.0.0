"""
Test script for all agents with the new prompt system.
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.agents.intent_classifier import classify_intent
from backend.server.agents.chat_agent import run_chat_agent
from backend.server.agents.designing_agent import run_designing_agent

def test_intent_classifier():
    """Test the intent classifier."""
    print("Testing intent classifier...")
    
    # Test code intent
    code_intent = asyncio.run(classify_intent("build a profile card"))
    print(f"✓ Code intent classification: {code_intent}")
    
    # Test chat intent
    chat_intent = asyncio.run(classify_intent("what is flutter?"))
    print(f"✓ Chat intent classification: {chat_intent}")
    
    return code_intent == "code" and chat_intent == "chat"

async def test_chat_agent():
    """Test the chat agent."""
    print("\nTesting chat agent...")
    
    message = "What is Flutter?"
    response_text = ""
    
    async for event in run_chat_agent(message):
        if event.get("event") == "chat.chunk":
            response_text += event.get("content", "")
            # Just get a small chunk to verify it works
            if len(response_text) > 50:
                break
    
    print(f"✓ Chat agent response length: {len(response_text)} characters")
    return len(response_text) > 0

async def test_designing_agent():
    """Test the designing agent."""
    print("\nTesting designing agent...")
    
    message = "build a profile card"
    
    async for event in run_designing_agent(message):
        if event.get("event") == "design.completed":
            files = event.get("files", [])
            error = event.get("error")
            
            if error:
                print(f"✗ Design agent error: {error}")
                return False
            else:
                print(f"✓ Design agent generated {len(files)} files")
                print(f"  Files: {files}")
                return len(files) > 0
    
    return False

def main():
    """Run all tests."""
    print("Testing all agents with new prompt system...\n")
    
    # Test intent classifier
    intent_success = test_intent_classifier()
    
    # Test chat agent
    chat_success = asyncio.run(test_chat_agent())
    
    # Test designing agent
    design_success = asyncio.run(test_designing_agent())
    
    # Summary
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print(f"Intent classifier: {'✓ PASS' if intent_success else '✗ FAIL'}")
    print(f"Chat agent: {'✓ PASS' if chat_success else '✗ FAIL'}")
    print(f"Designing agent: {'✓ PASS' if design_success else '✗ FAIL'}")
    print("="*50)
    
    if intent_success and chat_success and design_success:
        print("All agents are working correctly with the new prompt system!")
    else:
        print("Some agents have issues. Please check the errors above.")

if __name__ == "__main__":
    main()