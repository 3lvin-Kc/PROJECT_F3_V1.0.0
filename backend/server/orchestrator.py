from .agents import intent_classifier, chat_agent, designing_agent, coding_agent

async def run_agent_pipeline(request):
    """Manages the sequential execution of agents."""

    yield {"event": "pipeline.started"}

    # 1. Classify intent
    intent = await intent_classifier.classify_intent(request.message)
    yield {"event": "intent.classified", "intent": intent}

    # 2. Route based on intent
    if intent == "chat":
        async for event in chat_agent.run_chat_agent(request.message):
            yield event
    elif intent == "code":
        design_plan = None
        async for event in designing_agent.run_designing_agent(request.message):
            if event.get("event") == "design.completed":
                design_plan = event
            yield event
        
        if design_plan:
            async for event in coding_agent.run_coding_agent(design_plan, request.message):
                yield event

    yield {"event": "pipeline.completed"}
