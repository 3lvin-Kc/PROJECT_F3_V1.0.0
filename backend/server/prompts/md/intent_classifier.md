# Intent Classifier Prompt

Your task is to classify the user's intent into one of two categories: 'chat' or 'code'.

'code': The user wants to create, build, modify, or add to a software project. Examples: "build a login page", "add a button", "refactor this function".

'chat': The user is asking a question, seeking an explanation, or having a general conversation. Examples: "how does this work?", "what is a widget?", "can you explain that?".

If the intent is ambiguous, default to 'chat'.

Respond with only the single word 'chat' or 'code'.

User message: "{message}"
Classification: