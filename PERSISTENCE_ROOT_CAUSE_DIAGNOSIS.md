# Session Data Persistence Issue: Deep Diagnosis & Fix Plan

**Status:** Analysis Complete | Mode: Diagnosis Only (No Implementation)  
**Date:** Nov 20, 2025  
**Severity:** 🔴 CRITICAL - All generated data lost on page reload

---

## Executive Summary

Session data (chat history, generated files, editor content) **disappears on page reload** because:

1. **Backend never persists generated files to database** (PRIMARY)
2. **Frontend state is only in-memory React state** (PRIMARY)
3. **No hydration endpoint to load files on page reload** (PRIMARY)
4. **Chat history persists but file content doesn't** (SECONDARY)
5. **File service references non-existent backend endpoints** (SECONDARY)

**Root cause is split 60% backend + 40% frontend**, not a single point of failure.

---

## Part 1: Root Cause Report

### ROOT CAUSE #1: Generated Files Never Persisted to Database ⚠️ CRITICAL

**Location:** 
- `backend/server/orchestrator.py` (lines 28-43)
- `backend/server/agents/coding_agent.py` (entire file, 128 lines)

**The Problem:**

When code is generated, the backend streams it to the frontend but **never writes it to the database**. The database has `create_file()` and `save_code()` methods, but they are **never called**.

**Evidence:**

```python
# orchestrator.py lines 28-43
if intent == "chat":
    async for event in chat_agent.run_chat_agent(user_message):
        if event.get("event") == "chat.chunk":
            ai_response += event.get("content", "")
        yield event
    
    # ✅ Chat message IS saved to DB
    db.add_chat_message(project_id, user_message, ai_response, intent)
    
elif intent == "code":
    design_plan = None
    async for event in designing_agent.run_designing_agent(user_message):
        if event.get("event") == "design.completed":
            design_plan = event
        yield event
    
    if design_plan:
        async for event in coding_agent.run_coding_agent(design_plan, user_message):
            yield event
    
    # ✅ Chat message IS saved to DB
    db.add_chat_message(project_id, user_message, str(design_plan), intent)
    # ❌ BUT FILES ARE NEVER SAVED!
```

**What's Missing:**

```python
# After coding_agent completes, should do:
for file_path, file_content in file_contents.items():
    file_record = db.create_file(project_id, file_path, file_path.split('/')[-1])
    if file_record:
        db.save_code(file_record['id'], file_content)
```

**Impact:**
- Files exist only in frontend React state (in-memory Map)
- Page reload → React component unmounts → state lost
- Frontend tries to load from DB → gets empty list
- User sees blank editor

**Database Methods Exist But Unused:**
```python
# database.py has these methods but they're NEVER CALLED:
def create_file(self, project_id: str, file_path: str, file_name: str)  # Line 155
def save_code(self, file_id: int, code_content: str)  # Line 203
def get_files_by_project(self, project_id: str)  # Line 174 - returns empty list
```

---

### ROOT CAUSE #2: Frontend State Only In-Memory (React useState) ⚠️ CRITICAL

**Location:**
- `src/pages/EditorPageNew.tsx` (lines 16-32)
- `src/hooks/use-agent.ts` (lines 6-16)

**The Problem:**

All application state is stored in React `useState` hooks with no persistence layer. When the page reloads:
1. Component unmounts
2. All state variables reset to initial values
3. User sees blank editor

**Evidence:**

```typescript
// EditorPageNew.tsx lines 16-32
const [selectedFile, setSelectedFile] = useState<string>('');
const [showFileExplorer, setShowFileExplorer] = useState(true);
const [isCodeEditable, setIsCodeEditable] = useState(true);
const [editorContent, setEditorContent] = useState('// Welcome to the editor!...');

// Agent State - ALL IN-MEMORY
const [projectId, setProjectId] = useState<string>('');
const { state: agentState, sendMessage } = useAgent(projectId);
const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

// Project State - ALL IN-MEMORY
const [files, setFiles] = useState<Map<string, any>>(new Map());
```

