"""
Agent Coordinator
=================
This is the master orchestrator that manages all agents and workflow.
Think of it as the "conductor" of an orchestra, coordinating all the agents.

SERVER SIDE FILE - This is the heart of the system!
"""

from typing import Dict, Any, Optional, List
import uuid
from ..models.message_models import (
    Message,
    MessageRole,
    IntentType,
    ModeType,
    ConversationState,
    CoordinatorState,
    AssistantResponse
)
from ..agents.intent_classifier_agent import intent_classifier_agent
from ..agents.planning_agent import planning_agent
from ..agents.coding_agent import coding_agent
from ..agents.error_recovery_agent import error_recovery_agent
from ..agents.chat_agent import chat_agent

# Import WebSocket service for streaming
try:
    from ..services.websocket_service import f3_websocket_manager
    WEBSOCKET_AVAILABLE = True
except ImportError:
    f3_websocket_manager = None
    WEBSOCKET_AVAILABLE = False
    print(" WebSocket service not available - progress updates disabled")

# Import AIService separately to ensure it is always available
from ..services.ai_service import AIService

# Import project service for file management
try:
    from ..projects.project_service import project_service
    PROJECT_SERVICE_AVAILABLE = True
except ImportError:
    project_service = None
    PROJECT_SERVICE_AVAILABLE = False
    print(" Project service not available - file saving disabled")


