"""
Intent Classifier Agent
=======================
This agent analyzes user messages and determines what they want to do.
Think of it as a "traffic controller" that routes messages to the right place.

SERVER SIDE FILE
"""

from typing import Dict, Any, Optional, List
from ..models.message_models import IntentType, IntentClassification, ModeType, Message
from ..services.ai_service import ai_service
from ..utils.prompt_templates import (
    INTENT_CLASSIFIER_SYSTEM,
    build_intent_prompt
)


class IntentClassifierAgent:
    """
    Analyzes user messages and classifies their intent.
    
    This agent decides:
    - What does the user want? (chat, code, explain, error)
    - Which mode should we be in? (chat mode or code mode)
    - How confident are we? (0.0 to 1.0)
    """
    
    def __init__(self):
        """Initialize the Intent Classifier Agent."""
        self.name = "IntentClassifierAgent"
        print(f"✅ {self.name} initialized")
    
    async def _silent_callback(self, stream_data: Dict):
        """Silent callback for internal AI processing - doesn't send to users."""
        # Intent classification happens internally and doesn't need user-visible streaming
        pass
    
    
    async def classify(
        self,
        message: str,
        conversation_history: Optional[List[Message]] = None,
        current_mode: Optional[ModeType] = None
    ) -> IntentClassification:
        """
        Classify the intent of a user message.
        
        Args:
            message: The user's message to classify
            conversation_history: Previous messages for context
            current_mode: Current mode (chat or code)
        
        Returns:
            IntentClassification object with intent, confidence, and reasoning
        
        Example:
            result = await classifier.classify("Create a blue button")
            # result.intent = IntentType.CODE
            # result.confidence = 0.95
            # result.suggested_mode = ModeType.CODE_MODE
        """
        try:
            print(f"\n🔍 [{self.name}] Classifying message: '{message[:50]}...'")
            
            # Build context from conversation history
            context = self._build_context(conversation_history, current_mode)
            
            # Create the prompt
            prompt = build_intent_prompt(message, context)
            
            # Get classification from AI (using silent streaming for internal processing)
            result = await ai_service.generate_structured_response(
                prompt=prompt,
                system_instruction=INTENT_CLASSIFIER_SYSTEM,
                websocket_callback=self._silent_callback,
                conversation_id="intent_classification",
                response_format="json"
            )
            
            # Validate and parse the result
            intent_classification = self._parse_result(result)
            
            print(f"✅ [{self.name}] Classified as: {intent_classification.intent.value} "
                  f"(confidence: {intent_classification.confidence:.2f})")
            
            return intent_classification
        
        except Exception as e:
            print(f"❌ [{self.name}] Error during classification: {str(e)}")
            # Return a safe default (chat mode with low confidence)
            return IntentClassification(
                intent=IntentType.CHAT,
                confidence=0.3,
                reasoning=f"Classification failed: {str(e)}. Defaulting to chat mode.",
                suggested_mode=ModeType.CHAT_MODE
            )
    
    
    def _build_context(
        self,
        conversation_history: Optional[List[Message]],
        current_mode: Optional[ModeType]
    ) -> Dict[str, Any]:
        """
        Build context dictionary from conversation history.
        
        This helps the AI understand what's been discussed before.
        """
        context = {}
        
        if conversation_history:
            # Get last 5 messages for context (we don't need the entire history)
            recent_messages = conversation_history[-5:]
            context["history"] = [
                {
                    "role": msg.role.value,
                    "content": msg.content
                }
                for msg in recent_messages
            ]
        
        if current_mode:
            context["current_mode"] = current_mode.value
        
        return context
    
    
    def _parse_result(self, result: Dict[str, Any]) -> IntentClassification:
        """
        Parse the AI's response into an IntentClassification object.
        
        This handles validation and provides defaults if something is missing.
        """
        try:
            # Map string intent to IntentType enum
            intent_str = result.get("intent", "chat").lower()
            intent_map = {
                "chat": IntentType.CHAT,
                "code": IntentType.CODE,
                "explain": IntentType.EXPLAIN,
                "error": IntentType.ERROR_CLARIFICATION
            }
            intent = intent_map.get(intent_str, IntentType.CHAT)
            
            # Map suggested mode
            mode_str = result.get("suggested_mode", "chat").lower()
            mode_map = {
                "chat": ModeType.CHAT_MODE,
                "code": ModeType.CODE_MODE
            }
            suggested_mode = mode_map.get(mode_str, ModeType.CHAT_MODE)
            
            # Get confidence (ensure it's between 0 and 1)
            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            # Get reasoning
            reasoning = result.get("reasoning", "No reasoning provided")
            
            return IntentClassification(
                intent=intent,
                confidence=confidence,
                reasoning=reasoning,
                suggested_mode=suggested_mode
            )
        
        except Exception as e:
            print(f"⚠️ [{self.name}] Error parsing result: {str(e)}")
            # Return safe default
            return IntentClassification(
                intent=IntentType.CHAT,
                confidence=0.3,
                reasoning="Failed to parse classification result",
                suggested_mode=ModeType.CHAT_MODE
            )
    
    
    def should_switch_mode(
        self,
        classification: IntentClassification,
        current_mode: ModeType
    ) -> bool:
        """
        Determine if we should switch modes based on the classification.
        
        Args:
            classification: The intent classification result
            current_mode: The current mode
        
        Returns:
            True if mode should be switched, False otherwise
        
        Logic:
            - If intent is CODE and we're in CHAT_MODE → switch to CODE_MODE
            - If intent is CHAT/EXPLAIN and we're in CODE_MODE → switch to CHAT_MODE
            - If intent is ERROR, stay in current mode
        """
        # High confidence threshold for switching
        CONFIDENCE_THRESHOLD = 0.7
        
        # Don't switch on low confidence
        if classification.confidence < CONFIDENCE_THRESHOLD:
            print(f"⚠️ [{self.name}] Low confidence ({classification.confidence:.2f}), not switching mode")
            return False
        
        # Determine if switch is needed
        should_switch = classification.suggested_mode != current_mode
        
        if should_switch:
            print(f"🔄 [{self.name}] Recommending mode switch: "
                  f"{current_mode.value} → {classification.suggested_mode.value}")
        
        return should_switch
    
    
    async def classify_batch(
        self,
        messages: List[str],
        conversation_history: Optional[List[Message]] = None
    ) -> List[IntentClassification]:
        """
        Classify multiple messages at once.
        
        Useful for processing a queue of messages or analyzing patterns.
        """
        results = []
        for message in messages:
            classification = await self.classify(message, conversation_history)
            results.append(classification)
        return results
    
    
    def get_classification_stats(
        self,
        classifications: List[IntentClassification]
    ) -> Dict[str, Any]:
        """
        Get statistics about a set of classifications.
        
        Useful for analytics and debugging.
        """
        if not classifications:
            return {"total": 0}
        
        stats = {
            "total": len(classifications),
            "intents": {},
            "modes": {},
            "avg_confidence": sum(c.confidence for c in classifications) / len(classifications),
            "low_confidence_count": sum(1 for c in classifications if c.confidence < 0.5)
        }
        
        # Count by intent
        for c in classifications:
            intent_name = c.intent.value
            stats["intents"][intent_name] = stats["intents"].get(intent_name, 0) + 1
        
        # Count by suggested mode
        for c in classifications:
            mode_name = c.suggested_mode.value
            stats["modes"][mode_name] = stats["modes"].get(mode_name, 0) + 1
        
        return stats


# Create singleton instance
intent_classifier_agent = IntentClassifierAgent()


# Export
__all__ = ['IntentClassifierAgent', 'intent_classifier_agent']