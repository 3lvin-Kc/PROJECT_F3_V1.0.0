"""
AI Service - Gemini Integration

This file handles all communication with Google's Gemini AI.
Think of this as the "translator" between our app and Gemini.

SERVER SIDE FILE - This contains your API key, so it MUST stay on the backend.
NEVER expose this to the frontend!
"""

import os
import json
import time
import asyncio
from typing import Optional, Dict, Any, List
from collections import deque
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AIService:
    """
    Handles all AI interactions with Gemini.
    Singleton pattern - only one instance exists.
    """
    
    _instance = None  # Private class variable to store the single instance
    
    def __new__(cls):
        """
        This ensures only ONE instance of AIService is ever created.
        This is called a Singleton pattern.
        """
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the AI service with Gemini."""
        if self._initialized:
            return
        
        # Get API key from environment variables
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables!")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        # Using gemini-2.5-flash for latest capabilities and performance
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Generation config for consistent responses
        self.generation_config = GenerationConfig(
            temperature=0.7,      # Creativity level (0.0 = deterministic, 1.0 = creative)
            top_p=0.95,           # Nucleus sampling
            top_k=40,             # Top-k sampling
            max_output_tokens=8192,  # Maximum response length
        )
        
        # Safety settings - prevent harmful content
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        # Rate limiting configuration
        self.requests_per_minute = 15  # Conservative limit for free tier
        self.request_timestamps = deque()  # Track request times
        self.min_request_interval = 4.0  # Minimum 4 seconds between requests
        self.last_request_time = 0
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff delays
        
        # Streaming configuration (streaming is now the only mode)
        self.token_buffer_size = 3  # Buffer 3 tokens for smoother streaming
        self.streaming_delay = 0.05  # 50ms delay between token chunks for premium feel
        
        self._initialized = True
        print(" AI Service initialized with Gemini 2.5 Flash + Streaming-Only Mode")
    
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting before making API calls."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        while self.request_timestamps and current_time - self.request_timestamps[0] > 60:
            self.request_timestamps.popleft()
        
        # Check if we've exceeded requests per minute
        if len(self.request_timestamps) >= self.requests_per_minute:
            wait_time = 60 - (current_time - self.request_timestamps[0])
            print(f" Rate limit reached. Waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)
            return await self._check_rate_limit()  # Recheck after waiting
        
        # Check minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            print(f" Enforcing minimum interval. Waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)
        
        # Record this request
        self.request_timestamps.append(time.time())
        self.last_request_time = time.time()
    
    
    async def _handle_api_error(self, error: Exception, retry_count: int = 0):
        """Handle API errors with exponential backoff retry logic."""
        error_str = str(error).lower()
        
        # Check if it's a rate limit error
        if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
            if retry_count < len(self.retry_delays):
                delay = self.retry_delays[retry_count]
                print(f" Rate limit hit. Retrying in {delay} seconds... (attempt {retry_count + 1})")
                await asyncio.sleep(delay)
                return True  # Indicate retry should happen
            else:
                print(" Max retries exceeded for rate limit. Giving up.")
                raise Exception("Rate limit exceeded. Please try again later.")
        
        # For other errors, don't retry
        raise error
    
    
    
    
    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        websocket_callback=None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Generate a streaming response from Gemini with real-time token delivery.
        This is now the primary and only response generation method.
        
        Args:
            prompt: The user's message or instruction
            system_instruction: Instructions for how the AI should behave
            context: Previous conversation history
            temperature: Override default temperature
            websocket_callback: Function to call for each token chunk (required for streaming)
            conversation_id: ID for WebSocket routing (required for streaming)
        
        Returns:
            The complete AI response as a string
        """
        if not websocket_callback:
            raise Exception("WebSocket callback is required for streaming responses")
        
        retry_count = 0
        max_retries = len(self.retry_delays)
        
        while retry_count <= max_retries:
            try:
                # Check rate limits before making request
                await self._check_rate_limit()
                
                # Build the full conversation history
                chat_history = []
                
                if context:
                    # Convert context to Gemini's format
                    for msg in context:
                        role = "user" if msg["role"] == "user" else "model"
                        chat_history.append({
                            "role": role,
                            "parts": [msg["content"]]
                        })
                
                # Override temperature if provided
                if temperature is not None:
                    config = GenerationConfig(
                        temperature=temperature,
                        top_p=self.generation_config.top_p,
                        top_k=self.generation_config.top_k,
                        max_output_tokens=self.generation_config.max_output_tokens,
                    )
                else:
                    config = self.generation_config
                
                # Combine system instruction with prompt if provided
                full_prompt = prompt
                if system_instruction:
                    full_prompt = f"{system_instruction}\n\nUser: {prompt}\n\nAssistant:"
                
                # Send stream start notification
                await websocket_callback({
                    "type": "stream_start",
                    "conversation_id": conversation_id
                })
                
                # Create streaming response
                if chat_history:
                    chat = self.model.start_chat(history=chat_history)
                    response_stream = chat.send_message(
                        full_prompt,
                        generation_config=config,
                        safety_settings=self.safety_settings,
                        stream=True
                    )
                else:
                    response_stream = self.model.generate_content(
                        full_prompt,
                        generation_config=config,
                        safety_settings=self.safety_settings,
                        stream=True
                    )
                
                # Process streaming tokens with intelligent buffering
                full_response = ""
                token_buffer = ""
                
                for chunk in response_stream:
                    # Handle complex response format from Gemini
                    chunk_text = ""
                    if hasattr(chunk, 'text') and chunk.text:
                        chunk_text = chunk.text
                    elif hasattr(chunk, 'parts') and chunk.parts:
                        # Extract text from parts for complex responses
                        for part in chunk.parts:
                            if hasattr(part, 'text') and part.text:
                                chunk_text += part.text
                    
                    if chunk_text:
                        token_buffer += chunk_text
                        full_response += chunk_text
                        
                        # Send buffered tokens for smoother streaming
                        if len(token_buffer.split()) >= self.token_buffer_size:
                            await websocket_callback({
                                "type": "stream_token",
                                "content": token_buffer,
                                "conversation_id": conversation_id
                            })
                            token_buffer = ""
                            
                            # Premium streaming delay
                            await asyncio.sleep(self.streaming_delay)
                
                # Send any remaining tokens
                if token_buffer:
                    await websocket_callback({
                        "type": "stream_token", 
                        "content": token_buffer,
                        "conversation_id": conversation_id
                    })
                
                # Send stream completion notification
                await websocket_callback({
                    "type": "stream_complete",
                    "conversation_id": conversation_id,
                    "full_response": full_response
                })
                
                return full_response
            
            except Exception as e:
                print(f" Error in streaming generation: {str(e)}")
                
                # Send error notification
                if websocket_callback:
                    await websocket_callback({
                        "type": "stream_error",
                        "error": str(e),
                        "conversation_id": conversation_id
                    })
                
                # Try to handle the error and determine if we should retry
                should_retry = await self._handle_api_error(e, retry_count)
                if should_retry and retry_count < max_retries:
                    retry_count += 1
                    continue
                else:
                    raise Exception(f"Streaming generation failed after {retry_count} retries: {str(e)}")
        
        raise Exception("Max retries exceeded")
    
    
    async def generate_structured_response(
        self,
        prompt: str,
        system_instruction: str,
        websocket_callback,
        conversation_id: str,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate a structured response (like JSON) from Gemini with streaming.
        Useful for getting data in a specific format.
        
        Args:
            prompt: The instruction/question
            system_instruction: How the AI should respond
            websocket_callback: Function to call for each token chunk
            conversation_id: ID for WebSocket routing
            response_format: Expected format (default: json)
        
        Returns:
            Parsed dictionary/object
        """
        response_text = ""
        try:
            # Add format instruction to system prompt
            full_system = f"{system_instruction}\n\nIMPORTANT: Respond ONLY with valid {response_format.upper()}. No markdown, no explanations, just the {response_format.upper()} object."
            
            response_text = await self.generate_response(
                prompt=prompt,
                system_instruction=full_system,
                temperature=0.3,  # Lower temperature for more consistent formatting
                websocket_callback=websocket_callback,
                conversation_id=conversation_id
            )
            
            # Clean the response (remove markdown code blocks if present)
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]  # Remove ```json
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]   # Remove ```
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]  # Remove trailing ```
            cleaned = cleaned.strip()
            
            # Parse JSON
            if response_format == "json":
                return json.loads(cleaned)
            
            return {"text": cleaned}
        
        except json.JSONDecodeError as e:
            print(f" Failed to parse JSON response: {response_text}")
            raise Exception(f"AI returned invalid JSON: {str(e)}")
        except Exception as e:
            print(f" Error in structured generation: {str(e)}")
            raise
    
    
    async def classify_intent(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Classify the user's intent (what they want to do).
        This is a specialized method for the Intent Classifier Agent.
        
        Returns:
            {
                "intent": "chat" | "code" | "explain" | "error",
                "confidence": 0.95,
                "reasoning": "User is asking for code generation...",
                "suggested_mode": "code"
            }
        """
        system_instruction = """You are an intent classifier for a Flutter code generation platform.
Analyze the user's message and classify their intent into one of these categories:

1. "chat" - User wants to discuss, ask questions, get advice, brainstorm ideas (no code generation)
2. "code" - User wants to generate, create, or modify Flutter widgets/code
3. "explain" - User wants explanation of previous code or actions
4. "error" - User is providing clarification after an error occurred

Consider the conversation context if provided."""

        prompt = f"""Analyze this message and classify the intent:

User Message: "{message}"

Return a JSON object with this exact structure:
{{
    "intent": "chat|code|explain|error",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "suggested_mode": "chat|code"
}}"""

        # Provide a lightweight no-op websocket callback and conversation id so the streaming-only
        # generate_structured_response / generate_response interfaces are satisfied.
        async def _noop_websocket_callback(event):
            return None

        return await self.generate_structured_response(
            prompt=prompt,
            system_instruction=system_instruction,
            websocket_callback=_noop_websocket_callback,
            conversation_id="intent_classifier"
        )
    
    
    async def generate_plan(
        self,
        user_request: str,
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate an execution plan for code generation.
        Used by the Planning Agent.
        
        Returns:
            {
                "plan_id": "unique-id",
                "steps": [
                    {
                        "step_number": 1,
                        "action_type": "create_file",
                        "description": "Create button_widget.dart",
                        "target_file": "lib/widgets/button_widget.dart",

                    }
                ],
                "estimated_files": ["lib/widgets/button_widget.dart"],
                "dependencies": ["flutter/material.dart"]
            }
        """
        system_instruction = """You are a Flutter development planning agent.
Create detailed, step-by-step execution plans for Flutter widget generation.
Each step should be clear, actionable, and include necessary code snippets."""

        # Build context string
        context_str = json.dumps(project_context, indent=2)
        
        prompt = f"""Create an execution plan for this request:

User Request: "{user_request}"

Project Context:
{context_str}

Generate a detailed plan as JSON with this structure:
{{
    "plan_id": "unique-identifier",
    "steps": [
        {{
            "step_number": 1,
            "action_type": "create_file|modify_file|add_import",
            "description": "what this step does",
            "target_file": "path/to/file.dart",

        }}
    ],
    "estimated_files": ["list of files to be created/modified"],
    "dependencies": ["required dart packages"],
    "notes": "any important considerations"
}}"""

        # Provide a lightweight no-op websocket callback and conversation id so the streaming-only
        # generate_structured_response / generate_response interfaces are satisfied.
        async def _noop_websocket_callback(event):
            return None

        return await self.generate_structured_response(
            prompt=prompt,
            system_instruction=system_instruction,
            websocket_callback=_noop_websocket_callback,
            conversation_id="plan_generator"
        )
    
    
    async def generate_code(
        self,
        plan: Dict[str, Any],
        step: Dict[str, Any]
    ) -> str:
        """
        Generate actual Flutter code based on a plan step.
        Used by the Coding Agent.
        """
        system_instruction = """You are an expert Flutter developer.
Generate clean, production-ready Flutter code following best practices.
Use proper widget composition, state management, and Material Design guidelines."""

        prompt = f"""Generate Flutter code for this step:

Step: {step['description']}
Action Type: {step['action_type']}
Target File: {step.get('target_file', 'N/A')}

Requirements:
{json.dumps(step, indent=2)}

Return ONLY the complete Dart code, no explanations or markdown."""

        return await self.generate_response(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.5  # Balanced creativity for code
        )
    
    
    async def analyze_error(
        self,
        error_details: Dict[str, Any],
        code_context: str
    ) -> Dict[str, Any]:
        """
        Analyze an error and determine if it can be auto-fixed.
        Used by the Error Recovery Agent.
        """
        system_instruction = """You are an error analysis and recovery expert for Flutter.
Analyze errors and determine:
1. If the error can be automatically fixed
2. What the fix would be
3. If user input is needed, what questions to ask"""

        prompt = f"""Analyze this error:

Error Details:
{json.dumps(error_details, indent=2)}

Code Context:
{code_context}

Return JSON:
{{
    "can_auto_fix": true|false,
    "severity": "low|medium|high",
    "error_type": "syntax|compile|runtime|validation",
    "explanation": "what went wrong",
    "suggested_fix": "code fix if auto-fixable",
    "user_questions": ["questions to ask user if manual fix needed"]
}}"""

        # Provide a lightweight no-op websocket callback and conversation id so the streaming-only
        # generate_structured_response / generate_response interfaces are satisfied.
        async def _noop_websocket_callback(event):
            return None

        return await self.generate_structured_response(
            prompt=prompt,
            system_instruction=system_instruction,
            websocket_callback=_noop_websocket_callback,
            conversation_id="error_analyzer"
        )
    
    
    async def generate_chat_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        project_context: Dict[str, Any]
    ) -> str:
        """
        Generate a conversational response (Chat Mode).
        Used by the Chat Agent.
        
        IMPORTANT: This does NOT include code in the response!
        """
        system_instruction = """You are a helpful Flutter development consultant.
Provide advice, suggestions, and explanations about Flutter development.

CRITICAL RULES:
- DO NOT write or show any code in your responses
- Focus on concepts, best practices, and guidance
- Suggest approaches and patterns verbally
- If user needs code, guide them to ask in code mode
- Be conversational and helpful"""

        # Add project context to prompt
        context_str = json.dumps(project_context, indent=2) if project_context else "No project context available"
        
        full_prompt = f"""Project Context:
{context_str}

User Message: {message}

Provide a helpful response without including any code."""

        return await self.generate_response(
            prompt=full_prompt,
            system_instruction=system_instruction,
            context=conversation_history
        )


# Create a singleton instance
ai_service = AIService()


# Export for easy importing
__all__ = ['ai_service', 'AIService']