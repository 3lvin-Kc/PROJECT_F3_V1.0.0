"""
Planning Agent
==============
This agent creates detailed execution plans for code generation.
Think of it as an "architect" that designs the blueprint before building.

SERVER SIDE FILE
"""

from typing import Dict, Any, Optional, List
import uuid
from ..models.message_models import ExecutionPlan, ActionStep
from ..services.ai_service import ai_service
from ..utils.prompt_templates import (
    PLANNING_AGENT_SYSTEM,
    build_planning_prompt
)


class PlanningAgent:
    """
    Creates detailed execution plans for Flutter widget generation.
    
    This agent:
    - Analyzes user requests
    - Breaks them down into actionable steps
    - Determines which files need to be created/modified
    - Identifies required dependencies
    """
    
    def __init__(self):
        """Initialize the Planning Agent."""
        self.name = "PlanningAgent"
        print(f"✅ {self.name} initialized")
    
    async def _silent_callback(self, stream_data: Dict):
        """Silent callback for internal AI processing - doesn't send to users."""
        # Planning can happen internally without user-visible streaming in some cases
        pass
    
    
    async def create_plan(
        self,
        user_request: str,
        project_context: Dict[str, Any],
        websocket_callback=None,
        conversation_id: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Create a detailed execution plan for a user request.
        
        Args:
            user_request: What the user wants to build/modify
            project_context: Current state of the project (files, widgets, etc.)
        
        Returns:
            ExecutionPlan with steps, files, and dependencies
        
        Example:
            plan = await planner.create_plan(
                "Create a blue rounded button with icon",
                {"files": {...}, "current_widget": "home_page"}
            )
        """
        try:
            print(f"\n📋 [{self.name}] Creating plan for: '{user_request[:50]}...'")
            
            # Build the prompt
            prompt = build_planning_prompt(user_request, project_context)
            
            # Get plan from AI using streaming
            if websocket_callback and conversation_id:
                plan_data = await ai_service.generate_structured_response(
                    prompt=prompt,
                    system_instruction=PLANNING_AGENT_SYSTEM,
                    websocket_callback=websocket_callback,
                    conversation_id=conversation_id,
                    response_format="json"
                )
            else:
                # Fallback for internal use without streaming
                plan_data = await ai_service.generate_structured_response(
                    prompt=prompt,
                    system_instruction=PLANNING_AGENT_SYSTEM,
                    websocket_callback=self._silent_callback,
                    conversation_id="planning_internal",
                    response_format="json"
                )
            
            # Parse and validate the plan
            execution_plan = self._parse_plan(plan_data)
            
            print(f"✅ [{self.name}] Created plan with {len(execution_plan.steps)} steps")
            print(f"   Files to modify: {len(execution_plan.estimated_files)}")
            
            return execution_plan
        
        except Exception as e:
            print(f"❌ [{self.name}] Error creating plan: {str(e)}")
            # Return a minimal fallback plan
            return self._create_fallback_plan(user_request, str(e))
    
    
    def _parse_plan(self, plan_data: Dict[str, Any]) -> ExecutionPlan:
        """
        Parse AI response into an ExecutionPlan object.
        """
        try:
            # Generate unique plan ID if not provided
            plan_id = plan_data.get("plan_id", str(uuid.uuid4()))
            
            # Parse steps
            steps = []
            for step_data in plan_data.get("steps", []):
                step = ActionStep(
                    step_number=step_data.get("step_number", len(steps) + 1),
                    action_type=step_data.get("action_type", "unknown"),
                    description=step_data.get("description", "No description"),
                    target_file=step_data.get("target_file"),

                )
                steps.append(step)
            
            # Create execution plan
            return ExecutionPlan(
                plan_id=plan_id,
                steps=steps,
                estimated_files=plan_data.get("estimated_files", []),
                dependencies=plan_data.get("dependencies"),
                notes=plan_data.get("notes")
            )
        
        except Exception as e:
            print(f"⚠️ [{self.name}] Error parsing plan: {str(e)}")
            raise
    
    
    def _create_fallback_plan(self, request: str, error: str) -> ExecutionPlan:
        """
        Create a minimal fallback plan when AI planning fails.
        """
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            steps=[
                ActionStep(
                    step_number=1,
                    action_type="error",
                    description=f"Failed to create plan: {error}",
                    target_file=None,

                )
            ],
            estimated_files=[],
            dependencies=None,
            notes=f"Planning failed for request: {request}"
        )
    
    
    def validate_plan(self, plan: ExecutionPlan) -> tuple[bool, List[str]]:
        """
        Validate an execution plan for completeness and correctness.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if plan has steps
        if not plan.steps:
            issues.append("Plan has no steps")
        
        # Check each step
        for step in plan.steps:
            if not step.description:
                issues.append(f"Step {step.step_number} has no description")
            
            if not step.action_type:
                issues.append(f"Step {step.step_number} has no action type")
            
            # If action involves files, check target_file is specified
            if step.action_type in ["create_file", "modify_file", "update_widget"]:
                if not step.target_file:
                    issues.append(f"Step {step.step_number} needs a target file")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            print(f"⚠️ [{self.name}] Plan validation failed:")
            for issue in issues:
                print(f"   - {issue}")
        
        return is_valid, issues
    
    
    def optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Optimize a plan by combining similar steps and removing redundancies.
        """
        print(f"🔧 [{self.name}] Optimizing plan...")
        
        # Remove duplicate file operations
        seen_files = set()
        optimized_steps = []
        
        for step in plan.steps:
            if step.target_file:
                if step.target_file in seen_files and step.action_type == "create_file":
                    # Skip duplicate file creation
                    continue
                seen_files.add(step.target_file)
            
            optimized_steps.append(step)
        
        # Update step numbers
        for i, step in enumerate(optimized_steps, 1):
            step.step_number = i
        
        # Create optimized plan
        return ExecutionPlan(
            plan_id=plan.plan_id,
            steps=optimized_steps,
            estimated_files=list(set(plan.estimated_files)),  # Remove duplicates
            dependencies=plan.dependencies,
            notes=plan.notes
        )
    
    
    async def refine_plan(
        self,
        original_plan: ExecutionPlan,
        feedback: str,
        project_context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Refine an existing plan based on feedback or errors.
        
        This is useful when a plan needs adjustment after errors or user input.
        """
        print(f"🔄 [{self.name}] Refining plan based on feedback...")
        
        # Create a prompt for plan refinement
        prompt = f"""Refine this execution plan based on feedback.

Original Plan:
{self._plan_to_string(original_plan)}

Feedback: {feedback}

Project Context:
{project_context}

Create an updated plan that addresses the feedback while maintaining the original goal."""

        try:
            # Get refined plan from AI using streaming
            refined_data = await ai_service.generate_structured_response(
                prompt=prompt,
                system_instruction=PLANNING_AGENT_SYSTEM,
                websocket_callback=self._silent_callback,
                conversation_id="planning_refinement",
                response_format="json"
            )
            
            refined_plan = self._parse_plan(refined_data)
            print(f"✅ [{self.name}] Plan refined")
            return refined_plan
        
        except Exception as e:
            print(f"❌ [{self.name}] Plan refinement failed: {str(e)}")
            # Return original plan if refinement fails
            return original_plan
    
    
    def _plan_to_string(self, plan: ExecutionPlan) -> str:
        """
        Convert a plan to a readable string format.
        """
        lines = [f"Plan ID: {plan.plan_id}"]
        lines.append(f"Steps: {len(plan.steps)}")
        
        for step in plan.steps:
            lines.append(f"  {step.step_number}. {step.action_type}: {step.description}")
            if step.target_file:
                lines.append(f"     File: {step.target_file}")
        
        return "\n".join(lines)
    
    
    def get_step_by_number(self, plan: ExecutionPlan, step_number: int) -> Optional[ActionStep]:
        """
        Get a specific step from a plan by its number.
        """
        for step in plan.steps:
            if step.step_number == step_number:
                return step
        return None
    
    
    def get_next_step(self, plan: ExecutionPlan, current_step: int) -> Optional[ActionStep]:
        """
        Get the next step in the plan after the current one.
        """
        return self.get_step_by_number(plan, current_step + 1)
    
    
    def is_plan_complete(self, plan: ExecutionPlan, current_step: int) -> bool:
        """
        Check if all steps in the plan have been executed.
        """
        return current_step >= len(plan.steps)


# Create singleton instance
planning_agent = PlanningAgent()


# Export
__all__ = ['PlanningAgent', 'planning_agent']