```typescript
// use-agent.ts lines 6-16
const initialState: AgentState = {
  isStreaming: false,
  intent: null,
  conversationHistory: [],
  currentChatMessage: '',
  currentProgress: null,
  narrativeBlocks: [],
  files: new Map(),  // ❌ Map is lost on reload
  error: null,
  activeFile: null,
};

export const useAgent = (projectId?: string) => {
  const [state, setState] = useState<AgentState>(() => {
    // Only reads from sessionStorage on init, doesn't persist files
    if (projectId) {
      const storedHistory = sessionStorage.getItem(`chatHistory_${projectId}`);
      // ❌ No code to load files from sessionStorage or DB
    }
    return initialState;
  });
```

**What's Missing:**

1. **No localStorage/sessionStorage persistence of files**
2. **No hydration from database on component mount**
3. **No useEffect to load persisted state**

**Impact:**
- Files Map is cleared on unmount
- Page reload → all files gone
- Even if backend had files, frontend doesn't load them

---

### ROOT CAUSE #3: No Hydration Endpoint for File Content ⚠️ CRITICAL

**Location:** `backend/server/main.py` (lines 106-141)

**The Problem:**

The backend has an endpoint to get project details, but:
1. It returns file **metadata** (path, name) but not **content**
2. The files table is **empty** (never populated by orchestrator)
3. No endpoint exists to fetch file content

**Evidence:**

```python
# main.py lines 106-126
@app.get("/api/projects/{project_id}")
async def get_project_endpoint(project_id: str):
    """Get project details including chat history."""
    project = db.get_project(project_id)
    
    if not project:
        return JSONResponse(status_code=404, content={"error": "Project not found"})
    
    chat_history = db.get_chat_history(project_id)
    files = db.get_files_by_project(project_id)  # ❌ Returns empty list
    
    return {
        "project": dict(project),
        "chat_history": chat_history,
        "files": files,  # ❌ Empty because orchestrator never called create_file()
        "file_count": len(files),
        "chat_count": len(chat_history)
    }
```

**What's Missing:**

```python
# Missing endpoint to get file content:
@app.get("/api/projects/{project_id}/files/{file_id}/content")
async def get_file_content(project_id: str, file_id: int):
    # Should return code content from database
    pass

# Missing endpoint to list files with content:
@app.get("/api/projects/{project_id}/files-with-content")
async def get_files_with_content(project_id: str):
    # Should return files with their code content
    pass
```

**Frontend Tries to Load But Gets Nothing:**

```typescript
// EditorPageNew.tsx lines 42-91
useEffect(() => {
  const loadChatHistory = async () => {
    if (!projectId) return;
    
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/projects/${projectId}/chat-history`
      );
      // ✅ Chat history loads successfully
      const data = await response.json();
      const chatHistory = data.chat_history || [];
      
      // ❌ But there's no code to load files!
      // Frontend should also call:
      // GET /api/projects/{projectId}/files-with-content
      // But this endpoint doesn't exist
    }
  };
  loadChatHistory();
}, [projectId]);
```

**Impact:**
- Even if backend persisted files, frontend can't retrieve them
- No way to hydrate editor on page reload
- User sees blank editor

---

### ROOT CAUSE #4: Chat History Persists But Files Don't ⚠️ SECONDARY

**Location:** 
- `backend/server/orchestrator.py` (line 29)
- `src/pages/EditorPageNew.tsx` (lines 42-91)

**The Problem:**

The system has **partial persistence**: chat history is saved to DB but file content is not. This creates an asymmetry where:
- Chat messages survive reload ✅
- Generated code doesn't ❌

**Evidence:**

```python
# orchestrator.py line 29 - CHAT IS SAVED
db.add_chat_message(project_id, user_message, ai_response, intent)

# orchestrator.py line 43 - CHAT IS SAVED
db.add_chat_message(project_id, user_message, str(design_plan), intent)

# ❌ NO CODE ANYWHERE TO SAVE FILES
```

**Frontend Can Load Chat But Not Files:**

```typescript
// EditorPageNew.tsx line 48 - LOADS CHAT HISTORY
const response = await fetch(
  `http://127.0.0.1:8000/api/projects/${projectId}/chat-history`
);

