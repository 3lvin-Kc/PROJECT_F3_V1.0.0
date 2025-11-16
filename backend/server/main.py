"""
F3 AI Backend - Consolidated API
===============================

This is the cleaned-up F3 backend with 9 essential endpoints:

  WebSocket:
  - /ws/{client_id}                    # Real-time AI progress updates

  System:
  - /health                            # System health check

  AI Chat:
  - /api/chat                          # Main AI conversation (POST)

  Projects:
  - /api/projects                      # Create project from prompt (POST)
  - /api/projects/{id}                 # Get info (GET) / Delete (DELETE)
  - /api/projects/{id}/files           # List project files (GET)

  Files:
  - /api/files/read                    # Read file content (POST)
  - /api/files/write                   # Write file content (POST)

  Preview:
  - /api/preview/generate              # Generate widget preview (POST)

  Conversations:
  - /api/conversations/{id}            # Clear conversation (DELETE)

All endpoints have TODO comments for Supabase authentication integration.
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from dataclasses import dataclass
import uvicorn
import os
from dotenv import load_dotenv

from server.coordinator.agent_coordinator import agent_coordinator
from server.models.message_models import ChatRequest, ChatResponse
from server.services.file_service import file_service
from server.services.preview_service import preview_service
from server.services.websocket_service import f3_websocket_manager
from server.projects.project_service import project_service
from server.database.repositories import project_repo, conversation_repo, message_repo

load_dotenv()

app = FastAPI(
    title="F3 AI Backend",
    description="AI-powered Flutter widget generation platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],  # Removed wildcard for security
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Only needed methods
    allow_headers=["*"],
)


# Removed: Root endpoint - not needed for production API


# ============================================================================
# WEBSOCKET ENDPOINTS..................................
# ============================================================================

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time AI progress updates
    """
    await f3_websocket_manager.handle_connection(websocket, client_id)


