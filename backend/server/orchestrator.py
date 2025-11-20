import asyncio
from .agents import intent_classifier, chat_agent, designing_agent, coding_agent
from .database import db

async def run_agent_pipeline(request):
    """Manages the sequential execution of agents."""
    
    project_id = request.project_id
    user_message = request.message

    yield {"event": "pipeline.started"}
    
    # Emit initial friendly narration
    yield {"event": "file.narrative", "path": "pipeline_start", "narrative": "I'm here to help you build something amazing. Let me start by understanding your request and figuring out the best approach to bring your vision to life."}

    # 1. Classify intent
    intent = await intent_classifier.classify_intent(user_message)
    yield {"event": "intent.classified", "intent": intent}

    # 2. Route based on intent
    ai_response = ""
    file_contents = {}  # Collect generated files
    
    if intent == "chat":
        async for event in chat_agent.run_chat_agent(user_message):
            if event.get("event") == "chat.chunk":
                ai_response += event.get("content", "")
            yield event
        
        # Store chat message in database
        db.add_chat_message(project_id, user_message, ai_response, intent)
        
    elif intent == "code":
        design_plan = None
        async for event in designing_agent.run_designing_agent(user_message):
            if event.get("event") == "design.completed":
                design_plan = event
            yield event
        
        if design_plan:
            async for event in coding_agent.run_coding_agent(design_plan, user_message):
                # Capture file content from code generation events
                if event.get("event") == "code.chunk":
                    file_path = event.get("file")
                    content = event.get("content", "")
                    if file_path:
                        file_contents[file_path] = file_contents.get(file_path, "") + content
                        print(f"DEBUG: Captured code chunk for {file_path}, total size now: {len(file_contents[file_path])} bytes")
                yield event
        
        # Debug: Print file contents before persisting
        print(f"DEBUG: File contents before persisting:")
        for file_path, content in file_contents.items():
            print(f"  {file_path}: {len(content)} bytes")
        
        # Persist generated files to database
        print(f"DEBUG: Persisting {len(file_contents)} files for project {project_id}")
        for file_path, file_content in file_contents.items():
            print(f"DEBUG: Saving file {file_path} with {len(file_content)} bytes")
            file_record = db.create_file(project_id, file_path, file_path.split('/')[-1])
            if file_record:
                db.save_code(file_record['id'], file_content)
                print(f"DEBUG: Successfully persisted {file_path}")
                yield {"event": "file.persisted", "path": file_path}
            else:
                print(f"DEBUG: Failed to create file record for {file_path}")
        
        # Store code request in database
        db.add_chat_message(project_id, user_message, str(design_plan), intent)

    yield {"event": "pipeline.completed"}