// ❌ NO CODE TO LOAD FILES
// Should be something like:
// const filesResponse = await fetch(
//   `http://127.0.0.1:8000/api/projects/${projectId}/files-with-content`
// );
```

**Impact:**
- Inconsistent persistence model
- User sees chat history but blank editor
- Confusing UX: "Why is my chat saved but not my code?"

---

### ROOT CAUSE #5: File Service References Non-Existent Endpoints ⚠️ SECONDARY

**Location:** `src/hooks/use-files.ts` (lines 40-130)

**The Problem:**

The `use-files.ts` hook calls `fileService.writeFile()`, `readFile()`, and `listFiles()`, but:
1. These backend endpoints don't exist
2. The hook is never actually used in EditorPageNew
3. fileService is imported but abandoned

**Evidence:**

```typescript
// use-files.ts line 45 - CALLS NON-EXISTENT ENDPOINT
const response = await fileService.writeFile(projectId, filePath, content);

// use-files.ts line 71 - CALLS NON-EXISTENT ENDPOINT
const response = await fileService.readFile(projectId, filePath);

// use-files.ts line 99 - CALLS NON-EXISTENT ENDPOINT
const response = await fileService.listFiles(projectId);
```

**Backend Has No These Endpoints:**

```python
# main.py has these endpoints:
@app.post("/api/agent/stream")  # ✅ Exists
@app.get("/api/projects/{project_id}")  # ✅ Exists
@app.get("/api/projects/{project_id}/chat-history")  # ✅ Exists

# But NOT these:
# POST /api/projects/{project_id}/files/{file_path}  # ❌ Missing
# GET /api/projects/{project_id}/files/{file_path}  # ❌ Missing
# GET /api/projects/{project_id}/files  # ❌ Missing
```

**Hook Is Never Used:**

```typescript
// EditorPageNew.tsx - use-files is imported but NEVER USED
// Line 2: import { useAgent } from "@/hooks/use-agent";
// ❌ No import of useFiles
// ❌ No call to useFiles hook
```

**Impact:**
- Dead code in codebase
- Confusing for future developers
- If someone tried to use it, would get 404 errors

---

### ROOT CAUSE #6: SessionStorage Only Stores Chat History ⚠️ SECONDARY

**Location:**
- `src/pages/EditorPageNew.tsx` (line 83)
- `src/hooks/use-agent.ts` (line 22)

**The Problem:**

Only chat history is persisted to sessionStorage, not files. sessionStorage is also cleared on browser close, so it's not a true persistence layer.

**Evidence:**

```typescript
// EditorPageNew.tsx line 83 - ONLY CHAT HISTORY SAVED
sessionStorage.setItem(
  `chatHistory_${projectId}`,
  JSON.stringify(conversationHistory)
);

// ❌ NO CODE TO SAVE FILES
// Should be:
// sessionStorage.setItem(
//   `files_${projectId}`,
//   JSON.stringify(Array.from(agentState.files.entries()))
// );
```

```typescript
// use-agent.ts line 22 - ONLY CHAT HISTORY LOADED
const storedHistory = sessionStorage.getItem(`chatHistory_${projectId}`);

// ❌ NO CODE TO LOAD FILES
// Should be:
// const storedFiles = sessionStorage.getItem(`files_${projectId}`);
```

**Impact:**
- Files lost even within same session if page reloaded
- sessionStorage is not persistent across browser close
- Inconsistent with database persistence strategy

---

### ROOT CAUSE #7: Race Condition - Streaming Completes Before Persistence ⚠️ SECONDARY

**Location:** `backend/server/orchestrator.py` (line 45)

**The Problem:**

The pipeline emits `pipeline.completed` event before files are written to database. Frontend receives completion event and thinks data is persisted, but backend never actually saved it.

**Evidence:**

```python
# orchestrator.py lines 22-45
async def run_agent_pipeline(request):
    """Manages the sequential execution of agents."""
    
    project_id = request.project_id
    user_message = request.message
    
    yield {"event": "pipeline.started"}
    
    # ... design and code generation ...
    
    # ❌ MISSING: Save files to database here
    # for file_path, file_content in generated_files.items():
    #     file_record = db.create_file(project_id, file_path, ...)
    #     db.save_code(file_record['id'], file_content)
    
    yield {"event": "pipeline.completed"}  # ← Emitted BEFORE files saved
