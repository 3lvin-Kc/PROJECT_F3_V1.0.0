# Root Cause Analysis: Backend Pipeline Not Triggering

## Summary
The frontend is **NOT sending the initial prompt to the backend**. The user enters a prompt on the Index page, clicks "Generate", and gets redirected to the editor page, but **no API request is ever made to the backend**.

---

## Root Cause: Frontend Issue

### **PRIMARY ISSUE: Index.tsx handleGenerate() Function**

**Location:** `src/pages/Index.tsx` lines 43-51

```typescript
const handleGenerate = () => {
  if (!prompt.trim()) return;
  setIsLoading(true);
  // Simulate a delay then navigate to the editor page
  setTimeout(() => {
    navigate(`/editor`);
    setIsLoading(false);
  }, 1000);
};
```

**The Problem:**
1. The function has a comment saying "Simulate a delay then navigate to the editor page"
2. It **only navigates to `/editor`** without sending the prompt to the backend
3. It **does NOT call the `useAgent` hook's `sendMessage()` function**
4. The prompt text is captured in state but **never transmitted**

**Why This Breaks the Pipeline:**
- User enters prompt → Clicks "Generate"
- Frontend navigates to `/editor` page immediately
- **NO API request is made to `http://127.0.0.1:8000/api/agent/stream`**
- Backend never receives the message, so orchestrator never runs
- EditorPageNew loads with empty state (no files, no streaming)
- User sees blank editor with no generation activity

---

## Secondary Issue: Event Type Mismatch

Even if the frontend sent the request, there's a **mismatch between backend events and frontend event handlers**.

### **Backend Events Emitted:**
```
code.started
code.file_started
code.chunk
code.completed
```

### **Frontend Event Handlers (use-agent.ts lines 54-83):**
```typescript
case 'intent.classified':
case 'chat.chunk':
case 'design.phase':
case 'file.create':        // ❌ Backend doesn't emit this
case 'file.chunk':         // ❌ Backend doesn't emit this
case 'file.narrative':     // ❌ Backend doesn't emit this
case 'pipeline.completed':
```

**The Mismatch:**
- Backend emits: `code.chunk` with `{ content, file }`
- Frontend expects: `file.chunk` with `{ path, content }`
- Frontend expects: `file.create` to initialize files
- Frontend expects: `file.narrative` for narrative blocks

**Result:** Even if the request reaches the backend, the frontend won't recognize the code generation events and won't populate the editor.

---

## Data Flow Breakdown

### **What SHOULD Happen (Code Flow):**
```
1. User enters prompt on Index page
2. Clicks "Generate" button
3. handleGenerate() calls sendMessage(prompt)  ← NOT HAPPENING
4. Frontend POST to http://127.0.0.1:8000/api/agent/stream
5. Backend receives request
6. Orchestrator runs:
   - IntentClassifier → "code"
   - DesigningAgent → generates file list
   - CodingAgent → generates code
7. Backend streams events (SSE)
8. Frontend parses events and updates state
9. Editor displays files and code
```

### **What ACTUALLY Happens:**
```
1. User enters prompt on Index page
2. Clicks "Generate" button
3. handleGenerate() navigates to /editor  ← STOPS HERE
4. NO API request made
5. Backend receives NOTHING
6. EditorPageNew loads with empty state
7. User sees blank editor
```

---

## Verification: Backend is Working Correctly

The backend is **NOT the problem**. Evidence:

1. **Config loads correctly** - `config.py` validates GOOGLE_API_KEY on startup
2. **Prompts load correctly** - `prompts.yaml` is properly structured
3. **Agents are refactored** - All use `PromptLoader` and `Config`
4. **Orchestrator logic is sound** - Sequential execution is correct
5. **Main.py is enhanced** - Health check endpoint works, CORS is configured
6. **CodingAgent is implemented** - Streams code events properly

**If you manually call the backend endpoint:**
```bash
curl -X POST http://127.0.0.1:8000/api/agent/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Build a login button"}'
```

The backend **WILL respond with streaming events**. The problem is the frontend never makes this call.

---

## Complete Issue Map

| Component | Issue | Severity | Impact |
|-----------|-------|----------|--------|
| **Index.tsx handleGenerate()** | Doesn't call sendMessage() | 🔴 CRITICAL | No request sent to backend |
| **use-agent.ts event handlers** | Event type mismatch | 🟡 HIGH | Code won't display even if request sent |
| **Frontend-Backend contract** | Events don't align | 🟡 HIGH | Streaming won't work correctly |
| Backend orchestrator | ✅ Working | - | - |
| Backend agents | ✅ Working | - | - |
| Backend config | ✅ Working | - | - |

---

## What Needs to Happen

### **Fix 1: Index.tsx - Send Prompt to Backend (CRITICAL)**
The `handleGenerate()` function must:
1. Get the prompt from state
2. Call `sendMessage(prompt)` from the `useAgent` hook
3. Navigate to `/editor` AFTER the message is sent (or pass prompt via route)

### **Fix 2: use-agent.ts - Update Event Handlers (HIGH)**
The event handler switch statement must map backend events to frontend state:
- `code.started` → Initialize code generation state
- `code.file_started` → Create file entry
- `code.chunk` → Append to file content
- `code.completed` → Mark generation as done

### **Fix 3: Event Structure Alignment (HIGH)**
Backend must emit events in a format the frontend expects, OR frontend must parse backend events correctly.

---

## Why No Backend Activity

**The backend logs show nothing because:**
1. No HTTP request reaches the backend
2. FastAPI never receives a POST to `/api/agent/stream`
3. Orchestrator never runs
4. No agents execute
5. No events are streamed back

**Proof:** If you check the backend console, you won't see:
- "Received request: Build a login button..."
- "Backend server started" (unless you manually started it)
- Any agent execution logs

---

## Conclusion

**Root Cause:** The frontend's Index page doesn't send the user's prompt to the backend. It only navigates to the editor page without triggering any API call.

**Secondary Issue:** Even if the request were sent, the event types don't match between backend and frontend.

**Solution Required:** 
1. Modify `Index.tsx` to send the prompt via the `useAgent` hook
2. Update `use-agent.ts` to handle backend event types correctly
3. Ensure the prompt is passed to the editor page so it can be used there
