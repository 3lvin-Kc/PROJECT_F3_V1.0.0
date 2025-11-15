#!/usr/bin/env python3
"""
Simple F3 Backend Server
========================
A minimal working version to get the server running quickly.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="F3 AI Backend",
    description="AI-powered Flutter widget generation platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple request/response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    project_context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    content: str
    intent: str = "chat"
    files_modified: list = []
    conversation_id: Optional[str] = None

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "F3 AI Backend",
        "version": "1.0.0",
        "message": "Welcome to F3 AI Platform!"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents": {
            "intent_classifier": "active",
            "planning_agent": "active", 
            "coding_agent": "active",
            "error_recovery_agent": "active",
            "chat_agent": "active"
        },
        "services": {
            "compiler": "mock",
            "file_service": "active",
            "preview": "active",
            "project_manager": "active"
        }
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"Received chat request: {request.message[:50]}...")
        
        # Simple response for now
        response = ChatResponse(
            content=f"Hello! I received your message: '{request.message}'. The F3 platform is starting up!",
            intent="chat",
            files_modified=[],
            conversation_id=request.conversation_id
        )
        
        return response
        
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting F3 Backend Server...")
    print("🔗 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("🎯 Frontend should connect from: http://localhost:5173")
    print("-" * 60)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
