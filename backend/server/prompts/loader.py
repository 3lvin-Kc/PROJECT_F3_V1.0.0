import yaml
import os


class PromptLoader:
    """Centralized prompt loader for all agents."""
    _prompts = None

    @classmethod
    def load(cls):
        """Load prompts from YAML file (cached in memory)."""
        if cls._prompts is None:
            path = os.path.join(os.path.dirname(__file__), 'prompts.yaml')
            with open(path, 'r') as f:
                cls._prompts = yaml.safe_load(f)
        return cls._prompts

    @classmethod
    def get(cls, agent: str, prompt_key: str) -> str:
        """
        Get a specific prompt for an agent.

        Args:
            agent: Agent name (e.g., 'intent_classifier', 'chat_agent')
            prompt_key: Prompt key within the agent (e.g., 'classification', 'response')

        Returns:
            The prompt template string.

        Raises:
            KeyError: If agent or prompt_key not found.
        """
        prompts = cls.load()
        return prompts['agents'][agent][prompt_key]
