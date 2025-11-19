import google.generativeai as genai
from ..config import Config
from ..prompts import PromptLoader

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

        # Get the prompt template
        prompt_template = PromptLoader.get('coding_agent', 'generate_code')
        prompt = prompt_template.format(
            design_files=design_files_str,
            message=message
        )

        # Emit friendly narration for code generation start
        yield {"event": "file.narrative", "path": "code_start", "narrative": "Now I'm crafting the actual code for each component. I'll make sure everything works together seamlessly, following best practices and making the code clean and maintainable."}

        # Stream the code generation
        response_stream = await model.generate_content_async(prompt, stream=True)

        current_file = None
        file_index = 0
        file_contents = {}  # Store generated code for each file
        narrated_files = set()  # Track which files have been narrated

        async for chunk in response_stream:
            if chunk.text:
                text = chunk.text

                # Simple heuristic: detect file boundaries by looking for file paths
                for file_path in files:
                    if file_path in text and file_index < len(files):
                        # If we were working on a previous file, generate its narration now
                        if current_file and current_file not in narrated_files:
                            try:
                                code_snippet = file_contents.get(current_file, '')
                                if code_snippet:
                                    # Generate friendly paragraph narration while next file is being processed
                                    narration_prompt = f"""Based on this code for {current_file}, write a friendly 2-3 sentence paragraph explaining what this file does, its purpose, and how it fits into the overall component. Sound conversational and explain the creative choices made. Be warm and descriptive, not technical.

File: {current_file}
Code:
{code_snippet[:500]}...

Friendly explanation:"""
                                    
                                    narration_response = await model.generate_content_async(narration_prompt)
                                    narration_text = narration_response.text.strip()
                                    
                                    # Emit the narration event immediately
                                    yield {"event": "file.narrative", "path": current_file, "narrative": narration_text}
                                    narrated_files.add(current_file)
                            except Exception as e:
                                print(f"Error generating narration for {current_file}: {e}")
                        
                        # Start new file
                        current_file = file_path
                        file_index += 1
                        file_contents[current_file] = ''
                        yield {"event": "code.file_started", "file": current_file}
                        break

                # Stream the code chunk and accumulate for narration
                if current_file:
                    file_contents[current_file] = file_contents.get(current_file, '') + text
                yield {"event": "code.chunk", "content": text, "file": current_file}

        # Generate narration for the last file
        if current_file and current_file not in narrated_files:
            try:
                code_snippet = file_contents.get(current_file, '')
                if code_snippet:
                    narration_prompt = f"""Based on this code for {current_file}, write a friendly 2-3 sentence paragraph explaining what this file does, its purpose, and how it fits into the overall component. Sound conversational and explain the creative choices made. Be warm and descriptive, not technical.

File: {current_file}
Code:
{code_snippet[:500]}...

Friendly explanation:"""
                    
                    narration_response = await model.generate_content_async(narration_prompt)
                    narration_text = narration_response.text.strip()
                    
                    yield {"event": "file.narrative", "path": current_file, "narrative": narration_text}
                    narrated_files.add(current_file)
            except Exception as e:
                print(f"Error generating narration for {current_file}: {e}")

        # Emit completion event
        yield {"event": "code.completed", "files_generated": len(files)}

    except Exception as e:
        print(f"Error during code generation: {e}")
        yield {"event": "code.completed", "error": f"Failed to generate code: {str(e)}"}
