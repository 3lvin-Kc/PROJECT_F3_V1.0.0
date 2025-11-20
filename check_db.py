import sqlite3
import os

# Connect to the database
db_path = os.path.join('backend', 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check projects
print("=== Projects ===")
cursor.execute('SELECT * FROM projects')
projects = cursor.fetchall()
for project in projects:
    print(project)

# Check files for the specific project
print("\n=== Files for project proj_1763573158247_uprzix6gj ===")
cursor.execute('SELECT * FROM files WHERE project_id = ?', ('proj_1763573158247_uprzix6gj',))
files = cursor.fetchall()
print(f"Number of files: {len(files)}")
for file in files:
    print(file)

# Check code for those files
print("\n=== Code entries ===")
for file in files:
    file_id = file[0]
    print(f"File ID {file_id}:")
    cursor.execute('SELECT * FROM code WHERE file_id = ?', (file_id,))
    code_entries = cursor.fetchall()
    for code in code_entries:
        print(f"  Code ID {code[0]}: {len(code[2])} characters")

# Check chat history for the specific project
print("\n=== Chat history for project proj_1763573158247_uprzix6gj ===")
cursor.execute('SELECT * FROM chat_history WHERE project_id = ?', ('proj_1763573158247_uprzix6gj',))
chat_history = cursor.fetchall()
for chat in chat_history:
    print(chat)

conn.close()