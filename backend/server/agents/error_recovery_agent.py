"""
Error Recovery Agent
===================
This agent analyzes errors and attempts to fix them automatically.
Think of it as the "debugger" that tries to solve problems.

SERVER SIDE FILE
"""

from typing import Dict, Any, Optional, List
from ..models.message_models import (
    ErrorDetails,
    ErrorRecoveryResult,
    ErrorSeverity
)
from ..services.ai_service import ai_service
from ..utils.prompt_templates import (
    ERROR_RECOVERY_SYSTEM,
    build_error_analysis_prompt
)


class ErrorRecoveryAgent:
    """
    Analyzes errors and attempts automatic recovery.
    
    This agent:
    - Analyzes compilation and runtime errors
    - Determines if errors can be auto-fixed
    - Attempts fixes (max 3 retries)
    - Escalates to user when manual input needed
    """
    
    MAX_RETRY_ATTEMPTS = 3
    
    def __init__(self):
        """Initialize the Error Recovery Agent."""
        self.name = "ErrorRecoveryAgent"
        self.retry_tracker: Dict[str, int] = {}  # Track retry counts per error
        print(f" {self.name} initialized")
    
    async def _silent_callback(self, stream_data: Dict):
        """Silent callback for internal AI processing - doesn't send to users."""
        # Error analysis can happen internally without user-visible streaming
        pass
    
    async def analyze_error(
        self,
        error: ErrorDetails,
        code_context: str,
        retry_count: int = 0
    ) -> ErrorRecoveryResult:
        """
        Analyze an error and determine recovery strategy.
        
        Args:
            error: Details about the error
            code_context: The code that caused the error
            retry_count: How many times we've tried to fix this
        
        Returns:
            ErrorRecoveryResult with fix strategy
        """
        try:
            print(f"\n [{self.name}] Analyzing error: {error.error_type}")
            print(f"   Severity: {error.severity.value}")
            print(f"   Retry count: {retry_count}/{self.MAX_RETRY_ATTEMPTS}")
            
            # Build the analysis prompt
            prompt = build_error_analysis_prompt(
                error=error.__dict__,
                code=code_context,
                retry_count=retry_count
            )
            
            # Get analysis from AI using streaming
            analysis = await ai_service.generate_structured_response(
                prompt=prompt,
                system_instruction=ERROR_RECOVERY_SYSTEM,
                websocket_callback=self._silent_callback,
                conversation_id="error_recovery_internal",
                response_format="json"
            )
            
            # Parse the analysis
            result = self._parse_analysis(analysis, retry_count)
            
            # Log result
            if result.can_auto_fix:
                print(f" [{self.name}] Error can be auto-fixed")
            else:
                print(f" [{self.name}] Manual intervention required")
            
            return result
        
        except Exception as e:
            print(f" [{self.name}] Error analysis failed: {str(e)}")
            return self._create_fallback_result(str(e))
    
    
    def _parse_analysis(
        self,
        analysis: Dict[str, Any],
        retry_count: int
    ) -> ErrorRecoveryResult:
        """
        Parse AI analysis into ErrorRecoveryResult.
        """
        # Check if we've exceeded max retries
        can_auto_fix = analysis.get("can_auto_fix", False)
        if retry_count >= self.MAX_RETRY_ATTEMPTS:
            can_auto_fix = False
            print(f" [{self.name}] Max retries reached, escalating to user")
        
        return ErrorRecoveryResult(
            can_auto_fix=can_auto_fix,
            attempted_fix=False,  # Will be set to True after fix attempt
            success=False,        # Will be updated after fix is applied
            fixed_code=analysis.get("suggested_fix"),
            explanation=analysis.get("explanation"),
            suggested_actions=analysis.get("user_questions"),
            retry_count=retry_count
        )
    
    
    def _create_fallback_result(self, error_msg: str) -> ErrorRecoveryResult:
        """
        Create a fallback result when analysis fails.
        """
        return ErrorRecoveryResult(
            can_auto_fix=False,
            attempted_fix=False,
            success=False,
            fixed_code=None,
            explanation=f"Error analysis failed: {error_msg}",
            suggested_actions=["Please review the error manually"],
            retry_count=0
        )
    
    
    async def attempt_fix(
        self,
        error: ErrorDetails,
        code_context: str,
        recovery_result: ErrorRecoveryResult
    ) -> ErrorRecoveryResult:
        """
        Attempt to apply an automatic fix.
        
        Args:
            error: The error to fix
            code_context: Current code
            recovery_result: The analysis result with suggested fix
        
        Returns:
            Updated ErrorRecoveryResult with fix status
        """
        if not recovery_result.can_auto_fix:
            print(f" [{self.name}] Cannot auto-fix, skipping attempt")
            return recovery_result
        
        if not recovery_result.fixed_code:
            print(f" [{self.name}] No fix code provided")
            recovery_result.can_auto_fix = False
            return recovery_result
        
        try:
            print(f"\n🔧 [{self.name}] Attempting auto-fix...")
            
            # Update the result to indicate fix was attempted
            recovery_result.attempted_fix = True
            
            # In a real implementation, you would:
            # 1. Apply the fixed code
            # 2. Try to compile/validate it
            # 3. Check if the error is resolved
            
            # For now, we'll assume the fix needs to be validated by caller
            print(f" [{self.name}] Fix generated, needs validation")
            
            return recovery_result
        
        except Exception as e:
            print(f" [{self.name}] Fix attempt failed: {str(e)}")
            recovery_result.success = False
            recovery_result.explanation = f"Fix failed: {str(e)}"
            return recovery_result
    
    
    def track_retry(self, error_id: str) -> int:
        """
        Track retry attempts for an error.
        
        Args:
            error_id: Unique identifier for the error
        
        Returns:
            Current retry count
        """
        if error_id not in self.retry_tracker:
            self.retry_tracker[error_id] = 0
        
        self.retry_tracker[error_id] += 1
        return self.retry_tracker[error_id]
    
    
    def reset_retry(self, error_id: str):
        """
        Reset retry count for an error (when successfully fixed).
        """
        if error_id in self.retry_tracker:
            del self.retry_tracker[error_id]
            print(f" [{self.name}] Reset retry count for {error_id}")
    
    
    def should_escalate(self, error: ErrorDetails, retry_count: int) -> bool:
        """
        Determine if error should be escalated to user.
        
        Returns True if:
        - Retry count >= MAX_RETRY_ATTEMPTS
        - Error severity is HIGH
        - Error type requires user input
        """
        if retry_count >= self.MAX_RETRY_ATTEMPTS:
            return True
        
        if error.severity == ErrorSeverity.HIGH:
            return True
        
        # Check for error types that typically need user input
        needs_input_types = ["validation", "ambiguous", "configuration"]
        if error.error_type in needs_input_types:
            return True
        
        return False
    
    
    async def generate_user_message(
        self,
        error: ErrorDetails,
        recovery_result: ErrorRecoveryResult
    ) -> str:
        """
        Generate a user-friendly error message for Chat Mode.
        
        This is shown when we need user input to resolve the error.
        """
        message_parts = [
            " **Error Occurred**\n",
            f"**Type:** {error.error_type.capitalize()}\n",
            f"**Message:** {error.message}\n"
        ]
        
        if error.file_path:
            message_parts.append(f"**File:** {error.file_path}\n")
        
        if error.line_number:
            message_parts.append(f"**Line:** {error.line_number}\n")
        
        if recovery_result.explanation:
            message_parts.append(f"\n**What went wrong:**\n{recovery_result.explanation}\n")
        
        if recovery_result.suggested_actions:
            message_parts.append("\n**How to fix it:**")
            for i, action in enumerate(recovery_result.suggested_actions, 1):
                message_parts.append(f"{i}. {action}")
        
        return "\n".join(message_parts)
    
    
    def categorize_error(self, error_message: str) -> tuple[str, ErrorSeverity]:
        """
        Categorize an error based on its message.
        
        Returns:
            (error_type, severity)
        """
        error_lower = error_message.lower()
        
        # Syntax errors (usually low severity, easy to fix)
        if any(keyword in error_lower for keyword in ["syntax error", "unexpected token", "missing ';'"]):
            return "syntax", ErrorSeverity.LOW
        
        # Compile errors (medium severity)
        if any(keyword in error_lower for keyword in ["undefined name", "type mismatch", "cannot find"]):
            return "compile", ErrorSeverity.MEDIUM
        
        # Runtime errors (medium to high severity)
        if any(keyword in error_lower for keyword in ["null", "exception", "error at runtime"]):
            return "runtime", ErrorSeverity.MEDIUM
        
        # Validation errors (medium severity)
        if any(keyword in error_lower for keyword in ["constraint", "overflow", "invalid"]):
            return "validation", ErrorSeverity.MEDIUM
        
        # Default to medium severity
        return "unknown", ErrorSeverity.MEDIUM
    
    
    def create_error_details(
        self,
        error_message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        stack_trace: Optional[str] = None,
        code_context: Optional[str] = None
    ) -> ErrorDetails:
        """
        Create an ErrorDetails object from error information.
        
        Helper method to construct ErrorDetails from various sources.
        """
        error_type, severity = self.categorize_error(error_message)
        
        return ErrorDetails(
            error_type=error_type,
            severity=severity,
            message=error_message,
            file_path=file_path,
            line_number=line_number,
            stack_trace=stack_trace,
            context=code_context
        )
    
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about retry attempts.
        
        Useful for monitoring and debugging.
        """
        return {
            "total_tracked_errors": len(self.retry_tracker),
            "errors_at_max_retries": sum(
                1 for count in self.retry_tracker.values() 
                if count >= self.MAX_RETRY_ATTEMPTS
            ),
            "average_retries": (
                sum(self.retry_tracker.values()) / len(self.retry_tracker)
                if self.retry_tracker else 0
            )
        }
    
    
    def clear_old_retries(self, max_age_minutes: int = 60):
        """
        Clear retry tracking for old errors.
        
        This prevents memory buildup from tracking errors indefinitely.
        In production, you'd use timestamps to track age.
        """
        # Simple implementation - clear all if too many tracked
        if len(self.retry_tracker) > 100:
            print(f"🧹 [{self.name}] Clearing old retry tracking data")
            self.retry_tracker.clear()


# Create singleton instance
error_recovery_agent = ErrorRecoveryAgent()


# Export
__all__ = ['ErrorRecoveryAgent', 'error_recovery_agent']