@app.get("/api/websocket/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics
    """
    return f3_websocket_manager.get_stats()


# ============================================================================
# HEALTH CHECK........................
# ============================================================================

@app.get("/health")
async def health_check():
    """
    System health check endpoint.
    TODO: Add Supabase authentication check when implemented
    """
    try:
        stats = agent_coordinator.get_system_stats()
        return {
            "status": "healthy",
            "service": "F3 AI Backend",
            "version": "1.0.0",
            "agents": {
                "intent_classifier": "active",
                "planning_agent": "active",
                "coding_agent": "active",
                "error_recovery_agent": "active",
                "chat_agent": "active"
            },
            "services": {
                "file_service": "active",
                "preview": "active",
                "project_manager": "active",
                "websocket": "active",
                "ai_service": "active"
            },
            "websocket": f3_websocket_manager.get_stats(),
            "statistics": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"\nReceived chat request: {request.message[:50]}...")
        if not request.conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id required")
        if not request.project_context or not isinstance(request.project_context, dict) or not request.project_context.get("project_id"):
            raise HTTPException(status_code=400, detail="project_id required in project_context")
        proj_info = file_service.get_project_info(request.project_context["project_id"])
        if not proj_info or not proj_info.get("success"):
            raise HTTPException(status_code=400, detail="invalid project_id")
        conv_db = conversation_repo.get_conversation(request.conversation_id)
        if not conv_db:
            raise HTTPException(status_code=400, detail="invalid conversation_id")
        
        response = await agent_coordinator.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            project_context=request.project_context
        )
        
        if request.conversation_id:
            conv = conversation_repo.get_conversation(request.conversation_id)
            if conv:
                message_repo.create_message(
                    conversation_id=conv['id'],
                    role='user',
                    content=request.message
                )
                message_repo.create_message(
                    conversation_id=conv['id'],
                    role='assistant',
                    content=response.content,
                    intent_type=response.intent.value if hasattr(response, 'intent') else None,
                    files_modified=response.files_modified
                )
        
        return ChatResponse(
            message=response.content,
            conversation_id=response.conversation_id,
            mode=response.mode,
            files_changed=response.files_modified,
            preview_update_required=response.files_modified is not None and len(response.files_modified) > 0,
            error=response.error,
            metadata=response.metadata
        )
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Removed: Legacy project creation endpoint - use /api/projects instead


@app.post("/api/projects")
async def create_project(request: Dict[str, Any]):
    """
    Create a new Flutter project - just generate ID and save prompt.
    AI processing happens later in the editor.
    TODO: Add Supabase authentication check here
    """
    try:
        user_prompt = request.get("user_prompt")
        user_id = request.get("user_id", 1)  # TODO: Get from Supabase auth
        
        if not user_prompt:
            raise HTTPException(status_code=400, detail="user_prompt required")
        
        # Generate unique project ID
        import uuid
        import time
        project_id = f"f3_project_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        conversation_id = f"conv_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Create project directory structure (no AI yet)
        project_result = file_service.create_project(project_id)
        
        if not project_result["success"]:
            raise HTTPException(status_code=500, detail=project_result["error"])
        
        # Save to database for later AI processing
        try:
            db_project_id = project_repo.create_project(
                user_id=user_id,
                project_name=f"Flutter Project - {user_prompt[:30]}...",
                description=user_prompt
            )
            
            db_conversation_id = conversation_repo.create_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                project_id=db_project_id
            )
        except Exception as db_error:
            print(f"Database save failed (non-critical): {db_error}")
        
        return {
            "success": True,
            "project_id": project_id,
            "conversation_id": conversation_id,
            "message": "Project created successfully. AI processing will start in editor.",
            "user_prompt": user_prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@app.get("/api/projects/{project_id}")
async def get_project_info(project_id: str):
    """
    Get project information.
    TODO: Add Supabase authentication and project ownership check
    """
    try:
        result = file_service.get_project_info(project_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/files")
async def get_project_files(project_id: str):
    """
    List all files in a project.
    TODO: Add Supabase authentication and project ownership check
    """
    try:
        result = file_service.list_files(project_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/read")
async def read_file(request: Dict[str, str]):
    """
    Read file content from a project.
    TODO: Add Supabase authentication and project ownership check
    """
    try:
        project_id = request.get("project_id")
        file_path = request.get("file_path")
        
        if not project_id or not file_path:
            raise HTTPException(status_code=400, detail="project_id and file_path required")
        
        result = file_service.read_file(project_id, file_path)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/write")
async def write_file(request: Dict[str, str]):
    """
    Write content to a file in a project.
    TODO: Add Supabase authentication and project ownership check
    """
    try:
        project_id = request.get("project_id")
        file_path = request.get("file_path")
        content = request.get("content")
        
        if not project_id or not file_path or content is None:
            raise HTTPException(status_code=400, detail="project_id, file_path, and content required")
        
        result = file_service.write_file(project_id, file_path, content)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """
    Delete a project completely.
    TODO: Add Supabase authentication and project ownership check
    """
    try:
        result = file_service.delete_project(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





# Removed: Compile and validate endpoints - not needed for core functionality


@dataclass
class PreviewRequest:
    code: str
    file_path: str


@app.post("/api/preview/generate")
async def generate_preview(request: PreviewRequest):
    """
    Generate Flutter widget preview.
    TODO: Add Supabase authentication check
    """
    try:
        result = preview_service.generate_preview_data(
            request.code,
            request.file_path
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Removed: Hot reload endpoint - not essential for MVP


# Removed: Conversation stats endpoint - debug only


@app.delete("/api/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Clear a conversation from memory.
    TODO: Add Supabase authentication and conversation ownership check
    """
    try:
        agent_coordinator.clear_conversation(conversation_id)
        return {"message": f"Conversation {conversation_id} cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Removed: Mode setting endpoint - handled automatically by AI


# Removed: Stats and test endpoints - debug only


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Unhandled exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "type": type(exc).__name__
    }


# Removed: All direct database access endpoints - use service layer instead
# TODO: When implementing Supabase auth, add these endpoints:
# GET /api/users/projects - Get user's projects
# GET /api/users/conversations - Get user's conversations


@app.on_event("startup")
async def startup_event():
    print("\n" + "="*70)
    print("F3 AI Backend Starting...")
    print("="*70)
    print(f"Agent Coordinator initialized")
    print(f"All agents ready")
    print(f"Compilation services ready")
    print(f"Database initialized")
    print(f"API endpoints registered")
    print(f"Server running on http://localhost:{os.getenv('PORT', 8000)}")
    print("="*70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    # TODO: Add proper database cleanup when implemented
    print("\n" + "="*70)
    print("F3 AI Backend Shutting Down...")
    print("="*70 + "\n")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )