# User Flow & Rate Limiting System

## Part 1: Exact Flow When User Clicks "Generate"

### Timeline for: "i want to discuss about input widgets...."

```
┌─────────────────────────────────────────────────────────────────┐
│                    INDEX PAGE (Initial State)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  T=0ms: User types prompt                                       │
│  T=0ms: User clicks "Generate" button                           │
│         └─ handleGenerate() called (Index.tsx:45)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              SENDING MESSAGE TO BACKEND                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  T=0ms: await sendMessage(prompt)  ← Starts                    │
│         ├─ POST /api/agent/stream                              │
│         ├─ Body: { message: "i want to discuss..." }           │
│         └─ Backend receives request                            │
│                                                                 │
│  Backend Processing:                                            │
│  ├─ Rate limiter checks: allowed? YES                          │
│  ├─ Orchestrator starts                                        │
│  ├─ IntentClassifier runs (Gemini API call #1)                │
│  │  └─ Returns: "chat"                                         │
│  ├─ ChatAgent runs (Gemini API call #2, STREAMING)            │
│  │  ├─ Sends prompt to Gemini                                 │
│  │  ├─ Gemini generates response token-by-token               │
│  │  ├─ Backend receives tokens from Gemini                    │
│  │  ├─ Backend emits SSE events                               │
│  │  └─ Frontend receives events                               │
│  │                                                             │
│  │  Token Stream from Gemini:                                 │
│  │  ├─ "An" → SSE event → Frontend receives                  │
│  │  ├─ " input" → SSE event → Frontend receives              │
│  │  ├─ " field" → SSE event → Frontend receives              │
│  │  ├─ " is" → SSE event → Frontend receives                 │
│  │  └─ ...                                                    │
│  │                                                             │
│  └─ Frontend state updates in real-time                        │
│     ├─ chatMessage = "An"                                      │
│     ├─ chatMessage = "An input"                                │
│     ├─ chatMessage = "An input field"                          │
│     ├─ chatMessage = "An input field is"                       │
│     └─ ...                                                     │
│                                                                 │
│  T=100ms: First event arrives (pipeline.started)               │
│  T=100ms: sendMessage() returns (streaming has started)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              NAVIGATION TO EDITOR PAGE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  T=100ms: navigate(`/editor`, { state: { prompt } })           │
│           ├─ URL changes to /editor                            │
│           ├─ EditorPageNew component mounts                    │
│           ├─ useAgent hook initialized                         │
│           │  └─ Already has streaming state from Index page    │
│           ├─ AIAssistantPanel renders                          │
│           └─ User sees editor page                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│         STREAMING CONTINUES IN BACKGROUND                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  T=100-5000ms: Backend continues streaming tokens              │
│  ├─ Frontend receives: chat.chunk events                       │
│  ├─ Updates state: chatMessage += token                        │
│  ├─ React re-renders AIAssistantPanel                          │
│  └─ User sees text appearing word-by-word                      │
│                                                                 │
│  UI Display:                                                    │
│  ├─ "An"                                                        │
│  ├─ "An input"                                                  │
│  ├─ "An input field"                                            │
│  ├─ "An input field is"                                         │
│  ├─ "An input field is a fundamental..."                        │
│  └─ ...                                                        │
│                                                                 │
│  T=5000ms: Backend finishes streaming                          │
│  ├─ Emits: pipeline.completed                                  │
│  ├─ Frontend sets: isStreaming = false                         │
│  └─ Chat message fully displayed                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Points About the Flow

1. **Navigation Happens Immediately**: User sees editor page after ~100ms
2. **Streaming Continues in Background**: Response appears in real-time
3. **No File Generation for Chat**: Only ChatAgent runs, no files created
4. **Shared State**: EditorPageNew reuses the agent state from Index page

---

## Part 2: Rate Limiting System

### What Was Added

**File:** `backend/server/rate_limiter.py`

A rate limiter that:
- Tracks requests per client IP
- Enforces minute-level limits (10 requests/min for free tier)
- Enforces hour-level limits (100 requests/hour for free tier)
- Uses token bucket algorithm
- Automatically cleans up old request records

### How It Works

```python
# Initialize with free tier limits
rate_limiter = get_rate_limiter(
    requests_per_minute=10,
    requests_per_hour=100
)

