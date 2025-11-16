"""
Chat Agent
==========
This agent handles conversational interactions in Chat Mode.
Think of it as the "consultant" that provides advice and guidance.

CRITICAL: This agent NEVER writes or shows code!

SERVER SIDE FILE
"""

from typing import Dict, Any, List, Optional
from ..models.message_models import Message, MessageRole
from ..services.ai_service import ai_service
from ..utils.prompt_templates import (
    CHAT_AGENT_SYSTEM,
    build_chat_prompt,
    format_conversation_history
)


class ChatAgent:
    """
    Handles conversational interactions without code generation.
    
    This agent:
    - Answers questions about Flutter development
    - Provides advice and best practices
    - Explains concepts and patterns
    - Helps brainstorm ideas
    - NEVER writes or shows code
    """
    
    def __init__(self):
        """Initialize the Chat Agent."""
        self.name = "ChatAgent"
        print(f" {self.name} initialized")
    
    
    # NOTE: Chat responses are now handled directly by the Agent Coordinator
    # using streaming AI service. This agent now provides utility methods only.
    
    
    def _format_history(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Convert Message objects to dict format for AI service.
        """
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in messages
        ]
    
    
    def _contains_code(self, text: str) -> bool:
        """
        Check if response accidentally contains code.
        
        This is a safety check to ensure Chat Mode doesn't leak code.
        """
        # Check for common code indicators
        code_indicators = [
            "```dart",       # Dart code blocks
            "```java",       # Java code blocks
            "```javascript", # JavaScript code blocks
            "```python",     # Python code blocks
            "```",           # Generic code blocks
            "class ",        # Dart class definitions
            "Widget build(", # Flutter widget build method
            "import 'package:", # Dart imports
            "void main()",   # Main function
            "setState(",     # Flutter state updates
        ]
        
        for indicator in code_indicators:
            if indicator in text:
                return True
        
        # Additional check for lines that look like code
        lines = text.split('\n')
        code_patterns = [
            r'^\s*[A-Za-z]+\s+[A-Za-z_][A-Za-z0-9_]*\s*\(.*\)\s*\{',  # Function definitions
            r'^\s*[A-Za-z_][A-Za-z0-9_]*\s*:\s*[A-Za-z_][A-Za-z0-9_]*',  # Variable declarations
            r'^\s*return\s+',  # Return statements
            r'^\s*if\s*\(',    # If statements
            r'^\s*for\s*\(',   # For loops
            r'^\s*while\s*\(', # While loops
        ]
        
        import re
        consecutive_code_lines = 0
        for line in lines:
            # Check if line matches code patterns
            for pattern in code_patterns:
                if re.match(pattern, line):
                    consecutive_code_lines += 1
                    break
            else:
                consecutive_code_lines = 0
            
            # If we find 3+ consecutive lines that look like code, flag it
            if consecutive_code_lines >= 3:
                return True
        
        return False
    
    
    def _sanitize_response(self, text: str) -> str:
        """
        Remove any code that accidentally leaked into the response.
        """
        # Remove markdown code blocks
        import re
        
        # Remove ```language ... ``` blocks (more comprehensive)
        text = re.sub(r'```[a-zA-Z]*\n.*?```', '[Code removed - please use Code Mode]', text, flags=re.DOTALL)
        
        # Remove generic ``` ... ``` blocks
        text = re.sub(r'```\n.*?```', '[Code removed - please use Code Mode]', text, flags=re.DOTALL)
        
        # Remove inline code
        text = re.sub(r'`[^`]+`', '[code snippet]', text)
        
        # Additional sanitization for code-like content
        # Look for common Flutter/Dart patterns and replace them
        flutter_patterns = [
            (r'class\s+[A-Za-z_][A-Za-z0-9_]*\s*', '[Class definition removed]'),
            (r'Widget\s+build\(\s*BuildContext\s+context\s*\)', '[Widget build method removed]'),
            (r'import\s+\'package:.*?\'', '[Import statement removed]'),
            (r'void\s+main\(\)', '[Main function removed]'),
            (r'setState\(\s*\(\s*\)\s*\{.*?\}\s*\)', '[setState call removed]'),
        ]
        
        for pattern, replacement in flutter_patterns:
            text = re.sub(pattern, replacement, text, flags=re.DOTALL)
        
        return text
    
    
    def _generate_error_response(self, error: str) -> str:
        """
        Generate a friendly error message.
        """
        return (
            "I apologize, but I encountered an issue generating a response. "
            "Could you please rephrase your question? If you need help with code, "
            "try switching to Code Mode."
        )
    
    
    def should_suggest_code_mode(self, message: str) -> bool:
        """
        Check if the user's message suggests they want code generation.
        
        If true, we can suggest they switch to Code Mode.
        """
        code_intent_keywords = [
            "create",
            "build",
            "make",
            "generate",
            "add",
            "implement",
            "write",
            "code",
            "widget"
        ]
        
        message_lower = message.lower()
        
        for keyword in code_intent_keywords:
            if keyword in message_lower:
                return True
        
        return False
    
    
    def generate_code_mode_suggestion(self) -> str:
        """
        Generate a suggestion to switch to Code Mode.
        """
        return (
            "\n\n **Tip:** If you'd like me to generate actual code for this, "
            "you can tell me and i'll switch to Code Mode and create the Flutter widgets for you!"
        )
    
    
    def format_response(
        self,
        content: str,
        add_code_mode_suggestion: bool = False
    ) -> str:
        """
        Format a response with optional code mode suggestion.
        """
        formatted = content
        
        if add_code_mode_suggestion:
            formatted += self.generate_code_mode_suggestion()
        
        return formatted
    
    
    def handle_error_explanation(
        self,
        error_message: str,
        error_context: Optional[str] = None
    ) -> str:
        """
        Provide a simple error explanation.
        
        Note: Detailed error analysis is now handled by the Error Recovery Agent
        with streaming support.
        """
        return f"""I see there was an error: {error_message}

This type of error typically occurs when there are issues with the code structure or dependencies. 

For detailed analysis and fixes, the system will automatically use the Error Recovery Agent to provide streaming assistance."""
    
    
    def create_welcome_message(self) -> str:
        """
        Generate a welcome message for new conversations.
        """
        return """ **Welcome to F3!**

I'm here to help you with your Flutter development! I can:
- Answer questions about Flutter concepts
- Suggest best practices and design patterns
- Help brainstorm UI/UX ideas
- Explain approaches and architectures
- Provide guidance on your project

**Note:** I'm currently in Chat Mode, which means I provide guidance and explanations without writing code. If you want me to generate actual Flutter widgets, just ask and I'll switch to Code Mode!

How can I help you today?"""


# Create singleton instance
chat_agent = ChatAgent()


# Export
__all__ = ['ChatAgent', 'chat_agent']