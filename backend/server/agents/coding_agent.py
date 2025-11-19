import google.generativeai as genai
from ..config import Config
from ..prompts import PromptLoader

# Configure the Gemini model
Config.validate()
genai.configure(api_key=Config.GOOGLE_API_KEY)
model = genai.GenerativeModel(Config.MODEL_NAME)


async def run_coding_agent(design_plan: dict, message: str):
    """
    Generates code for each file in the design plan.

    Args:
        design_plan: Dict containing 'files' list from DesigningAgent
        message: Original user request

    Yields:
        Events with code generation progress
    """
    yield {"event": "code.started"}

    try:
        files = design_plan.get("files", [])

        if not files:
            yield {"event": "code.completed", "error": "No files in design plan"}
            return

        # Validate that no file paths contain unresolved placeholders
        for file_path in files:
            if '{' in file_path or '}' in file_path:
                error_msg = f"Invalid file path with unresolved placeholder: {file_path}"
                yield {"event": "code.completed", "error": error_msg}
                return

        # Format the design files for the prompt
        design_files_str = "\n".join([f"- {file}" for file in files])

        # Get the prompt template
        prompt_template = PromptLoader.get('coding_agent', 'generate_code')
        prompt = prompt_template.format(
            design_files=design_files_str,
            message=message
        )

        # Stream the code generation
        response_stream = await model.generate_content_async(prompt, stream=True)

        current_file = None
        file_index = 0

        async for chunk in response_stream:
            if chunk.text:
                text = chunk.text

                # Simple heuristic: detect file boundaries by looking for file paths
                for file_path in files:
                    if file_path in text and file_index < len(files):
                        # Emit file started event
                        current_file = file_path
                        file_index += 1
                        yield {"event": "code.file_started", "file": current_file}
                        break

                # Stream the code chunk
                yield {"event": "code.chunk", "content": text, "file": current_file}

        # Emit completion event
        yield {"event": "code.completed", "files_generated": len(files)}

    except Exception as e:
        print(f"Error during code generation: {e}")
        yield {"event": "code.completed", "error": f"Failed to generate code: {str(e)}"}
