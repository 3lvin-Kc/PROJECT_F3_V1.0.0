# F3 Platform Backend Architecture

## Overview

The backend is built with **FastAPI** and implements a sequential agent pipeline for intelligent code generation. All agents follow a single-source-of-truth prompt system and are orchestrated through a centralized pipeline.

## Directory Structure

```
backend/
├── server/
│   ├── main.py                    # FastAPI app initialization & routes
│   ├── config.py                  # Centralized configuration management
│   ├── orchestrator.py            # Sequential agent pipeline orchestrator
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py   # Routes user intent (chat vs. code)
│   │   ├── chat_agent.py          # Conversational responses
│   │   ├── designing_agent.py     # Flutter widget scaffold design
│   │   └── coding_agent.py        # Code generation for designed files
│   └── prompts/
│       ├── __init__.py
│       ├── loader.py              # PromptLoader class for centralized access
│       └── prompts.yaml           # Single source of truth for all prompts
├── .env                           # Environment variables
└── requirements.txt               # Python dependencies
```

## Key Components

### 1. Configuration Layer (`config.py`)

Centralized configuration management that loads environment variables once at startup.

**Features:**
- Single point of configuration
- Environment-based settings
- Validation on startup
- Prevents repeated `.env` loading across agents

**Usage:**
```python
from .config import Config

Config.validate()  # Validates required variables
api_key = Config.GOOGLE_API_KEY
model_name = Config.MODEL_NAME
```

### 2. Prompt System (`prompts/`)

**Single Source of Truth** for all agent prompts stored in YAML format.

**Structure:**
- `prompts.yaml` - All prompts organized by agent
- `loader.py` - PromptLoader class with caching

**Benefits:**
- Easy to maintain and update prompts
- Version control friendly
- No hardcoded prompts in agent code
- Cached in memory for performance

**Usage:**
```python
from ..prompts import PromptLoader

prompt_template = PromptLoader.get('intent_classifier', 'classification')
prompt = prompt_template.format(message=user_message)
```

### 3. Agents

#### **IntentClassifier**
- **Purpose:** Routes user intent to either "chat" or "code"
- **Input:** User message
- **Output:** Intent classification
- **Events:** `intent.classified`

#### **ChatAgent**
- **Purpose:** Handles conversational interactions
- **Input:** User message
- **Output:** Streamed conversational response
- **Events:** `chat.chunk`

#### **DesigningAgent**
- **Purpose:** Creates minimal Flutter widget scaffold
- **Input:** User request
- **Output:** JSON with file structure (5-file scaffold)
- **Events:** `design.started`, `design.phase`, `design.completed`
- **Rule:** Only generates minimal scaffold on first request

#### **CodingAgent**
- **Purpose:** Generates code for each file in the design plan
- **Input:** Design plan (files list) + original user request
- **Output:** Streamed code for each file
- **Events:** `code.started`, `code.file_started`, `code.chunk`, `code.completed`
- **Rule:** No chain-of-thought exposure, only final code

### 4. Orchestrator (`orchestrator.py`)

Manages sequential execution of agents:

1. **Pipeline Started** → Emit `pipeline.started`
2. **Intent Classification** → Route to appropriate agent
3. **Intent == "chat"** → Run ChatAgent
4. **Intent == "code"** → Run DesigningAgent → Run CodingAgent
5. **Pipeline Completed** → Emit `pipeline.completed`

### 5. FastAPI Server (`main.py`)

**Endpoints:**

- `GET /health` - Health check for monitoring
- `POST /api/agent/stream` - Main streaming endpoint

**Features:**
- Proper initialization and validation
- CORS middleware configuration
- Logging setup
- Startup/shutdown event handlers
- SSE (Server-Sent Events) streaming

## Event Flow

### Chat Request
```
User Message
    ↓
IntentClassifier → "chat"
    ↓
ChatAgent (streaming)
    ↓
Events: chat.chunk
```

### Code Request
```
User Message
    ↓
IntentClassifier → "code"
    ↓
DesigningAgent (streaming)
    ↓
Design Plan (5 files)
    ↓
CodingAgent (streaming)
    ↓
Events: code.file_started, code.chunk, code.completed
```

## Configuration

Environment variables (`.env`):

```env
GOOGLE_API_KEY=your_api_key_here
MODEL_NAME=gemini-1.5-flash
HOST=127.0.0.1
PORT=8000
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

## Running the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn backend.server.main:app --reload
```

The server will start at `http://127.0.0.1:8000` with:
- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## System Rules Compliance

✅ **Sequential Agents** - Orchestrator enforces strict order
✅ **Single Prompt File** - All prompts in `prompts.yaml`
✅ **Scaffold-First** - DesigningAgent creates 5-file scaffold
✅ **Chat vs. Code Routing** - IntentClassifier routes correctly
✅ **UI Streaming** - FastAPI SSE streaming implemented
✅ **No Chain-of-Thought** - CodingAgent only outputs final code
✅ **Modular Frontend** - React + TypeScript structure
✅ **Python FastAPI Backend** - Async/await throughout

## Adding New Prompts

1. Add to `prompts.yaml` under the appropriate agent
2. Access via `PromptLoader.get('agent_name', 'prompt_key')`
3. No code changes needed

## Error Handling

Each agent includes:
- Try-catch blocks for graceful failures
- Error events yielded to frontend
- Fallback behavior (e.g., default to "chat" on classification error)
- Logging for debugging

## Performance Considerations

- **Prompt Caching:** PromptLoader caches prompts in memory
- **Streaming:** All responses streamed via SSE for real-time UI updates
- **Async/Await:** Non-blocking I/O throughout
- **Configuration Validation:** One-time validation at startup
