"""
Data Models for F3 Platform

This file defines all the data structures (models) used throughout the application.
Think of these as blueprints that define what data looks like.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
# Simple validation function to avoid circular import
def validate_confidence(value: float, field_name: str = "confidence") -> float:
    """Validate confidence value is between 0.0 and 1.0"""
    return max(0.0, min(1.0, value))


class MessageRole(str, Enum):
    """
    Defines who sent the message.
    Enum = A fixed set of options (like a dropdown menu in code)
    """
    USER = "user"           # Message from the user
    ASSISTANT = "assistant" # Message from AI
    SYSTEM = "system"       # Internal system messages


class IntentType(str, Enum):
    """
    Defines what the user wants to do.
    This helps route the message to the right agent.
    """
    CHAT = "chat"                    # User wants to chat/ask questions
    CODE = "code"                    # User wants to generate/modify code
    EXPLAIN = "explain"              # User wants explanation
    ERROR_CLARIFICATION = "error"    # User responding to error


class ModeType(str, Enum):
    """
    Defines which mode the system is currently in.
    """
    CHAT_MODE = "chat"  # Conversational mode
    CODE_MODE = "code"  # Code generation mode


class ErrorSeverity(str, Enum):
    """
    How serious is the error?
    """
    LOW = "low"         # Minor issue, easy to fix
    MEDIUM = "medium"   # Needs attention
    HIGH = "high"       # Critical, needs user input


# ============================================================================
# MESSAGE MODELS
# ============================================================================

@dataclass
class Message:
    """
    Represents a single message in the conversation.
    Dataclass for structured data with automatic validation
    """
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'role': self.role.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class UserMessage:
    """
    Message sent from the frontend (user).
    This is what the API endpoint receives.
    """
    content: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # Additional info like file names


@dataclass
class AssistantResponse:
    """
    Response sent back to the frontend.
    This is what the API endpoint returns.
    """
    content: str
    mode: ModeType
    intent: IntentType
    conversation_id: str
    metadata: Optional[Dict[str, Any]] = None
    files_modified: Optional[List[str]] = None  # List of files changed (in code mode)
    error: Optional[str] = None


# ============================================================================
# INTENT CLASSIFICATION MODELS................................................
# ============================================================================

@dataclass
class IntentClassification:
    """
    Result from the Intent Classifier Agent.
    Tells us what the user wants to do.
    """
    intent: IntentType
    confidence: float  # 0.0 to 1.0 (0% to 100%)
    suggested_mode: ModeType
    reasoning: Optional[str] = None
    
    def __post_init__(self):
        """Validate fields after initialization."""
        self.confidence = validate_confidence(self.confidence, "confidence")


# ============================================================================
# PLANNING MODELS.................................................................
# ============================================================================

@dataclass
class ActionStep:
    """
    A single step in the execution plan.
    """
    step_number: int
    action_type: str  # e.g., "create_file", "modify_widget", "add_import"
    description: str
    target_file: Optional[str] = None


@dataclass
class ExecutionPlan:
    """
    The complete plan created by the Planning Agent.
    """
    plan_id: str
    steps: List[ActionStep]
    estimated_files: List[str]  # Files that will be created/modified
    dependencies: Optional[List[str]] = None  # Required packages/imports
    notes: Optional[str] = None


# ============================================================================
# CODE GENERATION MODELS........................................................
# ============================================================================

@dataclass
class CodeChange:
    """
    Represents a change made to code.
    """
    file_path: str
    operation: str  # "create", "update", "delete"
    content: str
    line_numbers: Optional[Dict[str, int]] = None  # {"start": 10, "end": 25}


@dataclass
class CodeGenerationResult:
    """
    Result from the Coding Agent.
    """
    success: bool
    changes: List[CodeChange]
    message: str  # Brief confirmation message
    warnings: Optional[List[str]] = None


# ============================================================================
# ERROR HANDLING MODELS.........................................................
# ============================================================================

@dataclass
class ErrorDetails:
    """
    Details about an error that occurred.
    """
    error_type: str  # "compile", "runtime", "syntax", "validation"
    severity: ErrorSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    context: Optional[str] = None  # Surrounding code


@dataclass
class ErrorRecoveryResult:
    """
    Result from the Error Recovery Agent.
    """
    can_auto_fix: bool
    attempted_fix: bool
    success: bool
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None  # Explanation for user (if manual fix needed)
    suggested_actions: Optional[List[str]] = None
    retry_count: int = 0


# ============================================================================
# COORDINATOR STATE MODELS...................................................................
# ============================================================================

@dataclass
class ConversationState:
    """
    Maintains the current state of the conversation.
    This is like the "memory" of the system.
    """
    conversation_id: str
    current_mode: ModeType
    message_history: List[Message]
    project_files: Dict[str, str] = field(default_factory=dict)  # {file_path: content}
    error_history: List[ErrorDetails] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)  # Track retry attempts per error
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinatorState:
    """
    Overall state managed by the Agent Coordinator.
    """
    active_conversations: Dict[str, ConversationState] = field(default_factory=dict)
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get a specific conversation's state."""
        return self.active_conversations.get(conversation_id)
    
    def create_conversation(self, conversation_id: str) -> ConversationState:
        """Create a new conversation."""
        state = ConversationState(
            conversation_id=conversation_id,
            current_mode=ModeType.CHAT_MODE,
            message_history=[],
        )
        self.active_conversations[conversation_id] = state
        return state


# ============================================================================
# API REQUEST/RESPONSE MODELS.......................................
# ============================================================================

@dataclass
class ChatRequest:
    """
    Request model for the main chat endpoint.
    This is what your frontend will send to the API.
    """
    message: str
    conversation_id: Optional[str] = None
    project_context: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """
    Response model for the main chat endpoint.
    This is what your frontend will receive from the API.
    """
    message: str
    conversation_id: str
    mode: ModeType
    files_changed: Optional[List[str]] = None
    preview_update_required: bool = False
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None