# Check if request is allowed
allowed, message = rate_limiter.is_allowed(client_ip)

if not allowed:
    return 429 error with retry info
```

### Integration in main.py

**Endpoint:** `POST /api/agent/stream`

```python
@app.post("/api/agent/stream")
async def agent_stream_endpoint(request: AgentRequest, http_request: Request):
    client_ip = http_request.client.host
    
    # Check rate limit BEFORE processing
    allowed, message = rate_limiter.is_allowed(client_ip)
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": message,
                "retry_after": 60,
            },
        )
    
    # Process request if allowed
    return StreamingResponse(agent_event_stream(request), ...)
```

### New Endpoint: Rate Limit Status

**Endpoint:** `GET /api/rate-limit-status`

Check your current rate limit status:

```bash
curl http://127.0.0.1:8000/api/rate-limit-status
```

Response:
```json
{
  "client_ip": "127.0.0.1",
  "rate_limits": {
    "minute": {
      "used": 2,
      "limit": 10,
      "remaining": 8
    },
    "hour": {
      "used": 5,
      "limit": 100,
      "remaining": 95
    }
  }
}
```

---

## How Rate Limiting Prevents Quota Exhaustion

### Before Rate Limiting

```
User makes 5 prompts in quick succession:
├─ Prompt 1: IntentClassifier (1) + ChatAgent (1) = 2 API calls
├─ Prompt 2: IntentClassifier (1) + ChatAgent (1) = 2 API calls
├─ Prompt 3: IntentClassifier (1) + ChatAgent (1) = 2 API calls
├─ Prompt 4: IntentClassifier (1) + ChatAgent (1) = 2 API calls
├─ Prompt 5: IntentClassifier (1) + ChatAgent (1) = 2 API calls
└─ Total: 10 API calls → QUOTA EXCEEDED ❌
```

### After Rate Limiting

```
User makes 5 prompts in quick succession:
├─ Prompt 1: ALLOWED (1/10 used) ✅
├─ Prompt 2: ALLOWED (2/10 used) ✅
├─ Prompt 3: ALLOWED (3/10 used) ✅
├─ Prompt 4: ALLOWED (4/10 used) ✅
├─ Prompt 5: ALLOWED (5/10 used) ✅
├─ Prompt 6: BLOCKED - Rate limit exceeded ❌
│  └─ Error: "Rate limit exceeded: 5/10 requests per minute"
│  └─ Retry after: 60 seconds
└─ After 60 seconds: Counter resets, can make 10 more requests
```

---

## Frontend Error Handling

When rate limit is exceeded, frontend receives:

```json
{
  "status": 429,
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded: 5/10 requests per minute",
  "retry_after": 60
}
```

Frontend should:
1. Show error message to user
2. Disable Generate button
3. Show countdown timer (60 seconds)
4. Re-enable button after countdown

---

## Configuration

### To Change Rate Limits

Edit `backend/server/main.py` line 23:

```python
# For paid tier (higher limits)
rate_limiter = get_rate_limiter(
    requests_per_minute=100,    # Increase this
    requests_per_hour=1000      # Increase this
)
```

### Common Configurations

**Free Tier (Current):**
```python
requests_per_minute=10
requests_per_hour=100
```

**Paid Tier (Recommended):**
```python
requests_per_minute=100
requests_per_hour=1000
```

**Development (Testing):**
```python
requests_per_minute=1000
requests_per_hour=10000
```

---

## Summary

| Aspect | Details |
|--------|---------|
| **Flow** | User clicks Generate → Message sent to backend → Navigation to editor → Streaming continues in background |
| **Navigation Timing** | Happens after ~100ms (as soon as first event arrives) |
| **Streaming** | Continues in real-time while user is in editor |
| **Rate Limiting** | Checks per client IP, enforces minute and hour limits |
| **Free Tier** | 10 requests/min, 100 requests/hour |
| **Quota Exhaustion** | Prevented by rate limiter returning 429 errors |
| **Status Endpoint** | GET /api/rate-limit-status shows current usage |