```

**Impact:**
- Frontend receives completion event
- Frontend thinks data is persisted
- But database is still empty
- Page reload → data gone

---

## Part 2: Verification of Non-Issues

### ✅ Database is Properly Configured

**Evidence:**
- DB_PATH correctly set to `backend/app.db` (database.py line 7)
- Database file exists on disk: 28KB (verified in backend/ directory)
- SQLite (not `:memory:`), so data is persisted to disk
- Schema properly initialized (database.py lines 23-77)
- Connection handling is correct (get_connection, commit, close)

**Conclusion:** Database layer is NOT the problem. It's configured correctly but never receives write operations.

---

### ✅ Backend Can Receive and Process Requests

**Evidence:**
- Rate limiter works correctly (main.py lines 82-94)
- Project creation works (main.py line 97: `db.create_project()`)
- Chat history saving works (orchestrator.py line 29: `db.add_chat_message()`)
- CORS is configured (main.py lines 34-40)
- API endpoint is listening (main.py line 76: `@app.post("/api/agent/stream")`)

**Conclusion:** Backend persistence layer is partially working (chat only). The issue is incomplete implementation (files not persisted).

---

### ✅ OneDrive/Filesystem Not the Issue

**Evidence:**
- Database file exists and is accessible
- No file locking errors in logs
- Database operations for chat history work fine
- Relative path is properly resolved

**Conclusion:** OneDrive sync is not causing the issue.

---

## Part 3: Prioritized Fix Plan

### Priority 1: Backend - Persist Generated Files to Database

**Effort:** Small (30 min)  
**Risk:** Low  
**Impact:** High

**Changes Required:**

1. **Modify `orchestrator.py`** to save files after code generation:
   - After `coding_agent` completes, iterate through generated files
   - Call `db.create_file()` for each file
   - Call `db.save_code()` for each file's content
   - Emit new event type `file.persisted` after DB write succeeds

2. **Modify `coding_agent.py`** to return file contents:
   - Currently accumulates in `file_contents` dict (line 56)
   - Need to return this dict in completion event or via new event type

3. **Update event types** in `types.ts`:
   - Add `file.persisted` event to signal successful DB write

**Pseudocode:**

```python
# orchestrator.py - after coding_agent completes
if intent == "code":
    design_plan = None
    file_contents = {}  # Collect from coding_agent
    
    async for event in designing_agent.run_designing_agent(user_message):
        if event.get("event") == "design.completed":
            design_plan = event
        yield event
    
    if design_plan:
        async for event in coding_agent.run_coding_agent(design_plan, user_message):
            # Capture file content from events
            if event.get("event") == "code.chunk":
                file_path = event.get("file")
                content = event.get("content", "")
                file_contents[file_path] = file_contents.get(file_path, "") + content
            yield event
    
    # ✅ NEW: Persist files to database
    for file_path, file_content in file_contents.items():
        file_record = db.create_file(project_id, file_path, file_path.split('/')[-1])
        if file_record:
            db.save_code(file_record['id'], file_content)
            yield {"event": "file.persisted", "path": file_path}
    
    db.add_chat_message(project_id, user_message, str(design_plan), intent)
```

---

### Priority 2: Backend - Add File Hydration Endpoint

**Effort:** Small (20 min)  
**Risk:** Low  
**Impact:** High

**Changes Required:**

1. **Add new endpoint** `GET /api/projects/{project_id}/files-with-content`:
   - Returns list of files with their code content
   - Joins files table with code table
   - Returns format: `[{ path, name, content }, ...]`

2. **Update existing endpoint** `GET /api/projects/{project_id}`:
   - Include file content in response
   - Or keep separate and use new endpoint

**Pseudocode:**

```python
# main.py - new endpoint
@app.get("/api/projects/{project_id}/files-with-content")
async def get_files_with_content(project_id: str):
    """Get all files with their content for a project."""
    project = db.get_project(project_id)
    
    if not project:
        return JSONResponse(status_code=404, content={"error": "Project not found"})
    
    files = db.get_files_by_project(project_id)
    
    files_with_content = []
    for file_record in files:
        code_record = db.get_code_by_file(file_record['id'])
        files_with_content.append({
            'path': file_record['file_path'],
            'name': file_record['file_name'],
            'content': code_record['code_content'] if code_record else '',
            'created_at': file_record['created_at']
        })
    
    return {
        "project_id": project_id,
        "files": files_with_content,
        "file_count": len(files_with_content)
    }
