# Issue Breakdown: Why Generation Doesn't Happen

## The Critical Flow Break

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User types prompt: "Build a login button"                  │
│     ↓                                                           │
│  2. User clicks "Generate" button                              │
│     ↓                                                           │
│  3. handleGenerate() is called                                 │
│     ↓                                                           │
│  ❌ PROBLEM: No API call is made!                              │
│     ↓                                                           │
│  4. Frontend just navigates to /editor                         │
│     ↓                                                           │
│  5. EditorPageNew loads with EMPTY state                       │
│     ↓                                                           │
│  6. User sees blank editor (no generation)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Code Evidence: The Missing API Call

### **Index.tsx (lines 43-51) - THE CULPRIT**

```typescript
const handleGenerate = () => {
  if (!prompt.trim()) return;
  setIsLoading(true);
  // Simulate a delay then navigate to the editor page
  setTimeout(() => {
    navigate(`/editor`);  // ← ONLY THIS HAPPENS
    setIsLoading(false);
  }, 1000);
};
```

**What's Missing:**
```typescript
// This SHOULD be called but ISN'T:
sendMessage(prompt);  // ← From useAgent hook
```

---

## What SHOULD Happen vs What ACTUALLY Happens

### **EXPECTED FLOW (Code Intent)**
```
Index Page
  ↓
handleGenerate()
  ├─ sendMessage(prompt)  ← Should call this
  │  └─ POST /api/agent/stream
  │     └─ Backend receives message
  │        └─ Orchestrator runs
  │           ├─ IntentClassifier
  │           ├─ DesigningAgent
  │           └─ CodingAgent
  │              └─ Streams events back
  │                 └─ Frontend updates state
  │                    └─ Editor shows files & code
  ↓
navigate('/editor')
  ↓
EditorPageNew (with generated files)
```

### **ACTUAL FLOW (Current Behavior)**
```
Index Page
  ↓
handleGenerate()
  ├─ (prompt is ignored)
  ├─ setTimeout(1000ms)
  │  └─ navigate('/editor')  ← Only this happens
  │     └─ NO API CALL
  │        └─ Backend receives NOTHING
  │           └─ No orchestrator execution
  │              └─ No events streamed
  │                 └─ Frontend state stays empty
  ↓
EditorPageNew (with NO files, NO code)
  ↓
User sees blank editor
```

---

## The Two-Part Problem

### **PART 1: Frontend Doesn't Send Request (CRITICAL)**

**File:** `src/pages/Index.tsx`
**Function:** `handleGenerate()`
**Issue:** Navigates without sending prompt to backend

**Current Code:**
```typescript
const handleGenerate = () => {
  if (!prompt.trim()) return;
  setIsLoading(true);
  setTimeout(() => {
    navigate(`/editor`);  // ← Navigates immediately
    setIsLoading(false);
  }, 1000);
};
```

**Missing:**
- No call to `sendMessage(prompt)`
- No API request to backend
- Prompt data is lost

---

### **PART 2: Event Type Mismatch (HIGH PRIORITY)**

Even if Part 1 is fixed, Part 2 will cause failures.

**Backend Events Emitted:**
```
code.started
code.file_started { file: "lib/main.dart" }
code.chunk { content: "import 'package:flutter/material.dart';", file: "lib/main.dart" }
code.completed { files_generated: 5 }
```

**Frontend Event Handlers (use-agent.ts):**
```typescript
case 'file.create':      // ❌ Backend doesn't emit this
case 'file.chunk':       // ❌ Backend emits 'code.chunk' instead
case 'file.narrative':   // ❌ Backend doesn't emit this
```

**Result:** Frontend won't recognize code generation events

---

## Backend Status: ✅ WORKING

The backend is **NOT the problem**. Proof:

### **Test the Backend Directly**
```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn server.main:app --reload

# Terminal 2: Send test request
curl -X POST http://127.0.0.1:8000/api/agent/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Build a login button"}'
```

**Expected Output:**
```
data: {"event": "pipeline.started"}
data: {"event": "intent.classified", "intent": "code"}
data: {"event": "design.started"}
data: {"event": "design.phase", "details": "Analyzing request..."}
data: {"event": "design.phase", "details": "Outlining file structure..."}
data: {"event": "design.completed", "files": ["lib/main.dart", ...]}
data: {"event": "code.started"}
data: {"event": "code.file_started", "file": "lib/main.dart"}
data: {"event": "code.chunk", "content": "import 'package:flutter/material.dart';", "file": "lib/main.dart"}
...
data: {"event": "pipeline.completed"}
```

**The backend WILL respond correctly.** The problem is the frontend never makes this request.

---

## Why You See Zero Backend Activity

**Backend Console Shows Nothing Because:**
1. ❌ No HTTP request reaches the backend
2. ❌ FastAPI never receives POST to `/api/agent/stream`
3. ❌ Orchestrator never executes
4. ❌ No agents run
5. ❌ No logs are printed

**You would see this IF the frontend sent the request:**
```
INFO:     Received request: Build a login button...
INFO:     F3 Platform Backend started
INFO:     Model: gemini-2.5-flash
```

---

## The Fix (High Level)

### **Fix 1: Index.tsx - Send Prompt (CRITICAL)**
```typescript
// Need to:
// 1. Import useAgent hook
// 2. Call sendMessage(prompt) in handleGenerate
// 3. Pass prompt to editor page OR wait for agent to start
```

### **Fix 2: use-agent.ts - Map Events (HIGH)**
```typescript
// Update event handlers to recognize:
// - code.started
// - code.file_started
// - code.chunk
// - code.completed
```

### **Fix 3: EditorPageNew - Initialize Agent (MEDIUM)**
```typescript
// Need to:
// 1. Get prompt from route params or context
// 2. Call sendMessage on component mount
// 3. Display streaming indicators
```

---

## Summary Table

| Layer | Component | Status | Issue |
|-------|-----------|--------|-------|
| **Frontend** | Index.tsx | ❌ BROKEN | Doesn't send prompt to backend |
| **Frontend** | use-agent.ts | ❌ BROKEN | Event handlers don't match backend |
| **Frontend** | EditorPageNew | ⚠️ PARTIAL | No initial message trigger |
| **Backend** | Orchestrator | ✅ OK | Works correctly |
| **Backend** | Agents | ✅ OK | All implemented |
| **Backend** | Config | ✅ OK | Loads correctly |
| **Backend** | Prompts | ✅ OK | Centralized system works |
| **Network** | CORS | ✅ OK | Configured correctly |
| **Network** | API Endpoint | ✅ OK | Listening on 8000 |

---

## Conclusion

**The backend is ready and waiting for requests that never come.**

The frontend's Index page captures the user's prompt but never sends it to the backend. It just navigates to the editor page with no data, leaving the backend completely idle.

This is a **frontend-only issue** with two parts:
1. **Critical:** No API request is made
2. **High:** Event types don't match when request is eventually made
