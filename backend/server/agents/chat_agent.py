import google.generativeai as genai
from ..config import Config
from ..prompts import PromptLoader

# Configure the Gemini model
Config.validate()
genai.configure(api_key=Config.GOOGLE_API_KEY)
model = genai.GenerativeModel(Config.MODEL_NAME)


async def run_chat_agent(message: str):
    """Handles conversational interactions by streaming the response."""
    try:
        prompt_template = PromptLoader.get('chat_agent', 'response')
        prompt = prompt_template.format(message=message)
        response_stream = await model.generate_content_async(prompt, stream=True)

        async for chunk in response_stream:
            if chunk.text:
                yield {"event": "chat.chunk", "content": chunk.text}

    except Exception as e:
        print(f"Error during chat generation: {e}")
        yield {"event": "chat.chunk", "content": "Sorry, I encountered an error. Please try again."}
