from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from .database import database


class UserRepository:
    
    def create_user(self, email: str, username: str, password_hash: str) -> Optional[int]:
        try:
            cursor = database.execute(
                "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
                (email, username, password_hash)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        row = database.fetchone("SELECT * FROM users WHERE email = ?", (email,))
        return dict(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        row = database.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(row) if row else None
    
    def update_last_login(self, user_id: int):
        database.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
    
    def update_user(self, user_id: int, updates: Dict[str, Any]):
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = tuple(updates.values()) + (user_id,)
        database.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?",
            values
        )


class ProjectRepository:
    
    def create_project(self, user_id: int, project_name: str, description: Optional[str] = None) -> Optional[int]:
        try:
            cursor = database.execute(
                "INSERT INTO projects (user_id, project_name, description) VALUES (?, ?, ?)",
                (user_id, project_name, description)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating project: {e}")
            return None
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        row = database.fetchone("SELECT * FROM projects WHERE id = ?", (project_id,))
        return dict(row) if row else None
    
    def get_user_projects(self, user_id: int) -> List[Dict]:
        rows = database.fetchall(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        return [dict(row) for row in rows]
    
    def update_project(self, project_id: int, updates: Dict[str, Any]):
        updates['updated_at'] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = tuple(updates.values()) + (project_id,)
        database.execute(
            f"UPDATE projects SET {set_clause} WHERE id = ?",
            values
        )
    
    def delete_project(self, project_id: int):
        database.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    
    def increment_file_count(self, project_id: int):
        database.execute(
            "UPDATE projects SET files_count = files_count + 1 WHERE id = ?",
            (project_id,)
        )


class FileRepository:
    
    def create_file(
        self,
        project_id: int,
        file_path: str,
        file_content: str,
        file_type: str = "dart"
    ) -> Optional[int]:
        try:
            cursor = database.execute(
                """INSERT INTO project_files 
                   (project_id, file_path, file_content, file_type, file_size)
                   VALUES (?, ?, ?, ?, ?)""",
                (project_id, file_path, file_content, file_type, len(file_content))
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating file: {e}")
            return None
    
    def get_file(self, file_id: int) -> Optional[Dict]:
        row = database.fetchone("SELECT * FROM project_files WHERE id = ?", (file_id,))
        return dict(row) if row else None
    
    def get_file_by_path(self, project_id: int, file_path: str) -> Optional[Dict]:
        row = database.fetchone(
            "SELECT * FROM project_files WHERE project_id = ? AND file_path = ?",
            (project_id, file_path)
        )
        return dict(row) if row else None
    
    def get_project_files(self, project_id: int) -> List[Dict]:
        rows = database.fetchall(
            "SELECT * FROM project_files WHERE project_id = ? ORDER BY file_path",
            (project_id,)
        )
        return [dict(row) for row in rows]
    
    def update_file(self, file_id: int, file_content: str):
        database.execute(
            """UPDATE project_files 
               SET file_content = ?, file_size = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (file_content, len(file_content), file_id)
        )
    
    def delete_file(self, file_id: int):
        database.execute("DELETE FROM project_files WHERE id = ?", (file_id,))


class ConversationRepository:
    
    def create_conversation(
        self,
        user_id: int,
        conversation_id: str,
        project_id: Optional[int] = None
    ) -> Optional[int]:
        try:
            cursor = database.execute(
                "INSERT INTO conversations (user_id, conversation_id, project_id) VALUES (?, ?, ?)",
                (user_id, conversation_id, project_id)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return None
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        row = database.fetchone(
            "SELECT * FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        )
        return dict(row) if row else None
    
    def get_user_conversations(self, user_id: int) -> List[Dict]:
        rows = database.fetchall(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY last_message_at DESC",
            (user_id,)
        )
        return [dict(row) for row in rows]
    
    def update_conversation(self, conversation_id: str, mode: str):
        database.execute(
            """UPDATE conversations 
               SET current_mode = ?, last_message_at = CURRENT_TIMESTAMP
               WHERE conversation_id = ?""",
            (mode, conversation_id)
        )
    
    def delete_conversation(self, conversation_id: str):
        database.execute(
            "DELETE FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        )


class MessageRepository:
    
    def create_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        intent_type: Optional[str] = None,
        files_modified: Optional[List[str]] = None
    ) -> Optional[int]:
        try:
            files_json = json.dumps(files_modified) if files_modified else None
            cursor = database.execute(
                """INSERT INTO messages 
                   (conversation_id, role, content, intent_type, files_modified)
                   VALUES (?, ?, ?, ?, ?)""",
                (conversation_id, role, content, intent_type, files_json)
            )
            
            database.execute(
                "UPDATE conversations SET message_count = message_count + 1 WHERE id = ?",
                (conversation_id,)
            )
            
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating message: {e}")
            return None
    
    def get_conversation_messages(self, conversation_id: int, limit: int = 50) -> List[Dict]:
        rows = database.fetchall(
            """SELECT * FROM messages 
               WHERE conversation_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (conversation_id, limit)
        )
        messages = [dict(row) for row in rows]
        return list(reversed(messages))


class TemplateRepository:
    
    def create_template(
        self,
        template_name: str,
        category: str,
        template_code: str,
        preview_image: Optional[str] = None
    ) -> Optional[int]:
        try:
            cursor = database.execute(
                """INSERT INTO widget_templates 
                   (template_name, category, template_code, preview_image)
                   VALUES (?, ?, ?, ?)""",
                (template_name, category, template_code, preview_image)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating template: {e}")
            return None
    
    def get_templates_by_category(self, category: str) -> List[Dict]:
        rows = database.fetchall(
            "SELECT * FROM widget_templates WHERE category = ? ORDER BY usage_count DESC",
            (category,)
        )
        return [dict(row) for row in rows]
    
    def get_all_templates(self) -> List[Dict]:
        rows = database.fetchall("SELECT * FROM widget_templates ORDER BY usage_count DESC")
        return [dict(row) for row in rows]
    
    def increment_usage(self, template_id: int):
        database.execute(
            "UPDATE widget_templates SET usage_count = usage_count + 1 WHERE id = ?",
            (template_id,)
        )


class ErrorLogRepository:
    
    def log_error(
        self,
        user_id: Optional[int],
        project_id: Optional[int],
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    ) -> Optional[int]:
        try:
            cursor = database.execute(
                """INSERT INTO error_logs 
                   (user_id, project_id, error_type, error_message, stack_trace)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, project_id, error_type, error_message, stack_trace)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"Error logging error: {e}")
            return None
    
    def get_user_errors(self, user_id: int, limit: int = 50) -> List[Dict]:
        rows = database.fetchall(
            """SELECT * FROM error_logs 
               WHERE user_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (user_id, limit)
        )
        return [dict(row) for row in rows]
    
    def mark_resolved(self, error_id: int):
        database.execute(
            "UPDATE error_logs SET resolved = 1 WHERE id = ?",
            (error_id,)
        )


class GenerationHistoryRepository:
    
    def log_generation(
        self,
        user_id: int,
        user_prompt: str,
        generated_code: Optional[str] = None,
        project_id: Optional[int] = None,
        success: bool = True,
        compilation_errors: Optional[str] = None
    ) -> Optional[int]:
        try:
            cursor = database.execute(
                """INSERT INTO generation_history 
                   (user_id, project_id, user_prompt, generated_code, success, compilation_errors)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, project_id, user_prompt, generated_code, success, compilation_errors)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"Error logging generation: {e}")
            return None
    
    def get_user_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        rows = database.fetchall(
            """SELECT * FROM generation_history 
               WHERE user_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (user_id, limit)
        )
        return [dict(row) for row in rows]


user_repo = UserRepository()
project_repo = ProjectRepository()
file_repo = FileRepository()
conversation_repo = ConversationRepository()
message_repo = MessageRepository()
template_repo = TemplateRepository()
error_log_repo = ErrorLogRepository()
generation_history_repo = GenerationHistoryRepository()


__all__ = [
    'user_repo',
    'project_repo',
    'file_repo',
    'conversation_repo',
    'message_repo',
    'template_repo',
    'error_log_repo',
    'generation_history_repo'
]  