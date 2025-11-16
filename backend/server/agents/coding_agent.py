"""
Coding Agent
============
This agent generates actual Flutter code based on execution plans.
Think of it as the "builder" that implements the architect's blueprint.

SERVER SIDE FILE
"""

from typing import Dict, Any, List, Optional
from ..models.message_models import (
    ExecutionPlan,
    ActionStep,
    CodeChange,
    CodeGenerationResult
)
from ..services.ai_service import ai_service
from ..utils.prompt_templates import (
    CODING_AGENT_SYSTEM,
    build_coding_prompt
)


class CodingAgent:
    """
    Generates Flutter code based on execution plans.
    
    This agent:
    - Executes steps from the planning agent
    - Generates clean, production-ready Flutter code
    - Creates and modifies files
    - Handles imports and dependencies
    """
    
    def __init__(self):
        """Initialize the Coding Agent."""
        self.name = "CodingAgent"
        print(f"  {self.name} initialized")
    
    async def _silent_callback(self, stream_data: Dict):
        """Silent callback for internal AI processing - doesn't send to users."""
        # Code generation can happen internally without user-visible streaming in some cases
        pass
    
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        project_context: Dict[str, Any],
        websocket_callback=None,
        conversation_id: Optional[str] = None
    ) -> CodeGenerationResult:
        """
        Execute an entire execution plan.
        
        Args:
            plan: The execution plan to implement
            project_context: Current project state
        
        Returns:
            CodeGenerationResult with all changes made
        """
        print(f"\n  [{self.name}] Executing plan: {plan.plan_id}")
        print(f"   Steps to execute: {len(plan.steps)}")
        
        all_changes = []
        warnings = []
        
        try:
            # Execute each step in sequence
            for i, step in enumerate(plan.steps, 1):
                print(f"   Executing step {i}/{len(plan.steps)}: {step.description}")
                
                result = await self.execute_step(
                    step, 
                    project_context, 
                    websocket_callback, 
                    conversation_id
                )
                
                if result.success:
                    all_changes.extend(result.changes)
                    if result.warnings:
                        warnings.extend(result.warnings)
                else:
                    # Stop execution on first failure
                    return CodeGenerationResult(
                        success=False,
                        changes=all_changes,
                        message=f"Failed at step {i}: {result.message}",
                        warnings=warnings
                    )
            
            # All steps completed successfully
            print(f"  [{self.name}] Plan executed successfully")
            return CodeGenerationResult(
                success=True,
                changes=all_changes,
                message=self._generate_success_message(all_changes),
                warnings=warnings if warnings else None
            )
        
        except Exception as e:
            print(f" [{self.name}] Plan execution failed: {str(e)}")
            return CodeGenerationResult(
                success=False,
                changes=all_changes,
                message=f"Execution error: {str(e)}",
                warnings=warnings
            )
    
    
    async def execute_step(
        self,
        step: ActionStep,
        project_context: Dict[str, Any],
        websocket_callback=None,
        conversation_id: Optional[str] = None
    ) -> CodeGenerationResult:
        """
        Execute a single step from the plan.
        
        Args:
            step: The step to execute
            project_context: Current project state
        
        Returns:
            CodeGenerationResult for this step
        """
        try:
            # Generate code for this step
            code = await self._generate_code_for_step(
                step, 
                project_context, 
                websocket_callback, 
                conversation_id
            )
            
            # Create a code change object
            change = CodeChange(
                file_path=step.target_file or "unknown",
                operation=self._get_operation_type(step.action_type),
                content=code,
                line_numbers=None  # Could be enhanced to track specific line changes
            )
            
            return CodeGenerationResult(
                success=True,
                changes=[change],
                message=f"✓ {step.action_type}: {step.target_file}",
                warnings=None
            )
        
        except Exception as e:
            print(f" [{self.name}] Step execution failed: {str(e)}")
            return CodeGenerationResult(
                success=False,
                changes=[],
                message=f"Failed: {str(e)}",
                warnings=[str(e)]
            )
    
    
    async def _generate_code_for_step(
        self,
        step: ActionStep,
        project_context: Dict[str, Any],
        websocket_callback=None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Generate the actual Dart code for a step.
        """
        # Build the prompt for code generation
        prompt = build_coding_prompt(
            step=step.__dict__,
            context=project_context
        )
        
        # Generate code using AI with streaming
        callback = websocket_callback if websocket_callback else self._silent_callback
        conv_id = conversation_id if conversation_id else "coding_internal"
        
        code = await ai_service.generate_response(
            prompt=prompt,
            system_instruction=CODING_AGENT_SYSTEM,
            temperature=0.5,  # Balanced creativity for code
            websocket_callback=callback,
            conversation_id=conv_id
        )
        
        # Clean up the code (remove markdown if present)
        code = self._clean_code(code)
        
        return code
    
    
    def _clean_code(self, code: str) -> str:
        """
        Clean up generated code (remove markdown, extra whitespace, etc.).
        """
        # Remove markdown code blocks
        if code.startswith("```dart"):
            code = code[7:]  # Remove ```dart
        elif code.startswith("```"):
            code = code[3:]   # Remove ```
        
        if code.endswith("```"):
            code = code[:-3]  # Remove trailing ```
        
        # Trim whitespace
        code = code.strip()
        
        return code
    
    
    def _get_operation_type(self, action_type: str) -> str:
        """
        Map action type to operation type.
        """
        mapping = {
            "create_file": "create",
            "modify_file": "update",
            "update_widget": "update",
            "add_import": "update",
            "delete_file": "delete"
        }
        return mapping.get(action_type, "update")
    
    
    def _generate_success_message(self, changes: List[CodeChange]) -> str:
        """
        Generate a brief success message for the user.
        
        This follows the CODE MODE rule: brief confirmations only!
        """
        if not changes:
            return "  No changes made"
        
        # Count operations
        created = sum(1 for c in changes if c.operation == "create")
        updated = sum(1 for c in changes if c.operation == "update")
        deleted = sum(1 for c in changes if c.operation == "delete")
        
        messages = []
        if created:
            messages.append(f" Created {created} file(s)")
        if updated:
            messages.append(f" Updated {updated} file(s)")
        if deleted:
            messages.append(f" Deleted {deleted} file(s)")
        
        # Also list specific files
        file_list = []
        for change in changes[:3]:  # Show first 3 files
            file_list.append(f"  • {change.file_path}")
        
        if len(changes) > 3:
            file_list.append(f"  • ... and {len(changes) - 3} more")
        
        return "\n".join(messages + file_list)
    
    
    async def generate_widget(
        self,
        widget_description: str,
        file_path: str,
        project_context: Dict[str, Any]
    ) -> CodeGenerationResult:
        """
        Generate a single Flutter widget.
        
        This is a convenience method for simple widget generation.
        """
        print(f"\n [{self.name}] Generating widget: {widget_description}")
        
        # Create a simple action step
        step = ActionStep(
            step_number=1,
            action_type="create_file",
            description=f"Create {widget_description}",
            target_file=file_path
        )
        
        return await self.execute_step(step, project_context)
    
    
    async def modify_widget(
        self,
        file_path: str,
        modification: str,
        current_code: str,
        project_context: Dict[str, Any]
    ) -> CodeGenerationResult:
        """
        Modify an existing Flutter widget.
        """
        print(f"\n [{self.name}] Modifying widget: {file_path}")
        
        # Create modification step
        step = ActionStep(
            step_number=1,
            action_type="modify_file",
            description=modification,
            target_file=file_path
        )
        
        return await self.execute_step(step, project_context)
    
    
    def validate_code(self, code: str) -> tuple[bool, List[str]]:
        """
        Basic validation of generated Dart code.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for basic Dart syntax requirements
        if not code.strip():
            issues.append("Code is empty")
        
        # Check for balanced braces
        open_braces = code.count("{")
        close_braces = code.count("}")
        if open_braces != close_braces:
            issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
        
        # Check for balanced parentheses
        open_parens = code.count("(")
        close_parens = code.count(")")
        if open_parens != close_parens:
            issues.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
        
        # Check for class or function definition
        if "class " not in code and "Widget " not in code:
            issues.append("No class or widget definition found")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            print(f" [{self.name}] Code validation failed:")
            for issue in issues:
                print(f"   - {issue}")
        
        return is_valid, issues
    
    
    def extract_imports(self, code: str) -> List[str]:
        """
        Extract import statements from Dart code.
        """
        imports = []
        for line in code.split("\n"):
            line = line.strip()
            if line.startswith("import "):
                imports.append(line)
        return imports
    
    
    def add_missing_imports(self, code: str, required_imports: List[str]) -> str:
        """
        Add missing import statements to code.
        """
        existing_imports = set(self.extract_imports(code))
        
        # Find imports that need to be added
        missing = [imp for imp in required_imports if imp not in existing_imports]
        
        if not missing:
            return code
        
        # Add missing imports at the top
        import_block = "\n".join(missing) + "\n\n"
        
        # Find where to insert (after existing imports or at start)
        if existing_imports:
            # Insert after last import
            lines = code.split("\n")
            last_import_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith("import "):
                    last_import_idx = i
            
            if last_import_idx >= 0:
                lines.insert(last_import_idx + 1, import_block)
                return "\n".join(lines)
        
        # No existing imports, add at start
        return import_block + code


# Create singleton instance
coding_agent = CodingAgent()


# Export
__all__ = ['CodingAgent', 'coding_agent']