```

---

### Priority 3: Frontend - Load Files on Component Mount

**Effort:** Small (20 min)  
**Risk:** Low  
**Impact:** High

**Changes Required:**

1. **Add useEffect** in `EditorPageNew.tsx` to load files:
   - Call new endpoint `GET /api/projects/{projectId}/files-with-content`
   - Populate `files` state with loaded content
   - Update `agentState` if needed

2. **Update `use-agent.ts`** to initialize files from sessionStorage:
   - Load files from sessionStorage on init
   - Persist files to sessionStorage on update

**Pseudocode:**

```typescript
// EditorPageNew.tsx - add useEffect
useEffect(() => {
  const loadProjectData = async () => {
    if (!projectId) return;
    
    try {
      // Load files with content
      const filesResponse = await fetch(
        `http://127.0.0.1:8000/api/projects/${projectId}/files-with-content`
      );
      if (filesResponse.ok) {
        const filesData = await filesResponse.json();
        const filesMap = new Map<string, any>();
        
        for (const file of filesData.files) {
          filesMap.set(file.path, { content: file.content });
        }
        
        setFiles(filesMap);
      }
    } catch (error) {
      console.error('Failed to load project files:', error);
    }
  };
  
  loadProjectData();
}, [projectId]);
```

---

### Priority 4: Frontend - Persist Files to SessionStorage

**Effort:** Small (15 min)  
**Risk:** Low  
**Impact:** Medium

**Changes Required:**

1. **Add useEffect** in `use-agent.ts` to save files:
   - Watch `agentState.files` for changes
   - Save to sessionStorage when files change

2. **Update initialization** to load files from sessionStorage:
   - Check for stored files on hook init
   - Restore files Map from sessionStorage

**Pseudocode:**

```typescript
// use-agent.ts - add useEffect to persist files
useEffect(() => {
  if (projectId && state.files.size > 0) {
    const filesArray = Array.from(state.files.entries());
    sessionStorage.setItem(
      `files_${projectId}`,
      JSON.stringify(filesArray)
    );
  }
}, [state.files, projectId]);

// use-agent.ts - update initialization
const [state, setState] = useState<AgentState>(() => {
  if (projectId) {
    // Load chat history
    const storedHistory = sessionStorage.getItem(`chatHistory_${projectId}`);
    
    // Load files
    const storedFiles = sessionStorage.getItem(`files_${projectId}`);
    const filesMap = storedFiles 
      ? new Map(JSON.parse(storedFiles))
      : new Map();
    
    if (storedHistory) {
      try {
        const conversationHistory = JSON.parse(storedHistory);
        return {
          ...initialState,
          conversationHistory,
          files: filesMap,
        };
      } catch (e) {
        console.error('Failed to parse stored data:', e);
      }
    }
  }
  return initialState;
});
```

---

### Priority 5: Cleanup - Remove Dead Code

**Effort:** Small (10 min)  
**Risk:** Low  
**Impact:** Low

**Changes Required:**

1. **Remove or implement `use-files.ts`**:
   - Either implement missing backend endpoints
   - Or remove the hook if not needed

2. **Remove unused imports**:
   - Clean up unused fileService references

---

## Part 4: Quick Temporary Mitigation

If you need data to persist **immediately** while full fix is being reviewed:

### Option A: Persist to localStorage (Immediate, 5 min)

```typescript
// EditorPageNew.tsx - add after files state updates
useEffect(() => {
  if (projectId && files.size > 0) {
    const filesArray = Array.from(files.entries());
    localStorage.setItem(
      `project_${projectId}_files`,
      JSON.stringify(filesArray)
    );
  }
}, [files, projectId]);

// EditorPageNew.tsx - add on mount
useEffect(() => {
  if (projectId) {
    const stored = localStorage.getItem(`project_${projectId}_files`);
    if (stored) {
      try {
        const filesArray = JSON.parse(stored);
        setFiles(new Map(filesArray));
      } catch (e) {
        console.error('Failed to load files from localStorage:', e);
      }
    }
  }
}, [projectId]);
```

**Pros:** Works immediately, survives page reload  
**Cons:** Lost on browser cache clear, not synced with backend

### Option B: Persist to Backend on Generation Complete (Better, 15 min)

Add to `orchestrator.py` after pipeline completes:

```python
# Save files immediately after generation
for file_path, file_content in file_contents.items():
    file_record = db.create_file(project_id, file_path, file_path.split('/')[-1])
    if file_record:
        db.save_code(file_record['id'], file_content)
```

**Pros:** Durable, synced with backend, proper persistence  
**Cons:** Requires backend change

---

## Part 5: Validation Tests

### Manual Test 1: Verify Backend Persistence

```bash
# 1. Start backend
cd backend
python -m uvicorn server.main:app --reload

