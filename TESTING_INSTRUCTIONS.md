# Testing Instructions - Session Data Persistence Fix

## What Was Fixed

✅ **Backend** (`orchestrator.py`): Now saves generated files to SQLite database  
✅ **Backend** (`main.py`): Added endpoint to retrieve files with content  
✅ **Frontend** (`EditorPageNew.tsx`): Loads files from database on mount  
✅ **Frontend** (`use-agent.ts`): Persists files to sessionStorage  

---

## How to Test

### Step 1: Start Backend with Debugging

```bash
cd backend
python -m uvicorn server.main:app --reload
```

**Watch for DEBUG messages in console:**
```
DEBUG: Captured code chunk for lib/main.dart, total size now: 150 bytes
DEBUG: Persisting 3 files for project proj_123
DEBUG: Saving file lib/main.dart with 1500 bytes
DEBUG: Successfully persisted lib/main.dart
```

If you DON'T see these messages, the persistence code is not running.

---

### Step 2: Generate Code in Frontend

1. Open http://localhost:5173 (or your dev server)
2. Enter a prompt: "Build a simple hello world button"
3. Click "Generate"
4. Wait for code to appear in editor
5. **Check backend console** for DEBUG messages

---

### Step 3: Verify Files Saved to Database

```bash
# In a new terminal, check database
sqlite3 backend/app.db "SELECT project_id, file_path, file_name FROM files LIMIT 5;"

# Expected output:
# proj_1234567890_abc|lib/main.dart|main.dart
# proj_1234567890_abc|lib/widgets.dart|widgets.dart
```

If empty: **Files NOT being saved** → Check backend DEBUG output

---

### Step 4: Test Hydration Endpoint

```bash
# Replace YOUR_PROJECT_ID with actual ID from URL
curl http://127.0.0.1:8000/api/projects/YOUR_PROJECT_ID/files-with-content

# Expected response:
# {
#   "project_id": "YOUR_PROJECT_ID",
#   "files": [
#     {
#       "path": "lib/main.dart",
#       "name": "main.dart",
#       "content": "import 'package:flutter/material.dart';...",
#       "created_at": "2025-11-20T..."
#     }
#   ],
#   "file_count": 1
# }
```

If `files` array is empty: **Files not in database** → Check Step 3

---

### Step 5: Refresh Page and Verify Data Persists

1. After generation, note the project ID from URL: `?projectId=proj_123`
2. **Refresh the page** (Ctrl+R or Cmd+R)
3. **Check if files appear in editor**

**Expected behavior:**
- Files load from database
- Chat history appears
- Editor shows generated code

**If files disappear:**
- Check browser console (F12) for errors
- Check Network tab for failed requests
- Verify endpoint is returning data (Step 4)

---

## Debugging Checklist

### ❌ Files disappear on refresh

**Check these in order:**

1. **Backend saving files?**
   ```bash
   sqlite3 backend/app.db "SELECT COUNT(*) FROM files;"
   ```
   - If 0: Backend not saving → Check DEBUG output in Step 1

2. **Endpoint returning files?**
   ```bash
   curl http://127.0.0.1:8000/api/projects/YOUR_ID/files-with-content
   ```
   - If empty array: No files in DB → Check Step 1

3. **Frontend calling endpoint?**
   - Open DevTools (F12) → Network tab
   - Refresh page
   - Look for GET request to `/api/projects/.../files-with-content`
   - If not there: Frontend not calling it → Check EditorPageNew.tsx line 86

4. **Frontend receiving data?**
   - In DevTools Console, after refresh:
   ```javascript
   sessionStorage.getItem('files_YOUR_PROJECT_ID')
   ```
   - If null: Data not being stored → Check EditorPageNew.tsx line 99

---

## Expected Debug Output

### During Generation (Backend Console)

```
DEBUG: Captured code chunk for lib/main.dart, total size now: 150 bytes
DEBUG: Captured code chunk for lib/main.dart, total size now: 300 bytes
DEBUG: Captured code chunk for lib/widgets.dart, total size now: 200 bytes
DEBUG: Persisting 2 files for project proj_1234567890_abc
DEBUG: Saving file lib/main.dart with 300 bytes
DEBUG: Successfully persisted lib/main.dart
DEBUG: Saving file lib/widgets.dart with 200 bytes
DEBUG: Successfully persisted lib/widgets.dart
```

### After Page Refresh (Browser Console)

Should NOT see errors. Should see files load silently.

---

## If Still Not Working

1. **Clear browser cache** (Ctrl+Shift+Delete)
2. **Restart backend** (Ctrl+C, then restart)
3. **Delete database** (rm backend/app.db) to start fresh
4. **Check for TypeScript errors** (npm run build)
5. **Check backend logs** for any exceptions

---

## Success Criteria

✅ Generate code → Files appear in editor  
✅ Refresh page → Files still there  
✅ Close browser → Reopen → Files still there (from database)  
✅ Backend console shows DEBUG messages during generation  
✅ Database has files after generation  
✅ Endpoint returns files with content
