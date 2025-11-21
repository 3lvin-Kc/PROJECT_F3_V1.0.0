import json
import re
import google.generativeai as genai
from ..config import Config
from ..prompts import PromptLoader
from .json_to_flutter_converter import convert_json_to_flutter

# Configure the Gemini model
Config.validate()
genai.configure(api_key=Config.GOOGLE_API_KEY)
model = genai.GenerativeModel(Config.MODEL_NAME)


async def run_coding_agent(design_plan: dict, message: str):
    """
    Generates code for each file in the design plan and streams narration in real-time.

    Args:
        design_plan: Dict containing 'files' list from DesigningAgent
        message: Original user request

    Yields:
        Events with code generation progress and real-time narration
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

        # Get the prompt template for generating JSON structure
        prompt_template = PromptLoader.get('coding_agent')  # Updated to use new API
        prompt = prompt_template.format(
            design_files=design_files_str,
            message=message
        )

        # Emit friendly narration for code generation start
        yield {"event": "file.narrative", "path": "code_start", "narrative": "Now I'm crafting the actual code for each component. I'll make sure everything works together seamlessly, following best practices and making the code clean and maintainable."}

        # Generate the JSON structure
        response = await model.generate_content_async(prompt)
        
        # Debug: Print the raw response
        print(f"DEBUG: Raw AI response: {response.text[:200]}...")
        
        # Clean the response by removing markdown code blocks
        cleaned_response = response.text.strip()
        # Remove markdown code block markers
        cleaned_response = re.sub(r'^```(?:json)?', '', cleaned_response)
        cleaned_response = re.sub(r'```$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()
        
        print(f"DEBUG: Cleaned response: {cleaned_response[:200]}...")
        
        # Parse the JSON structure
        json_structure = json.loads(cleaned_response)
        
        # Emit structure completion event
        yield {"event": "structure.completed", "structure": json_structure}
        
        # Convert JSON structure to Flutter code
        file_contents = convert_json_to_flutter(json_structure)
        
        # Stream the generated code
        current_file = None
        file_index = 0
        narrated_files = set()  # Track which files have been narrated

        for file_path, code_content in file_contents.items():
            # Start new file
            current_file = file_path
            file_index += 1
            yield {"event": "code.file_started", "file": current_file}
            
            # Split code into chunks for streaming
            chunk_size = 100
            for i in range(0, len(code_content), chunk_size):
                chunk = code_content[i:i+chunk_size]
                yield {"event": "code.chunk", "content": chunk, "file": current_file}

            # Generate narration for the file
            if current_file and current_file not in narrated_files:
                try:
                    code_snippet = code_content[:500] if len(code_content) > 500 else code_content
                    if code_snippet:
                        # Generate friendly paragraph narration while next file is being processed
                        narration_prompt = f"""Based on this code for {current_file}, write a friendly 2-3 sentence paragraph explaining what this file does, its purpose, and how it fits into the overall component. Sound conversational and explain the creative choices made. Be warm and descriptive, not technical.

File: {current_file}
Code:
{code_snippet}...

Friendly explanation:"""
                        
                        narration_response = await model.generate_content_async(narration_prompt)
                        narration_text = narration_response.text.strip()
                        
                        # Emit the narration event immediately
                        yield {"event": "file.narrative", "path": current_file, "narrative": narration_text}
                        narrated_files.add(current_file)
                except Exception as e:
                    print(f"Error generating narration for {current_file}: {e}")

        # Debug: Print file contents summary
        print(f"DEBUG: File contents summary:")
        for file_path, content in file_contents.items():
            print(f"  {file_path}: {len(content)} characters")
        
        # Emit completion event
        yield {"event": "code.completed", "files_generated": len(files)}

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON structure: {e}")
        print(f"Response text was: {response.text if 'response' in locals() else 'N/A'}")
        yield {"event": "code.completed", "error": f"Failed to parse JSON structure: {str(e)}"}
    except Exception as e:
        print(f"Error during code generation: {e}")
        import traceback
        traceback.print_exc()
        yield {"event": "code.completed", "error": f"Failed to generate code: {str(e)}"}