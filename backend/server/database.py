import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'app.db')


class Database:
    """SQLite database manager for the F3 platform."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chat History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                user_prompt TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                intent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        ''')
        
        # Files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        ''')
        
        # Code table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                code_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== Projects ====================
    
    def create_project(self, project_id: str) -> Dict[str, Any]:
        """Create a new project."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO projects (project_id)
                VALUES (?)
            ''', (project_id,))
            conn.commit()
            
            # Return the created project
            cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.IntegrityError:
            # Project already exists
            cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by project_id."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    # ==================== Chat History ====================
    
    def add_chat_message(self, project_id: str, user_prompt: str, ai_response: str, intent: str = None) -> Dict[str, Any]:
        """Add a chat message to history."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history (project_id, user_prompt, ai_response, intent)
            VALUES (?, ?, ?, ?)
        ''', (project_id, user_prompt, ai_response, intent))
        
        conn.commit()
        chat_id = cursor.lastrowid
        
        cursor.execute('SELECT * FROM chat_history WHERE id = ?', (chat_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_chat_history(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all chat messages for a project."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM chat_history 
            WHERE project_id = ? 
            ORDER BY timestamp ASC
        ''', (project_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ==================== Files ====================
    
    def create_file(self, project_id: str, file_path: str, file_name: str) -> Dict[str, Any]:
        """Create a file record."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO files (project_id, file_path, file_name)
            VALUES (?, ?, ?)
        ''', (project_id, file_path, file_name))
        
        conn.commit()
        file_id = cursor.lastrowid
        
        cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_files_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all files for a project."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM files 
            WHERE project_id = ? 
            ORDER BY created_at ASC
        ''', (project_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get a file by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    # ==================== Code ====================
    
    def save_code(self, file_id: int, code_content: str) -> Dict[str, Any]:
        """Save code for a file."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO code (file_id, code_content)
            VALUES (?, ?)
        ''', (file_id, code_content))
        
        conn.commit()
        code_id = cursor.lastrowid
        
        cursor.execute('SELECT * FROM code WHERE id = ?', (code_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_code_by_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest code for a file."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM code 
            WHERE file_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (file_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_code_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """Get all code versions for a file."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM code 
            WHERE file_id = ? 
            ORDER BY created_at ASC
        ''', (file_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ==================== Utility ====================
    
    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of a project (metadata, file count, chat count)."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        files = self.get_files_by_project(project_id)
        chat_history = self.get_chat_history(project_id)
        
        return {
            'project': dict(project),
            'file_count': len(files),
            'chat_count': len(chat_history),
            'files': files,
            'chat_history': chat_history
        }
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and all associated data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all files for this project
            cursor.execute('SELECT id FROM files WHERE project_id = ?', (project_id,))
            file_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete code entries
            for file_id in file_ids:
                cursor.execute('DELETE FROM code WHERE file_id = ?', (file_id,))
            
            # Delete files
            cursor.execute('DELETE FROM files WHERE project_id = ?', (project_id,))
            
            # Delete chat history
            cursor.execute('DELETE FROM chat_history WHERE project_id = ?', (project_id,))
            
            # Delete project
            cursor.execute('DELETE FROM projects WHERE project_id = ?', (project_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False
        finally:
            conn.close()


# Global database instance
db = Database()
