import asyncio
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.database import db

async def test_frontend_load():
    project_id = 'proj_1763573158247_uprzix6gj'
    
    print(f"Testing frontend load for project {project_id}")
    
    # Load files with content (simulating the frontend API call)
    project = db.get_project(project_id)
    
    if not project:
        print("Project not found")
        return
    
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
    
    result = {
        "project_id": project_id,
        "files": files_with_content,
        "file_count": len(files_with_content)
    }
    
    print(f"Loaded {result['file_count']} files:")
    for file in result['files']:
        print(f"  - {file['path']}: {len(file['content'])} characters")
    
    # Save to a JSON file that we can use for testing
    with open('test_frontend_data.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\nData saved to test_frontend_data.json")

if __name__ == "__main__":
    asyncio.run(test_frontend_load())