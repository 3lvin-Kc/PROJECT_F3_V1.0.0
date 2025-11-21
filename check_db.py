import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Look for actual Flutter code (Dart files with Flutter imports)
print("Searching for actual Flutter code (Dart files with Flutter content):")
cursor.execute("SELECT c.id, c.file_id, c.code_content, f.file_path, f.project_id FROM code c JOIN files f ON c.file_id = f.id WHERE f.file_path LIKE '%.dart' AND c.code_content LIKE '%flutter%' LIMIT 5;")
flutter_code_rows = cursor.fetchall()

if not flutter_code_rows:
    print("No Flutter code found with 'flutter' keyword. Let's check for Dart code with common Flutter patterns:")
    cursor.execute("SELECT c.id, c.file_id, c.code_content, f.file_path, f.project_id FROM code c JOIN files f ON c.file_id = f.id WHERE f.file_path LIKE '%.dart' AND (c.code_content LIKE '%import%package:flutter%' OR c.code_content LIKE '%StatelessWidget%' OR c.code_content LIKE '%StatefulWidget%') LIMIT 5;")
    flutter_code_rows = cursor.fetchall()

for row in flutter_code_rows:
    print(f"\nCode ID: {row[0]}, File ID: {row[1]}")
    print(f"File Path: {row[3]}, Project ID: {row[4]}")
    print(f"Code content (first 500 chars):\n{row[2][:500] if row[2] else 'None'}...")
    if len(row[2]) > 500:
        print(f"... (truncated, total length: {len(row[2])} characters)")
    print("="*80)

# Check how many total Dart files we have
cursor.execute("SELECT COUNT(*) FROM files WHERE file_path LIKE '%.dart';")
dart_file_count = cursor.fetchone()[0]
print(f"\nTotal Dart files in database: {dart_file_count}")

# Check how many code entries we have
cursor.execute("SELECT COUNT(*) FROM code;")
code_entry_count = cursor.fetchone()[0]
print(f"Total code entries in database: {code_entry_count}")

conn.close()