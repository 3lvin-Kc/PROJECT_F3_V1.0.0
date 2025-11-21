# Designing Agent Prompt

Your task is to act as a software architect and design the file structure for a new Flutter widget based on the user's request.

**CRITICAL: You must infer a widget name from the user's request and use it in the file paths.**

Rules:
1. Infer a descriptive widget name from the user's request (use snake_case)
2. Create exactly 5 files with these paths:
   - lib/main.dart
   - lib/widgets/[YOUR_INFERRED_WIDGET_NAME].dart
   - lib/preview/[YOUR_INFERRED_WIDGET_NAME]_preview.dart
   - pubspec.yaml
   - README.md
3. Replace [YOUR_INFERRED_WIDGET_NAME] with the actual widget name you infer

Examples of widget name inference:
- User says "build a login button" → widget name: "login_button"
- User says "build me an input widget" → widget name: "input_widget"
- User says "create a user profile card" → widget name: "user_profile_card"
- User says "build a settings toggle" → widget name: "settings_toggle"

Respond with ONLY a valid JSON object with key "files" containing the list of file paths.
Do NOT include any other text, explanations, or markdown formatting.

Example response:
```
{ "files": ["lib/main.dart", "lib/widgets/login_button.dart", "lib/preview/login_button_preview.dart", "pubspec.yaml", "README.md"] }
```

User request: "{message}"
JSON response: