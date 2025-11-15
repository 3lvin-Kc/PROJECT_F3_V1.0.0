# F3 AI Backend

This is the backend service for the F3 AI platform, an AI-powered Flutter widget generation platform.

## Features

- AI-powered Flutter widget generation
- Real-time WebSocket communication for progress updates
- Project management APIs
- File manipulation services
- Widget preview generation

## Tech Stack

- Python 3.x
- FastAPI (Web framework)
- Uvicorn (ASGI server)
- Google Generative AI (Gemini)
- SQLite (Database)

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file based on `.env.example` and add your API keys:
   ```
   GEMINI_API_KEY=your_api_key_here
   PORT=8000
   ENVIRONMENT=development
   ```

4. Run the server:
   ```bash
   python start_server.py
   ```

## API Endpoints

### WebSocket
- `ws://localhost:8000/ws/{client_id}` - Real-time AI progress updates

### Health Check
- `GET /health` - System health check

### AI Chat
- `POST /api/chat` - Main AI conversation

### Projects
- `POST /api/projects` - Create a new project
- `GET /api/projects/{id}` - Get project information
- `DELETE /api/projects/{id}` - Delete a project
- `GET /api/projects/{id}/files` - List project files

### Files
- `POST /api/files/read` - Read file content
- `POST /api/files/write` - Write file content

### Preview
- `POST /api/preview/generate` - Generate widget preview

### Conversations
- `DELETE /api/conversations/{id}` - Clear conversation

## Project Structure

```
backend/
├── server/
│   ├── agents/          # AI agents (intent classifier, planner, coder, etc.)
│   ├── coordinator/      # Agent coordination logic
│   ├── database/         # Database models and repositories
│   ├── models/           # Data models
│   ├── projects/         # Project management services
│   ├── services/         # Core services (AI, file, preview, etc.)
│   ├── utils/            # Utility functions
│   └── main.py           # Main application entry point
├── projects/             # Generated Flutter projects
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
└── start_server.py       # Server startup script
```

## Development

The backend uses several specialized AI agents to handle different aspects of Flutter development:

1. **Intent Classifier Agent** - Determines the type of request
2. **Planning Agent** - Creates implementation plans for complex tasks
3. **Coding Agent** - Generates Flutter code
4. **Error Recovery Agent** - Fixes compilation errors
5. **Chat Agent** - Handles conversational interactions

