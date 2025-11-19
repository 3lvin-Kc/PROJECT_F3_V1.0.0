# Database Implementation - MVP

## Overview
SQLite3 database implementation for storing project data, chat history, files, and code.

## Database Schema

### Tables

#### 1. **projects**
- `id` (INTEGER, PRIMARY KEY)
- `project_id` (TEXT, UNIQUE) - Unique identifier for the project
- `created_at` (TIMESTAMP) - Project creation time
- `updated_at` (TIMESTAMP) - Last update time

#### 2. **chat_history**
- `id` (INTEGER, PRIMARY KEY)
- `project_id` (TEXT, FOREIGN KEY) - Links to projects table
- `user_prompt` (TEXT) - User's message/prompt
- `ai_response` (TEXT) - AI's response
- `intent` (TEXT) - Intent classification (chat/code)
- `timestamp` (TIMESTAMP) - When the message was sent

#### 3. **files**
- `id` (INTEGER, PRIMARY KEY)
- `project_id` (TEXT, FOREIGN KEY) - Links to projects table
- `file_path` (TEXT) - Full file path
- `file_name` (TEXT) - File name
- `created_at` (TIMESTAMP) - File creation time
- `updated_at` (TIMESTAMP) - Last update time

#### 4. **code**
- `id` (INTEGER, PRIMARY KEY)
- `file_id` (INTEGER, FOREIGN KEY) - Links to files table
- `code_content` (TEXT) - Actual code content
- `created_at` (TIMESTAMP) - When code was saved
- `updated_at` (TIMESTAMP) - Last update time

## Files Created/Modified

### New Files
- **`backend/server/database.py`** - Database manager class with all CRUD operations

### Modified Files
- **`backend/server/main.py`**
  - Added `project_id` to `AgentRequest` model
  - Added project creation on request
  - Added new endpoints for retrieving project data

- **`backend/server/orchestrator.py`**
  - Now accepts `project_id` from request
  - Stores chat messages in database after processing
  - Stores intent classification

## Database API

### Database Class Methods

#### Projects
- `create_project(project_id)` - Create new project
- `get_project(project_id)` - Get project by ID
- `get_project_summary(project_id)` - Get project with all related data

#### Chat History
- `add_chat_message(project_id, user_prompt, ai_response, intent)` - Store chat message
- `get_chat_history(project_id)` - Get all messages for a project

#### Files
- `create_file(project_id, file_path, file_name)` - Create file record
- `get_files_by_project(project_id)` - Get all files for a project
- `get_file(file_id)` - Get specific file

#### Code
- `save_code(file_id, code_content)` - Save code for a file
- `get_code_by_file(file_id)` - Get latest code for a file
- `get_all_code_by_file(file_id)` - Get all code versions for a file

#### Utility
- `delete_project(project_id)` - Delete entire project and related data

## API Endpoints

### New Endpoints

#### GET `/api/projects/{project_id}`
Returns project details with chat history and files.

**Response:**
```json
{
  "project": {
    "id": 1,
    "project_id": "proj_123",
    "created_at": "2025-11-19 17:00:00",
    "updated_at": "2025-11-19 17:05:00"
  },
  "chat_history": [...],
  "files": [...],
  "file_count": 5,
  "chat_count": 3
}
```

#### GET `/api/projects/{project_id}/chat-history`
Returns only chat history for a project.

**Response:**
```json
{
  "project_id": "proj_123",
  "chat_history": [
    {
      "id": 1,
      "project_id": "proj_123",
      "user_prompt": "Create a button component",
      "ai_response": "...",
      "intent": "code",
      "timestamp": "2025-11-19 17:00:00"
    }
  ]
}
```

### Modified Endpoints

#### POST `/api/agent/stream`
Now requires `project_id` in request body.

**Request:**
```json
{
  "message": "Create a button component",
  "project_id": "proj_123"
}
```

## Database Location
- **Path:** `backend/app.db`
- **Type:** SQLite3
- **Auto-created:** Yes (on first run)

## Usage Flow

1. **Frontend generates project_id** when user enters editor
2. **Frontend sends request** with `project_id` and `message`
3. **Backend creates project** if it doesn't exist
4. **Orchestrator processes request** and stores chat message
5. **Frontend can retrieve history** using GET endpoints

## Future Enhancements

- Add file content storage (currently schema ready)
- Add code versioning (track multiple versions per file)
- Add design plan storage
- Add user_id when auth is implemented
- Add indexing for better query performance
- Add soft deletes for audit trail
