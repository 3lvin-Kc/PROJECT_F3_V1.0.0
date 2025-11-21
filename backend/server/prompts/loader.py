import os
import re


class PromptLoader:
    """Centralized prompt loader for all agents."""
    _prompts = {}

    @classmethod
    def load(cls):
        """Load prompts from Markdown files (cached in memory)."""
        if not cls._prompts:
            prompts_dir = os.path.join(os.path.dirname(__file__), 'md')
            
            # Load each prompt file
            for filename in os.listdir(prompts_dir):
                if filename.endswith('.md'):
                    agent_name = filename[:-3]  # Remove .md extension
                    file_path = os.path.join(prompts_dir, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Escape curly braces in code blocks to prevent format conflicts
                        # Find code blocks and escape their curly braces
                        def escape_code_blocks(text):
                            # Pattern to match code blocks
                            pattern = r'```[\s\S]*?```'
                            def replace_braces(match):
                                # Replace { with {{ and } with }} in code blocks
                                return match.group().replace('{', '{{').replace('}', '}}')
                            return re.sub(pattern, replace_braces, text)
                        
                        content = escape_code_blocks(content)
                        cls._prompts[agent_name] = content
        
        return cls._prompts

    @classmethod
    def get(cls, agent: str, prompt_key: str = None) -> str:
        """
        Get a specific prompt for an agent.

        Args:
            agent: Agent name (e.g., 'intent_classifier', 'chat_agent')
            prompt_key: Not used for Markdown prompts, kept for compatibility

        Returns:
            The prompt template string.

        Raises:
            KeyError: If agent not found.
        """
        prompts = cls.load()
        return prompts[agent]