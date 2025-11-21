import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import Config
from .orchestrator import run_agent_pipeline
from .rate_limiter import get_rate_limiter
from .database import db

# Initialize configuration and validation
Config.validate()

# Setup logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter (10 requests per minute, 100 per hour for free tier)
rate_limiter = get_rate_limiter(requests_per_minute=10, requests_per_hour=100)

# Create FastAPI app
app = FastAPI(
    title="F3 Platform Backend",
    description="Agent-based code generation backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    message: str
    project_id: str


async def format_event(data: dict):
    """Format event data as SSE."""
    return f"data: {json.dumps(data)}\n\n"


async def agent_event_stream(request_data: AgentRequest):
    """Generate events from the agent pipeline."""
    async for event in run_agent_pipeline(request_data):
        yield await format_event(event)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "F3 Platform Backend"}


@app.get("/api/rate-limit-status")
async def rate_limit_status(http_request: Request):
    """Get current rate limit status for the client."""
    client_ip = http_request.client.host if http_request.client else "unknown"
    status = rate_limiter.get_status(client_ip)
    return {
        "client_ip": client_ip,
        "rate_limits": status,
    }


@app.post("/api/agent/stream")
async def agent_stream_endpoint(request: AgentRequest, http_request: Request):
    """Main agent pipeline streaming endpoint with rate limiting."""
    # Get client IP for rate limiting
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    # Check rate limit
    allowed, message = rate_limiter.is_allowed(client_ip)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {client_ip}: {message}")
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": message,
                "retry_after": 60,
            },
        )
    
    # Ensure project exists in database
    db.create_project(request.project_id)
    
    logger.info(f"Received request from {client_ip}: {request.message[:50]}... (project: {request.project_id})")
    return StreamingResponse(
        agent_event_stream(request),
        media_type="text/event-stream"
    )


@app.get("/api/projects/{project_id}")
async def get_project_endpoint(project_id: str):
    """Get project details including chat history."""
    project = db.get_project(project_id)
    
    if not project:
        return JSONResponse(
            status_code=404,
            content={"error": "Project not found"}
        )
    
    chat_history = db.get_chat_history(project_id)
    files = db.get_files_by_project(project_id)
    
    return {
        "project": dict(project),
        "chat_history": chat_history,
        "files": files,
        "file_count": len(files),
        "chat_count": len(chat_history)
    }


@app.get("/api/projects/{project_id}/chat-history")
async def get_chat_history_endpoint(project_id: str):
    """Get chat history for a project."""
    project = db.get_project(project_id)
    
    if not project:
        return JSONResponse(
            status_code=404,
            content={"error": "Project not found"}
        )
    
    chat_history = db.get_chat_history(project_id)
    return {"project_id": project_id, "chat_history": chat_history}


@app.get("/api/projects/{project_id}/files-with-content")
async def get_files_with_content(project_id: str):
    """Get all files with their content for a project."""
    project = db.get_project(project_id)
    
    if not project:
        return JSONResponse(
            status_code=404,
            content={"error": "Project not found"}
        )
    
    files = db.get_files_by_project(project_id)
    
    files_with_content = []
    for file_record in files:
        code_record = db.get_code_by_file(file_record['id'])
        files_with_content.append({
            'path': file_record['file_path'],
            'name': file_record['file_name'],
            'content': code_record['code_content'] if code_record else '',
            'created_at': file_record['created_at']
        })
    
    return {
        "project_id": project_id,
        "files": files_with_content,
        "file_count": len(files_with_content)
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("F3 Platform Backend started")
    logger.info(f"Model: {Config.MODEL_NAME}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("F3 Platform Backend shutting down")