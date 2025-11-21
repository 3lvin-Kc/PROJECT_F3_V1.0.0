import json
import re
import google.generativeai as genai
from ..config import Config
from ..prompts import PromptLoader

# Configure the Gemini model
Config.validate()
genai.configure(api_key=Config.GOOGLE_API_KEY)
model = genai.GenerativeModel(Config.MODEL_NAME)


async def run_designing_agent(message: str):
    """Generates the high-level plan for the coding agent."""
    yield {"event": "design.started"}
    
    # Emit friendly narration for design phase start
    yield {"event": "file.narrative", "path": "design_phase", "narrative": "I'm taking a moment to understand what you're looking for and how best to approach this design. Let me analyze your request and think through the best structure for your component."}

    try:
        prompt_template = PromptLoader.get('designing_agent')  # Updated to use new API
        prompt = prompt_template.format(message=message)
        response = await model.generate_content_async(prompt)

        yield {"event": "design.phase", "details": "Outlining file structure..."}

        # More robust response cleaning to handle markdown code blocks
        cleaned_response = response.text.strip()
        
        # Remove markdown code block markers
        cleaned_response = re.sub(r'^```(?:json)?', '', cleaned_response)
        cleaned_response = re.sub(r'```$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        # Parse JSON with improved error handling
        try:
            design = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # Debug: Print the error
            print(f"DEBUG: JSON parsing error: {e}")
            
            # Try to fix common JSON issues
            fixed_response = cleaned_response
            # Fix missing quotes around keys
            fixed_response = re.sub(r'(\w+)(?=\s*:)', r'"\1"', fixed_response)
            # Fix single quotes to double quotes
            fixed_response = fixed_response.replace("'", '"')
            
            # Debug: Print the fixed response
            print(f"DEBUG: Fixed response: {fixed_response}")
            
            try:
                design = json.loads(fixed_response)
                print(f"DEBUG: Successfully parsed fixed JSON: {design}")
            except json.JSONDecodeError:
                raise e  # Re-raise original error if fix didn't work

        # Extract files with better error handling
        if not isinstance(design, dict):
            raise ValueError(f"Expected JSON object, got {type(design).__name__}: {design}")
            
        files = design.get("files", [])
        
        # Handle case where files might be a string instead of list
        if isinstance(files, str):
            try:
                files = json.loads(files)
            except json.JSONDecodeError:
                files = [files]  # Treat as single file path
        
        # Validate that files is a list
        if not isinstance(files, list):
            raise ValueError(f"Files field must be a list, got {type(files).__name__}: {files}")

        # Validate that files list is not empty and contains valid paths
        if not files:
            raise ValueError("Files list is empty")

        # Validate that no file paths contain unresolved placeholders
        for file_path in files:
            if not isinstance(file_path, str):
                raise ValueError(f"File path must be a string, got {type(file_path).__name__}: {file_path}")
            if '{' in file_path or '}' in file_path:
                raise ValueError(f"File path contains unresolved placeholder: {file_path}")

        yield {"event": "design.completed", "files": files}

    except json.JSONDecodeError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"JSON parsing error during design generation: {e}")
        logger.error(f"Response text was: {response.text if 'response' in locals() else 'N/A'}")
        print(f"Error during design generation: JSON parsing failed - {e}")
        yield {"event": "design.completed", "files": [], "error": "Failed to parse design plan JSON."}
    except ValueError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Validation error during design generation: {e}")
        print(f"Error during design generation: {e}")
        yield {"event": "design.completed", "files": [], "error": str(e)}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error during design generation: {e}")
        print(f"Error during design generation: {e}")
        yield {"event": "design.completed", "files": [], "error": "Failed to generate a design plan."}