class AgentCoordinator:
    """
    Master coordinator that orchestrates all agents and manages workflow.
    
    This coordinator:
    - Maintains conversation state
    - Routes messages to appropriate agents
    - Manages mode switching (Chat/Code)
    - Handles error recovery workflow
    - Coordinates multi-agent operations
    """
    
    def __init__(self):
        """Initialize the Agent Coordinator."""
        self.name = "AgentCoordinator"
        self.state = CoordinatorState()
        self.project_service_enabled = PROJECT_SERVICE_AVAILABLE
        
        # Initialize AI service for streaming (required)
        if not WEBSOCKET_AVAILABLE:
            raise Exception("WebSocket service is required for streaming-only mode")
        
        self.ai_service = AIService()
        
        print(f" {self.name} initialized")
        print(f"   Managing agents: Intent, Planning, Coding, Error Recovery, Chat")
        print(f"   Streaming mode:  Enabled (streaming-only)")
        print(f"   Project file saving: {'Enabled' if self.project_service_enabled else '❌ Disabled'}")
    
    async def _send_progress_update(self, conversation_id: str, status: str, message: str = "", files_created: Optional[List[str]] = None, error_message: Optional[str] = None, user_prompt: str = ""):
        # Pass user prompt to all phases for contextual AI generation
        if not WEBSOCKET_AVAILABLE or f3_websocket_manager is None:
            return
        # Ensure files_created is a list if None was passed
        files_list = files_created or []
        if status == "coding":
            await f3_websocket_manager.send_progress_update(conversation_id, status, message, files_list, error_message, user_prompt)
        elif status == "complete":
            await f3_websocket_manager.send_ai_complete(conversation_id, files_list, user_prompt)
        else:
            await f3_websocket_manager.send_progress_update(conversation_id, status, message, files_list, error_message, user_prompt)
    
    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> AssistantResponse:
        """
        Process a user message through the entire workflow.
        
        This is the main entry point for all user interactions.
        
        Args:
            message: The user's message
            conversation_id: Unique ID for this conversation
            project_context: Current project state (files, widgets, etc.)
        
        Returns:
            AssistantResponse with the result
        """
        try:
            print(f"\n{'='*70}")
            print(f" [{self.name}] Processing new message")
            print(f"{'='*70}")
            
            # Get or create conversation state
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            conv_state = self._get_or_create_conversation(conversation_id)
            
            # Update project context if provided
            if project_context:
                conv_state.context.update(project_context)
            
            # Add user message to history
            user_message = Message(
                role=MessageRole.USER,
                content=message
            )
            conv_state.message_history.append(user_message)
            
            # Send initial progress update with user prompt
            await self._send_progress_update(conversation_id, "analyzing", message, user_prompt=message)
            
            # STEP 1: Classify intent
            print(f"\n STEP 1: Intent Classification")
            classification = await intent_classifier_agent.classify(
                message=message,
                conversation_history=conv_state.message_history,
                current_mode=conv_state.current_mode
            )
            
            # STEP 2: Determine if mode switch is needed
            print(f"\n STEP 2: Mode Management")
            should_switch = intent_classifier_agent.should_switch_mode(
                classification=classification,
                current_mode=conv_state.current_mode
            )
            
            if should_switch:
                old_mode = conv_state.current_mode
                conv_state.current_mode = classification.suggested_mode
                print(f"   Mode switched: {old_mode.value} → {conv_state.current_mode.value}")
            
            # STEP 3: Route to appropriate workflow
            print(f"\n STEP 3: Workflow Routing")
            print(f"   Intent: {classification.intent.value}")
            print(f"   Mode: {conv_state.current_mode.value}")
            
            if conv_state.current_mode == ModeType.CODE_MODE:
                response = await self._handle_code_mode(
                    message=message,
                    conv_state=conv_state,
                    intent=classification.intent
                )
            else:  # CHAT_MODE
                response = await self._handle_chat_mode(
                    message=message,
                    conv_state=conv_state,
                    intent=classification.intent
                )
            
            # Add assistant response to history
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=response.content
            )
            conv_state.message_history.append(assistant_message)
            
            # Update state
            self.state.active_conversations[conversation_id] = conv_state
            
            print(f"\n [{self.name}] Message processed successfully")
            print(f"{'='*70}\n")
            
            return response
        
        except Exception as e:
            print(f"\n [{self.name}] Error processing message: {str(e)}")
            return AssistantResponse(
                content=f"I encountered an error: {str(e)}. Please try again.",
                mode=ModeType.CHAT_MODE,
                intent=IntentType.CHAT,
                conversation_id=conversation_id or str(uuid.uuid4()),
                error=str(e)
            )
    
    
    async def _handle_code_mode(
        self,
        message: str,
        conv_state: ConversationState,
        intent: IntentType
    ) -> AssistantResponse:
        """
        Handle Code Mode workflow.
        
        Workflow:
        1. Planning Agent creates execution plan
        2. Coding Agent executes the plan
        3. Compile & validate
        4. If error → Error Recovery Agent
        5. Return brief confirmation
        """
        print(f"\n CODE MODE WORKFLOW")
        
        try:
            # Check if this is an error clarification
            if intent == IntentType.ERROR_CLARIFICATION:
                return await self._handle_error_clarification(message, conv_state)
            
            # Check if user wants explanation (switch to chat mode)
            if intent == IntentType.EXPLAIN:
                conv_state.current_mode = ModeType.CHAT_MODE
                return await self._handle_chat_mode(message, conv_state, intent)
            
            # Send planning progress update
            await self._send_progress_update(conv_state.conversation_id, "planning", user_prompt=message)
            
            # STEP 1: Create execution plan
            print(f"\n   Step 1: Planning")
            try:
                plan = await planning_agent.create_plan(
                    user_request=message,
                    project_context=conv_state.context,
                    websocket_callback=f3_websocket_manager.streaming_callback if f3_websocket_manager else None,
                    conversation_id=conv_state.conversation_id
                )
                
                # Validate plan
                is_valid, issues = planning_agent.validate_plan(plan)
                if not is_valid:
                    return AssistantResponse(
                        content=f" Planning issue: {', '.join(issues)}",
                        mode=ModeType.CODE_MODE,
                        intent=IntentType.CODE,
                        conversation_id=conv_state.conversation_id
                    )
                    
            except Exception as e:
                print(f" Planning failed: {str(e)}")
                return AssistantResponse(
                    content=f" Planning failed: {str(e)}. Please try rephrasing your request.",
                    mode=ModeType.CODE_MODE,
                    intent=IntentType.CODE,
                    conversation_id=conv_state.conversation_id
                )
            
            # Send coding progress update
            files_created = []
            await self._send_progress_update(conv_state.conversation_id, "coding", files_created=files_created, user_prompt=message)
            
            # STEP 2: Execute plan
            print(f"\n   Step 2: Code Generation")
            try:
                result = await coding_agent.execute_plan(
                    plan=plan,
                    project_context=conv_state.context,
                    websocket_callback=f3_websocket_manager.streaming_callback if f3_websocket_manager else None,
                    conversation_id=conv_state.conversation_id
                )
            except Exception as e:
                print(f" Code generation failed: {str(e)}")
                return AssistantResponse(
                    content=f" Code generation failed: {str(e)}. Please try a simpler request.",
                    mode=ModeType.CODE_MODE,
                    intent=IntentType.CODE,
                    conversation_id=conv_state.conversation_id
                )
            
            if result.success:
                # Send validation progress update
                await self._send_progress_update(conv_state.conversation_id, "validating")
                
                # STEP 3: Update project state and save files
                for change in result.changes:
                    if change.operation == "create" or change.operation == "update":
                        conv_state.project_files[change.file_path] = change.content
                
                # STEP 4: Save generated files to project (if project context provided)
                files_created = [c.file_path for c in result.changes]
                if self.project_service_enabled and conv_state.context.get("project_id"):
                    await self._save_files_to_project(
                        project_id=conv_state.context["project_id"],
                        files=result.changes,
                        conversation_id=conv_state.conversation_id
                    )
                
                # Send completion progress update
                await self._send_progress_update(
                    conv_state.conversation_id, 
                    "complete", 
                    files_created=files_created,
                    user_prompt=message
                )
                
                # Return brief confirmation (CODE MODE rule!)
                return AssistantResponse(
                    content=result.message,
                    mode=ModeType.CODE_MODE,
                    intent=IntentType.CODE,
                    conversation_id=conv_state.conversation_id,
                    files_modified=files_created,
                    metadata={"plan_id": plan.plan_id, "project_id": conv_state.context.get("project_id")}
                )
            else:
                # Send error progress update
                await self._send_progress_update(
                    conv_state.conversation_id, 
                    "error", 
                    error_message=result.message
                )
                
                # STEP 4: Error occurred, attempt recovery
                return await self._handle_code_error(
                    error_message=result.message,
                    conv_state=conv_state,
                    plan=plan
                )
        
        except Exception as e:
            print(f" Code mode error: {str(e)}")
            return AssistantResponse(
                content=f" Code generation failed: {str(e)}",
                mode=ModeType.CODE_MODE,
                intent=IntentType.CODE,
                conversation_id=conv_state.conversation_id,
                error=str(e)
            )
    
    
    async def _handle_chat_mode(
        self,
        message: str,
        conv_state: ConversationState,
        intent: IntentType
    ) -> AssistantResponse:
        """
        Handle Chat Mode workflow.
        
        Workflow:
        1. Chat Agent generates conversational response
        2. Return full explanation (no code!)
        """
        print(f"\n CHAT MODE WORKFLOW")
        
        try:
            # Check if user wants to generate code (switch to code mode)
            if intent == IntentType.CODE:
                conv_state.current_mode = ModeType.CODE_MODE
                return await self._handle_code_mode(message, conv_state, intent)
            
            # Generate streaming chat response
            response_text = await self.ai_service.generate_response(
                prompt=message,
                system_instruction="You are a helpful Flutter development assistant. Provide clear, conversational responses about Flutter development, UI design, and mobile app creation. Be friendly and encouraging.",
                context=[{"role": msg.role.value, "content": msg.content} for msg in conv_state.message_history[-5:]],  # Last 5 messages for context
                websocket_callback=f3_websocket_manager.streaming_callback if f3_websocket_manager else None,
                conversation_id=conv_state.conversation_id
            )
            
            # Check if we should suggest code mode
            if chat_agent.should_suggest_code_mode(message):
                response_text = chat_agent.format_response(
                    content=response_text,
                    add_code_mode_suggestion=True
                )
            
            return AssistantResponse(
                content=response_text,
                mode=ModeType.CHAT_MODE,
                intent=IntentType.CHAT,
                conversation_id=conv_state.conversation_id
            )
        
        except Exception as e:
            print(f" Chat mode error: {str(e)}")
            return AssistantResponse(
                content=chat_agent._generate_error_response(str(e)),
                mode=ModeType.CHAT_MODE,
                intent=IntentType.CHAT,
                conversation_id=conv_state.conversation_id,
                error=str(e)
            )
    
    
    async def _handle_code_error(
        self,
        error_message: str,
        conv_state: ConversationState,
        plan: Any
    ) -> AssistantResponse:
        """
        Handle errors that occur during code generation.
        
        Workflow:
        1. Create ErrorDetails
        2. Error Recovery Agent analyzes
        3. If can auto-fix → retry (max 3 times)
        4. If needs user input → switch to Chat Mode
        """
        print(f"\n ERROR RECOVERY WORKFLOW")
        
        # Create error details
        error = error_recovery_agent.create_error_details(
            error_message=error_message
        )
        
        # Track retry count
        error_id = f"{plan.plan_id}_error"
        retry_count = error_recovery_agent.track_retry(error_id)
        
        # Analyze error
        recovery_result = await error_recovery_agent.analyze_error(
            error=error,
            code_context=str(plan),  # In real app, get actual code
            retry_count=retry_count
        )
        
        if recovery_result.can_auto_fix and retry_count < error_recovery_agent.MAX_RETRY_ATTEMPTS:
            # Attempt auto-fix
            print(f"   Attempting auto-fix (attempt {retry_count})")
            
            # In real implementation, you would:
            # 1. Apply the fix
            # 2. Re-run coding agent
            # 3. Check if error is resolved
            
            # For now, return a message about the fix attempt
            return AssistantResponse(
                content=f" Attempting to fix error (attempt {retry_count}/3)...\n{recovery_result.explanation}",
                mode=ModeType.CODE_MODE,
                intent=IntentType.CODE,
                conversation_id=conv_state.conversation_id,
                metadata={"recovery_attempt": retry_count}
            )
        else:
            # Switch to Chat Mode and ask user
            print(f"   Escalating to user (Chat Mode)")
            conv_state.current_mode = ModeType.CHAT_MODE
            
            # Generate user-friendly error message
            error_msg = await error_recovery_agent.generate_user_message(
                error=error,
                recovery_result=recovery_result
            )
            
            # Add explanation
            if recovery_result.explanation:
                explanation = chat_agent.handle_error_explanation(
                    error_message=error_message,
                    error_context=recovery_result.explanation
                )
                error_msg += f"\n\n{explanation}"
            
            return AssistantResponse(
                content=error_msg,
                mode=ModeType.CHAT_MODE,
                intent=IntentType.ERROR_CLARIFICATION,
                conversation_id=conv_state.conversation_id,
                metadata={"needs_clarification": True}
            )
    
    
    async def _handle_error_clarification(
        self,
        message: str,
        conv_state: ConversationState
    ) -> AssistantResponse:
        """
        Handle user's response to an error.
        
        User provides clarification, we go back to Planning Agent.
        """
        print(f"\n ERROR CLARIFICATION WORKFLOW")
        
        # Extract error context from conversation
        # In real app, you'd track which error is being addressed
        
        # Create new plan based on clarification
        plan = await planning_agent.create_plan(
            user_request=message,
            project_context=conv_state.context,
            websocket_callback=f3_websocket_manager.streaming_callback if f3_websocket_manager else None,
            conversation_id=conv_state.conversation_id
        )

        # Execute the refined plan
        result = await coding_agent.execute_plan(
            plan=plan,
            project_context=conv_state.context,
            websocket_callback=f3_websocket_manager.streaming_callback if f3_websocket_manager else None,
            conversation_id=conv_state.conversation_id
        )
        
        if result.success:
            return AssistantResponse(
                content=f" Fixed!\n{result.message}",
                mode=ModeType.CODE_MODE,
                intent=IntentType.CODE,
                conversation_id=conv_state.conversation_id,
                files_modified=[c.file_path for c in result.changes]
            )
        else:
            # Still has errors, try recovery again
            return await self._handle_code_error(
                error_message=result.message,
                conv_state=conv_state,
                plan=plan
            )
    
    
    def _get_or_create_conversation(self, conversation_id: str) -> ConversationState:
        """
        Get existing conversation or create new one.
        """
        if conversation_id in self.state.active_conversations:
            print(f"    Retrieved existing conversation: {conversation_id}")
            return self.state.active_conversations[conversation_id]
        
        print(f"    Created new conversation: {conversation_id}")
        return self.state.create_conversation(conversation_id)
    
    
    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get statistics about a conversation.
        """
        conv_state = self.state.get_conversation(conversation_id)
        if not conv_state:
            return {"error": "Conversation not found"}
        
        return {
            "message_count": len(conv_state.message_history),
            "current_mode": conv_state.current_mode.value,
            "files_count": len(conv_state.project_files),
            "error_count": len(conv_state.error_history)
        }
    
    
    async def _save_files_to_project(
        self,
        project_id: str,
        files: List[Any],
        conversation_id: str
    ):
        """
        Save generated files to project using project service.
        """
        try:
            print(f"\n [{self.name}] Saving {len(files)} files to project {project_id}")
            
            # Convert CodeChange objects to file format expected by project service
            file_list = []
            for change in files:
                if hasattr(change, 'file_path') and hasattr(change, 'content'):
                    file_list.append({
                        "file_path": change.file_path,
                        "content": change.content,
                        "operation": getattr(change, 'operation', 'create')
                    })
            
            # Save files using project service
            if project_service:
                result = await project_service.save_generated_files(
                    project_id=project_id,
                    files=file_list,
                    conversation_id=conversation_id
                )
                if result["success"]:
                    print(f" [{self.name}] Saved {result['total_saved']} files to project")
                    if result["total_failed"] > 0:
                        print(f" [{self.name}] Failed to save {result['total_failed']} files")
                else:
                    print(f" [{self.name}] Failed to save files to project: {result.get('error', 'Unknown error')}")
            else:
                print(f" [{self.name}] Project service is not available. Cannot save files.")
                
        except Exception as e:
            print(f" [{self.name}] Error saving files to project: {str(e)}")
    
    def clear_conversation(self, conversation_id: str):
        """
        Clear a conversation from memory.
        """
        if conversation_id in self.state.active_conversations:
            del self.state.active_conversations[conversation_id]
            print(f" [{self.name}] Cleared conversation: {conversation_id}")
    
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get overall system statistics.
        """
        return {
            "active_conversations": len(self.state.active_conversations),
            "total_messages": sum(
                len(conv.message_history) 
                for conv in self.state.active_conversations.values()
            ),
            "error_recovery_stats": error_recovery_agent.get_retry_stats()
        }


# Create singleton instance
agent_coordinator = AgentCoordinator()


# Export
__all__ = ['AgentCoordinator', 'agent_coordinator']