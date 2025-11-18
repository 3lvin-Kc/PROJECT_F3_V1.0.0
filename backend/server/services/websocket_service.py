"""
WebSocket Service for F3 Platform
Handles real-time AI progress updates and chat communication
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Any, Callable, Awaitable
import json
import asyncio
from datetime import datetime
import time
from enum import Enum


class AIProgressStatus(str, Enum):
    """AI Processing Status Types"""
    ANALYZING = "analyzing"
    PLANNING = "planning" 
    CODING = "coding"
    VALIDATING = "validating"
    COMPILING = "compiling"
    COMPLETE = "complete"
    ERROR = "error"


class ConnectionManager:
    """Manages WebSocket connections for F3 platform"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_connections: Dict[str, List[str]] = {}  # conversation_id -> [client_ids]
        self.streaming_sessions: Dict[str, Dict] = {}  # Track active streaming sessions
        print("F3 WebSocket ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str, conversation_id: Optional[str] = None):
        """Connect a client to WebSocket"""
        await websocket.accept()
        
        self.active_connections[client_id] = websocket
        
        # Associate client with conversation
        if conversation_id:
            if conversation_id not in self.conversation_connections:
                self.conversation_connections[conversation_id] = []
            if client_id not in self.conversation_connections[conversation_id]:
                self.conversation_connections[conversation_id].append(client_id)
        
        print(f"F3 Client {client_id} connected to conversation {conversation_id}")
    
    def disconnect(self, client_id: str, conversation_id: Optional[str] = None):
        """Disconnect a client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        # Remove from conversation
        if conversation_id and conversation_id in self.conversation_connections:
            if client_id in self.conversation_connections[conversation_id]:
                self.conversation_connections[conversation_id].remove(client_id)
            
            # Clean up empty conversations
            if not self.conversation_connections[conversation_id]:
                del self.conversation_connections[conversation_id]
        
        print(f"F3 Client {client_id} disconnected from conversation {conversation_id}")
    
    async def send_to_client(self, message: Dict[str, Any], client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def send_to_conversation(self, message: Dict[str, Any], conversation_id: str):
        """Send message to all clients in a conversation"""
        if conversation_id not in self.conversation_connections:
            return
        
        dead_connections = []
        
        for client_id in self.conversation_connections[conversation_id]:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    print(f"Error sending to conversation {conversation_id}, client {client_id}: {e}")
                    dead_connections.append(client_id)
        
        # Clean up dead connections
        for client_id in dead_connections:
            self.disconnect(client_id, conversation_id)
    
    def get_conversation_clients(self, conversation_id: str) -> List[str]:
        """Get all clients in a conversation"""
        return self.conversation_connections.get(conversation_id, [])
    
    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)


class F3WebSocketManager:
    """Main WebSocket manager for F3 platform"""
    
    def __init__(self):
        """Initialize the F3 WebSocket Manager."""
        self.manager = ConnectionManager()
        self.message_handlers: Dict[str, Callable[..., Any]] = {}
        self.streaming_sessions: Dict[str, Dict] = {}  # Track active streaming sessions
        print("F3 WebSocketManager initialized with streaming support")
    
    async def _silent_callback(self, stream_data: Dict):
        """Silent callback for internal AI processing - doesn't send to users."""
        # Progress updates can happen internally without user-visible streaming
        pass
    
    def _register_handlers(self):
        """Register message handlers"""
        self.message_handlers = {
            "ping": self._handle_ping,
            "join_conversation": self._handle_join_conversation,
            "leave_conversation": self._handle_leave_conversation,
            "chat_message": self._handle_chat_message,
        }
    
    async def handle_connection(self, websocket: WebSocket, client_id: str):
        """Handle new WebSocket connection"""
        await self.manager.connect(websocket, client_id)
        
        # Send connection confirmation
        await self.manager.send_to_client({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to F3 AI Platform"
        }, client_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_message(data, client_id)
        
        except WebSocketDisconnect:
            self.manager.disconnect(client_id)
        except Exception as e:
            print(f"F3 WebSocket error for {client_id}: {e}")
            self.manager.disconnect(client_id)
    
    async def _process_message(self, data: str, client_id: str):
        """Process incoming WebSocket message"""
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](message, client_id)
            else:
                await self.manager.send_to_client({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }, client_id)
        
        except json.JSONDecodeError:
            await self.manager.send_to_client({
                "type": "error",
                "message": "Invalid JSON format"
            }, client_id)
        except Exception as e:
            await self.manager.send_to_client({
                "type": "error",
                "message": str(e)
            }, client_id)
    
    async def _handle_ping(self, message: Dict, client_id: str):
        """Handle ping message"""
        await self.manager.send_to_client({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, client_id)
    
    async def _handle_join_conversation(self, message: Dict, client_id: str):
        """Handle joining a conversation"""
        conversation_id = message.get("conversation_id")
        
        if conversation_id:
            # Update connection mapping
            if conversation_id not in self.manager.conversation_connections:
                self.manager.conversation_connections[conversation_id] = []
            if client_id not in self.manager.conversation_connections[conversation_id]:
                self.manager.conversation_connections[conversation_id].append(client_id)
            
            await self.manager.send_to_client({
                "type": "conversation_joined",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }, client_id)
    
    async def _handle_leave_conversation(self, message: Dict, client_id: str):
        """Handle leaving a conversation"""
        conversation_id = message.get("conversation_id")
        
        if conversation_id and conversation_id in self.manager.conversation_connections:
            if client_id in self.manager.conversation_connections[conversation_id]:
                self.manager.conversation_connections[conversation_id].remove(client_id)
            
            await self.manager.send_to_client({
                "type": "conversation_left",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }, client_id)
    
    async def _handle_chat_message(self, message: Dict, client_id: str):
        """Handle chat message (for future use)"""
        conversation_id = message.get("conversation_id")
        content = message.get("content")
        
        if conversation_id and content:
            # Broadcast to conversation participants
            await self.manager.send_to_conversation({
                "type": "chat_message",
                "conversation_id": conversation_id,
                "client_id": client_id,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }, conversation_id)
    
    # ============================================================================
    # AI PROGRESS TRACKING METHODS...................................................................
    # ============================================================================
    
    async def send_progress_update(self, conversation_id: str, status: str, message: str = "", files_created: Optional[List[str]] = None, error_message: Optional[str] = None, user_prompt: str = ""):
        """Send conversational progress updates to the user"""
        if status == "analyzing":
            await self.send_ai_analyzing(conversation_id, user_prompt)
        elif status == "planning":
            await self.send_ai_planning(conversation_id, user_prompt)
        elif status == "coding":
            await self.send_ai_coding(conversation_id, files_created)
        elif status == "validating":
            await self.send_ai_validating(conversation_id)
        elif status == "complete":
            await self.send_ai_complete(conversation_id, files_created)
        elif status == "error":
            await self.send_ai_error(conversation_id, error_message or "Unknown error")
        else:
            # Generic progress update
            await self.send_ai_progress(conversation_id, AIProgressStatus.ANALYZING, message)
    
    async def send_ai_progress(self, conversation_id: str, status: AIProgressStatus, message: str, details: Optional[Dict] = None):
        """Send AI progress update to conversation"""
        progress_message: Dict[str, Any] = {
            "type": "ai_progress",
            "conversation_id": conversation_id,
            "status": status.value,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            progress_message["details"] = details
        
        await self.manager.send_to_conversation(progress_message, conversation_id)
    
    async def send_ai_analyzing(self, conversation_id: str, user_prompt: str):
        """AI is analyzing user request - Generate contextual response"""
        try:
            # Import AI service for real-time generation
            from ..services.ai_service import ai_service
            
            # Generate contextual analyzing message based on the specific prompt
            system_prompt = """You are an AI assistant working on a Flutter project. The user can see your progress in real-time. 
            Generate a natural, conversational message explaining what you're currently analyzing about their request. 
            Be specific about what you're thinking regarding their particular project type.
            Keep it under 150 words and sound like you're genuinely thinking through their request.
            Do not use emojis. Be professional but conversational."""
            
            user_message = f"I'm analyzing this Flutter project request: '{user_prompt}'. Generate a message explaining what I'm currently thinking about and analyzing regarding this specific request."
            
            message = await ai_service.generate_response(
                prompt=user_message,
                system_instruction=system_prompt,
                temperature=0.7,
                websocket_callback=self._silent_callback,
                conversation_id="progress_analyzing"
            )
            
        except Exception as e:
            # Fallback to a generic message if AI generation fails
            print(f"AI generation failed for analyzing phase: {e}")
            message = f"I'm starting to work on your Flutter project. Let me analyze what you're looking for: '{user_prompt[:100]}...' and determine the best approach."
        
        await self.send_ai_progress(
            conversation_id, 
            AIProgressStatus.ANALYZING,
            message,
            {
                "phase": "Understanding Requirements",
                "progress": 15,
                "estimated_time": "About 3 minutes remaining"
            }
        )
    
    async def send_ai_planning(self, conversation_id: str, user_prompt: str):
        """AI is planning the solution - Generate contextual response"""
        try:
            from ..services.ai_service import ai_service
            
            # Generate contextual planning message based on project type
            system_prompt = """You are an AI assistant planning a Flutter project architecture. 
            Generate a natural message explaining what you're currently planning and designing for this specific project.
            Mention specific Flutter concepts, widgets, or patterns that are relevant to their request.
            Be detailed about your architectural decisions. Keep it under 150 words.
            Do not use emojis. Sound like an experienced Flutter developer thinking through the design."""
            
            user_message = f"I'm now planning the architecture for this Flutter project: '{user_prompt}'. Explain what I'm specifically planning and designing for this type of project."
            
            message = await ai_service.generate_response(
                prompt=user_message,
                system_instruction=system_prompt,
                temperature=0.7,
                websocket_callback=self._silent_callback,
                conversation_id="progress_planning"
            )
            
        except Exception as e:
            print(f"AI generation failed for planning phase: {e}")
            message = "Now I'm creating the technical blueprint for your project. I'm planning the file structure, architecture, and determining the best Flutter widgets to use."
        
        await self.send_ai_progress(
            conversation_id,
            AIProgressStatus.PLANNING,
            message,
            {
                "phase": "Planning Architecture",
                "progress": 35,
                "estimated_time": "About 2 minutes remaining"
            }
        )
    
    async def send_ai_coding(self, conversation_id: str, files_created: Optional[List[str]] = None, user_prompt: str = ""):
        """AI is generating code - Generate contextual response"""
        try:
            from ..services.ai_service import ai_service
            
            # Generate contextual coding message based on current files and project type
            system_prompt = """You are an enthusiastic Flutter developer who is excited to build amazing widgets and components.
            Generate a natural, conversational message explaining what you're currently coding and implementing.
            Be specific about the Flutter widgets, state management, or features you're working on.
            If files are being created, mention what's in those specific files.
            Keep it under 150 words. Sound excited and helpful. Do not use emojis.
            Examples:
            - "Oh, I love this idea! Let me build this amazing button component for you. I'm starting with the core widget structure..."
            - "This is going to be great! I'm working on the main layout file that will tie everything together. This will make your UI really responsive..."
            - "I'm creating the state management logic that will make this widget really powerful. You'll be able to easily customize all the behaviors..."
            """
            
            files_context = f" Currently creating files: {', '.join(files_created)}" if files_created else ""
            user_message = f"I'm coding this Flutter project: '{user_prompt}'.{files_context} Explain what I'm specifically implementing right now with enthusiasm."
            
            message = await ai_service.generate_response(
                prompt=user_message,
                system_instruction=system_prompt,
                temperature=0.7,
                websocket_callback=self._silent_callback,
                conversation_id="progress_coding"
            )
            
        except Exception as e:
            print(f"AI generation failed for coding phase: {e}")
            if files_created and len(files_created) > 0:
                current_file = files_created[-1]
                message = f"Oh, I love this idea! Let me build this for you. I'm currently working on {current_file} and implementing the core functionality."
            else:
                message = "This is going to be great! I'm now writing the Flutter code for your project and implementing the user interface and core functionality."
        
        await self.send_ai_progress(
            conversation_id,
            AIProgressStatus.CODING,
            message,
            {
                "phase": "Writing Flutter Code",
                "progress": 75,
                "estimated_time": "About 1 minute remaining",
                "files_created": files_created or []
            }
        )
    
    async def send_ai_validating(self, conversation_id: str):
        """AI is validating code"""
        message = "I'm doing a final review of your Flutter project to ensure everything is perfect. I'm checking that all the code follows best practices, verifying that the components work well together, and making sure the styling is consistent throughout. Just putting the finishing touches on your project."
        
        await self.send_ai_progress(
            conversation_id,
            AIProgressStatus.VALIDATING,
            message,
            {
                "phase": "Final Review",
                "progress": 90,
                "estimated_time": "Almost done"
            }
        )
    
    async def send_ai_compiling(self, conversation_id: str):
        """AI is compiling code"""
        await self.send_ai_progress(
            conversation_id,
            AIProgressStatus.COMPILING,
            "🔨 Compiling Flutter project..."
        )
    
    async def send_ai_complete(self, conversation_id: str, files_created: Optional[List[str]] = None, user_prompt: str = ""):
        """AI has completed the task - Generate contextual completion message"""
        try:
            from ..services.ai_service import ai_service
            
            # Generate contextual completion message based on what was actually built
            system_prompt = """You are an enthusiastic Flutter developer who just finished creating a project.
            Generate an enthusiastic but professional completion message explaining what you've accomplished.
            Be specific about the features and components you've created for this particular project.
            Mention what the user can now do with their project.
            Also provide 2-3 suggestions for how they can improve or extend this further.
            Keep it under 200 words.
            Do not use emojis. Sound proud of the work completed.
            Example format:
            "Perfect! I've successfully created your Flutter [component/widget/app] with [X] files. Everything is ready for you to preview and customize further.
            
            Here's what I built:
            - [Feature 1]
            - [Feature 2]
            - [Feature 3]
            
            To make this even better, you could:
            1. [Suggestion 1]
            2. [Suggestion 2]
            3. [Suggestion 3]"
            """
            
            files_context = f" Created {len(files_created)} files: {', '.join(files_created)}" if files_created else ""
            user_message = f"I just completed this Flutter project: '{user_prompt}'.{files_context} Generate a completion message explaining what I've accomplished with enthusiasm and suggestions."
            
            message = await ai_service.generate_response(
                prompt=user_message,
                system_instruction=system_prompt,
                temperature=0.7,
                websocket_callback=self._silent_callback,
                conversation_id="progress_completion"
            )
            
        except Exception as e:
            print(f"AI generation failed for completion phase: {e}")
            file_count = len(files_created) if files_created else 0
            message = f"Perfect! I've successfully created your Flutter project with {file_count} files. Everything is ready for you to preview and customize further.\n\nTo make this even better, try asking me to add animations, improve the styling, or add more functionality!"
        
        await self.send_ai_progress(
            conversation_id,
            AIProgressStatus.COMPLETE,
            message,
            {
                "phase": "Project Complete",
                "progress": 100,
                "files_created": files_created or [],
                "file_count": len(files_created) if files_created else 0
            }
        )
    
    async def send_ai_error(self, conversation_id: str, error_message: str, error_type: Optional[str] = None):
        """AI encountered an error"""
        message = f"I encountered an issue while working on your project: {error_message}. Let me try a different approach to resolve this. I'm analyzing what went wrong and will adjust my strategy to ensure your project gets created successfully."
        
        await self.send_ai_progress(
            conversation_id,
            AIProgressStatus.ERROR,
            message,
            {
                "phase": "Resolving Issue",
                "error_type": error_type,
                "original_error": error_message
            }
        )
    
    # ============================================================================
    # FILE UPDATES....................................
    # ============================================================================
    
    async def send_file_update(self, conversation_id: str, file_path: str, content: str, operation: str = "update"):
        """Send file update notification"""
        await self.manager.send_to_conversation({
            "type": "file_update",
            "conversation_id": conversation_id,
            "file_path": file_path,
            "content": content,
            "operation": operation,  # "create", "update", "delete"
            "timestamp": datetime.now().isoformat()
        }, conversation_id)
    
    async def send_preview_update(self, conversation_id: str, preview_data: Dict):
        """Send preview update"""
        await self.manager.send_to_conversation({
            "type": "preview_update",
            "conversation_id": conversation_id,
            "preview_data": preview_data,
            "timestamp": datetime.now().isoformat()
        }, conversation_id)
    
    # ============================================================================
    # UTILITY METHODS....
    # ============================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            "total_connections": self.manager.get_total_connections(),
            "active_conversations": len(self.manager.conversation_connections),
            "conversations": {
                conv_id: {
                    "client_count": len(clients),
                    "clients": clients
                }
                for conv_id, clients in self.manager.conversation_connections.items()
            }
        }
    
    async def streaming_callback(self, stream_data: Dict):
        """
        Callback function for AI streaming responses.
        Routes streaming tokens to the appropriate conversation.
        """
        conversation_id = stream_data.get("conversation_id")
        if not conversation_id:
            return
        
        stream_type = stream_data.get("type")
        
        if stream_type == "stream_start":
            # Initialize streaming session
            self.streaming_sessions[conversation_id] = {
                "start_time": time.time(),
                "tokens_sent": 0,
                "is_active": True
            }
            
            message = {
                "type": "ai_stream_start",
                "conversation_id": conversation_id,
                "timestamp": time.time()
            }
            
        elif stream_type == "stream_token":
            # Send streaming tokens
            if conversation_id in self.streaming_sessions:
                self.streaming_sessions[conversation_id]["tokens_sent"] += 1
            
            message = {
                "type": "ai_stream_token",
                "conversation_id": conversation_id,
                "content": stream_data.get("content", ""),
                "timestamp": time.time()
            }
            
        elif stream_type == "stream_complete":
            # Complete streaming session
            if conversation_id in self.streaming_sessions:
                session = self.streaming_sessions[conversation_id]
                session["is_active"] = False
                session["end_time"] = time.time()
                session["duration"] = session["end_time"] - session["start_time"]
            
            message = {
                "type": "ai_stream_complete",
                "conversation_id": conversation_id,
                "full_response": stream_data.get("full_response", ""),
                "timestamp": time.time()
            }
            
        elif stream_type == "stream_error":
            # Handle streaming errors
            if conversation_id in self.streaming_sessions:
                self.streaming_sessions[conversation_id]["is_active"] = False
                self.streaming_sessions[conversation_id]["error"] = stream_data.get("error")
            
            message = {
                "type": "ai_stream_error",
                "conversation_id": conversation_id,
                "error": stream_data.get("error", "Unknown streaming error"),
                "timestamp": time.time()
            }
        
        else:
            return  # Unknown stream type
        
        # Send message to all clients in the conversation
        await self.manager.send_to_conversation(message, conversation_id)


# Global WebSocket manager instance
f3_websocket_manager = F3WebSocketManager()

__all__ = ['f3_websocket_manager', 'F3WebSocketManager', 'AIProgressStatus']