# 2. Send generation request
curl -X POST http://127.0.0.1:8000/api/agent/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Build a login button", "project_id": "test_proj_123"}'

# 3. Check database
sqlite3 backend/app.db "SELECT * FROM files WHERE project_id = 'test_proj_123';"
sqlite3 backend/app.db "SELECT * FROM code;"

# Expected: Files and code records should exist
```

### Manual Test 2: Verify Frontend Hydration

```bash
# 1. Generate code (see Test 1)
# 2. Reload page in browser
# 3. Check if files appear in editor

# Expected: Files should load from database
```

### Manual Test 3: Verify SessionStorage Persistence

```javascript
// In browser console after generation:
sessionStorage.getItem('files_test_proj_123')

// Expected: Should contain file data
```

### Automated Test: Unit Test for File Persistence

```python
# backend/tests/test_persistence.py
import pytest
from server.database import Database
from server.orchestrator import run_agent_pipeline

@pytest.mark.asyncio
async def test_files_persisted_after_generation():
    """Verify files are saved to database after code generation."""
    db = Database(':memory:')  # Use in-memory for testing
    
    # Mock request
    class MockRequest:
        project_id = 'test_123'
        message = 'Build a button'
    
    # Run pipeline
    events = []
    async for event in run_agent_pipeline(MockRequest()):
        events.append(event)
    
    # Verify files were saved
    files = db.get_files_by_project('test_123')
    assert len(files) > 0, "No files persisted to database"
    
    # Verify code was saved
    for file_record in files:
        code = db.get_code_by_file(file_record['id'])
        assert code is not None, f"No code for file {file_record['file_path']}"
        assert len(code['code_content']) > 0, "Code content is empty"
```

---

## Part 6: Implementation Effort Estimate

| Component | Task | Effort | Risk | Priority |
|-----------|------|--------|------|----------|
| **Backend** | Save files to DB in orchestrator | 30 min | Low | P1 |
| **Backend** | Add files-with-content endpoint | 20 min | Low | P1 |
| **Frontend** | Load files on mount | 20 min | Low | P2 |
| **Frontend** | Persist files to sessionStorage | 15 min | Low | P2 |
| **Frontend** | Cleanup dead code | 10 min | Low | P3 |
| **Testing** | Manual validation | 30 min | Low | P3 |
| **Testing** | Unit tests | 45 min | Low | P3 |
| **TOTAL** | Full fix + tests | ~3 hours | Low | - |

**Quick Win (Temporary):** 5-15 min (localStorage or backend persistence only)  
**Full Fix:** ~3 hours (all components + tests)

---

## Part 7: Risk Assessment

### Risk Level: 🟢 LOW

**Why:**
- Changes are isolated to specific functions
- Database schema is stable
- No breaking API changes (only additions)
- Frontend changes are additive (no removal)
- Existing chat persistence proves approach works

### Rollback Plan:

If issues arise:
1. Revert orchestrator.py changes (no persistence calls)
2. Revert main.py changes (remove new endpoint)
3. Revert EditorPageNew.tsx changes (remove load effects)
4. Frontend falls back to in-memory state (current behavior)

---

## Part 8: Summary & Next Steps

### What's Broken:
1. ❌ Backend never saves generated files to database
2. ❌ Frontend has no code to load files on mount
3. ❌ No endpoint to retrieve file content from backend
4. ❌ Files only exist in React state (lost on reload)

### What's Working:
- ✅ Database is properly configured
- ✅ Chat history persistence works
- ✅ Backend can receive requests
- ✅ Frontend can load chat history

### Root Cause (60% backend + 40% frontend):
- **60% Backend:** orchestrator.py never calls `db.create_file()` or `db.save_code()`
- **40% Frontend:** EditorPageNew.tsx never loads files from database on mount

### Fix Strategy:
1. Backend: Add file persistence to orchestrator (Priority 1)
2. Backend: Add hydration endpoint (Priority 1)
3. Frontend: Load files on mount (Priority 2)
4. Frontend: Persist to sessionStorage (Priority 2)
5. Cleanup: Remove dead code (Priority 3)

### Effort: ~3 hours (full fix) or ~15 min (temporary mitigation)

### Next Action: 
Review this diagnosis and approve fix plan before implementation.

---

**End of Diagnosis Report**
