# Diagnostic Checklist - Data Persistence Issue

## Quick Test: Is Data Being Saved?

### Test 1: Check Database After Generation
```bash
sqlite3 backend/app.db "SELECT COUNT(*) FROM files;"
```
- If 0: Files NOT being saved to database
- If > 0: Files ARE being saved

### Test 2: Check Backend Endpoint
```bash
curl http://127.0.0.1:8000/api/projects/YOUR_PROJECT_ID/files-with-content
```
- Should return files with content
- If empty array: No files in database

### Test 3: Check Browser Console
Press F12 → Console tab → Look for errors after generation

### Test 4: Check Network Tab
Press F12 → Network tab → Generate code → Look for:
- POST to `/api/agent/stream` - should succeed
- GET to `/api/projects/.../files-with-content` - should return files

## Most Likely Issue

**The backend is NOT saving files to the database.**

Why? The `file_contents` dictionary in orchestrator.py only captures content from `code.chunk` events. But if the coding_agent is NOT emitting `code.chunk` events with the `file` parameter, nothing gets captured.

## Verification

Check if coding_agent is emitting events correctly:

```python
# In orchestrator.py, add logging:
if event.get("event") == "code.chunk":
    print(f"DEBUG: Captured file={event.get('file')}, content_len={len(event.get('content', ''))}")
```

Then generate code and check backend console output.
