import google.generativeai as genai
from ..config import Config
from ..prompts import PromptLoader

# Configure the Gemini model
Config.validate()
genai.configure(api_key=Config.GOOGLE_API_KEY)
model = genai.GenerativeModel(Config.MODEL_NAME)


async def classify_intent(message: str) -> str:
    """Classifies the user's intent as 'chat' or 'code' using an LLM."""
    try:
        prompt_template = PromptLoader.get('intent_classifier')  # Updated to use new API
        prompt = prompt_template.format(message=message)
        response = await model.generate_content_async(prompt)

        # Clean up the response
        classification = response.text.strip().lower()

        if classification in ["chat", "code"]:
            return classification
        else:
            # Fallback in case of unexpected model output
            return "chat"

    except Exception as e:
        print(f"Error during intent classification: {e}")
        # Default to chat in case of any API error
        return "chat"