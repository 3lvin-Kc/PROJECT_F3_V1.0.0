# Frontend Rate Limit Handling

## Current Issue

When the backend returns a 429 error, the frontend doesn't handle it gracefully. The `use-agent.ts` hook needs to:

1. Detect 429 errors
2. Show user-friendly error message
3. Display retry countdown
4. Prevent further requests until rate limit resets

---

## Recommended Implementation

### Update `use-agent.ts`

Add error handling for rate limit responses:

```typescript
const sendMessage = async (message: string) => {
  setState(initialState);
  setState(prev => ({ ...prev, isStreaming: true }));

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    // Handle 429 Rate Limit Error
    if (response.status === 429) {
      const errorData = await response.json();
      const retryAfter = errorData.retry_after || 60;
      
      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: `Rate limit exceeded. Please wait ${retryAfter} seconds before trying again.`,
      }));
      
      // Optionally: Show countdown timer
      startRetryCountdown(retryAfter);
      return;
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) return;

    // ... rest of streaming logic
  } catch (error) {
    setState(prev => ({
      ...prev,
      error: error instanceof Error ? error.message : 'Failed to connect to the agent service.',
    }));
  } finally {
    setState(prev => ({ ...prev, isStreaming: false }));
  }
};
```

### Add Retry Countdown

```typescript
const [retryCountdown, setRetryCountdown] = useState<number | null>(null);

const startRetryCountdown = (seconds: number) => {
  setRetryCountdown(seconds);
  
  const interval = setInterval(() => {
    setRetryCountdown(prev => {
      if (prev === null || prev <= 1) {
        clearInterval(interval);
        return null;
      }
      return prev - 1;
    });
  }, 1000);
};
```

### Update AgentState Type

Add retry countdown to state:

```typescript
export interface AgentState {
  isStreaming: boolean;
  intent: 'chat' | 'code' | null;
  chatMessage: string;
  narrativeBlocks: { id: number; type: 'narrative'; content: string }[];
  files: Map<string, string>;
  error: string | null;
  currentDesignPhase: string | null;
  activeFile: string | null;
  retryCountdown: number | null;  // ← Add this
}
```

---

## Frontend UI Changes

### Show Error Message

In `AIAssistantPanel.tsx` or `Index.tsx`:

```typescript
{agentState.error && (
  <div className="p-3 bg-red-100 dark:bg-red-900/50 rounded-lg text-sm border border-red-300">
    <p className="font-semibold text-red-800 dark:text-red-200">Error</p>
    <p className="text-red-700 dark:text-red-300">{agentState.error}</p>
  </div>
)}
```

### Show Retry Countdown

```typescript
{agentState.retryCountdown !== null && (
  <div className="p-3 bg-yellow-100 dark:bg-yellow-900/50 rounded-lg text-sm border border-yellow-300">
    <p className="font-semibold text-yellow-800 dark:text-yellow-200">
      Rate Limited
    </p>
    <p className="text-yellow-700 dark:text-yellow-300">
      Please wait {agentState.retryCountdown} seconds before trying again...
    </p>
  </div>
)}
```

### Disable Generate Button

```typescript
<Button 
  onClick={handleGenerate}
  disabled={
    !prompt.trim() || 
    isLoading || 
    agentState.retryCountdown !== null  // ← Disable during countdown
  }
  className={...}
>
  {agentState.retryCountdown !== null ? (
    `Wait ${agentState.retryCountdown}s`
  ) : isLoading ? (
    <>
      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
      Generating...
    </>
  ) : (
    <>
      Generate
      <ArrowRight className="w-4 h-4 ml-2" />
    </>
  )}
</Button>
```

---

## Testing Rate Limits

### Test 1: Check Rate Limit Status

```bash
curl http://127.0.0.1:8000/api/rate-limit-status
```

### Test 2: Trigger Rate Limit

Make 10 requests rapidly:

```bash
for i in {1..10}; do
  curl -X POST http://127.0.0.1:8000/api/agent/stream \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}' &
done
```

The 11th request should return 429.

### Test 3: Verify Countdown

After hitting rate limit, wait 60 seconds and try again. It should work.

---

## Error Response Format

When rate limit is exceeded:

```json
{
  "status": 429,
  "error": "Rate limit exceeded",
  "message": "Rate limit exceeded: 10/10 requests per minute",
  "retry_after": 60
}
```

Frontend should:
1. Extract `retry_after` value
2. Show countdown timer
3. Disable Generate button
4. Allow user to retry after countdown

---

## Best Practices

1. **Show Clear Error Messages**: Users should understand why they can't generate
2. **Display Countdown**: Show exactly how long they need to wait
3. **Disable Button**: Prevent accidental repeated requests
4. **Log Errors**: Track rate limit hits for debugging
5. **Graceful Degradation**: Don't crash, just show error

---

## Future Improvements

1. **Client-Side Rate Limiting**: Prevent requests before they reach backend
2. **Persistent Storage**: Remember rate limit state across page reloads
3. **User Feedback**: Show usage statistics in UI
4. **Upgrade Prompt**: Suggest upgrading to paid tier when hitting limits
5. **Request Queuing**: Queue requests and process them sequentially

