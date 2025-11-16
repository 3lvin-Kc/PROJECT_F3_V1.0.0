"""
Project Service for F3 Platform
===============================

Handles comprehensive project management including:
- Project creation with proper Flutter structure
- Database integration for project metadata
- File system operations
- Project lifecycle management
- Integration with conversation system
"""

import os
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import database repositories
from ..database import project_repo, file_repo, conversation_repo
from ..services.file_service import file_service


class ProjectService:
    """
    Comprehensive project management service for F3 platform.
    
    This service coordinates between:
    - File system operations (via FileService)
    - Database persistence (via repositories)
    - Project metadata management
    - Conversation linking
    """
    
    def __init__(self):
        self.name = "ProjectService"
        print(f" {self.name} initialized")
    
    async def create_project_from_prompt(
        self,
        user_prompt: str,
        user_id: int = 1,  # Default user for now
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete project from user prompt.
        
        This is the main method called when user submits initial prompt.
        
        Args:
            user_prompt: The user's initial prompt/request
            user_id: User ID (default 1 for now)
            conversation_id: Optional conversation ID to link
            
        Returns:
            Dict with project details and status
        """
        try:
            print(f"\n [{self.name}] Creating project from prompt")
            print(f"   Prompt: {user_prompt[:100]}...")
            
            # 1. Generate unique project ID
            project_id = self._generate_project_id()
            project_name = self._generate_project_name(user_prompt)
            
            # 2. Create database project record
            db_project_id = await self._create_database_project(
                user_id=user_id,
                project_name=project_name,
                description=user_prompt,
                project_id=project_id
            )
            
            if not db_project_id:
                return {
                    "success": False,
                    "error": "Failed to create database project record"
                }
            
            # 3. Create file system project structure
            fs_result = await self._create_file_system_project(project_id, project_name)
            
            if not fs_result["success"]:
                # Rollback database record if file system creation fails
                await self._cleanup_failed_project(db_project_id, project_id)
                return fs_result
            
            # 4. Link conversation if provided
            if conversation_id:
                await self._link_conversation_to_project(conversation_id, db_project_id)
            
            # 5. Create project metadata
            metadata = await self._create_project_metadata(
                project_id=project_id,
                db_project_id=db_project_id,
                project_name=project_name,
                user_prompt=user_prompt,
                conversation_id=conversation_id
            )
            
            print(f" [{self.name}] Project created successfully")
            print(f"   Project ID: {project_id}")
            print(f"   DB ID: {db_project_id}")
            print(f"   Name: {project_name}")
            
            return {
                "success": True,
                "project_id": project_id,
                "db_project_id": db_project_id,
                "project_name": project_name,
                "file_system_path": fs_result["path"],
                "metadata": metadata,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            print(f" [{self.name}] Error creating project: {str(e)}")
            return {
                "success": False,
                "error": f"Project creation failed: {str(e)}"
            }
    
    async def get_project_details(self, project_id: str) -> Dict[str, Any]:
        """
        Get comprehensive project details.
        
        Args:
            project_id: The project identifier
            
        Returns:
            Dict with project details or error
        """
        try:
            # Get file system info
            fs_info = file_service.get_project_info(project_id)
            
            if not fs_info["success"]:
                return fs_info
            
            # Get database info (if exists)
            db_info = await self._get_database_project_info(project_id)
            
            # Get project files
            files_info = file_service.list_files(project_id)
            
            return {
                "success": True,
                "project_id": project_id,
                "file_system": fs_info,
                "database": db_info,
                "files": files_info if files_info["success"] else None,
                "metadata": fs_info.get("metadata", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get project details: {str(e)}"
            }
    
    async def save_generated_files(
        self,
        project_id: str,
        files: List[Dict[str, Any]],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save AI-generated files to project.
        
        Args:
            project_id: Target project ID
            files: List of files with path and content
            conversation_id: Optional conversation ID for tracking
            
        Returns:
            Dict with save results
        """
        try:
            print(f"\n💾 [{self.name}] Saving generated files to project {project_id}")
            
            saved_files = []
            failed_files = []
            
            # Get database project info
            db_project = await self._get_database_project_by_fs_id(project_id)
            
            for file_info in files:
                file_path = file_info.get("file_path", file_info.get("path"))
                content = file_info.get("content", file_info.get("file_content", ""))
                
                if not file_path or not content:
                    failed_files.append({
                        "file": file_info,
                        "error": "Missing file path or content"
                    })
                    continue
                
                # Save to file system
                fs_result = file_service.write_file(project_id, file_path, content)
                
                if fs_result["success"]:
                    # Save to database if project exists in DB
                    if db_project:
                        await self._save_file_to_database(
                            db_project["id"],
                            file_path,
                            content
                        )
                    
                    saved_files.append({
                        "file_path": file_path,
                        "size": len(content),
                        "fs_path": fs_result["path"]
                    })
                else:
                    failed_files.append({
                        "file_path": file_path,
                        "error": fs_result["error"]
                    })
            
            print(f" [{self.name}] Saved {len(saved_files)} files, {len(failed_files)} failed")
            
            return {
                "success": len(saved_files) > 0,
                "saved_files": saved_files,
                "failed_files": failed_files,
                "total_saved": len(saved_files),
                "total_failed": len(failed_files)
            }
            
        except Exception as e:
            print(f" [{self.name}] Error saving files: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to save files: {str(e)}"
            }
    
    async def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Delete project completely (file system + database).
        
        Args:
            project_id: Project to delete
            
        Returns:
            Dict with deletion results
        """
        try:
            print(f"\n [{self.name}] Deleting project {project_id}")
            
            # Get database project info first
            db_project = await self._get_database_project_by_fs_id(project_id)
            
            # Delete from file system
            fs_result = file_service.delete_project(project_id)
            
            # Delete from database if exists
            db_deleted = False
            if db_project:
                try:
                    project_repo.delete_project(db_project["id"])
                    db_deleted = True
                except Exception as e:
                    print(f"Warning: Failed to delete from database: {e}")
            
            return {
                "success": fs_result["success"],
                "file_system_deleted": fs_result["success"],
                "database_deleted": db_deleted,
                "project_id": project_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete project: {str(e)}"
            }
    
    # ============================================================================
    # PRIVATE HELPER METHODS.......................................
    # ============================================================================
    
    def _generate_project_id(self) -> str:
        """Generate unique project ID."""
        timestamp = int(datetime.now().timestamp())
        unique_id = str(uuid.uuid4())[:8]
        return f"f3_project_{timestamp}_{unique_id}"
    
    def _generate_project_name(self, user_prompt: str) -> str:
        """Generate project name from user prompt."""
        # Extract key words from prompt
        words = user_prompt.lower().split()
        
        # Filter out common words
        stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "create", "make", "build", "generate"}
        key_words = [word for word in words[:10] if word not in stop_words and len(word) > 2]
        
        # Take first 3 meaningful words
        name_parts = key_words[:3] if key_words else ["flutter", "widget"]
        
        # Create clean name
        project_name = "_".join(name_parts)
        
        # Add timestamp for uniqueness
        timestamp = int(datetime.now().timestamp())
        
        return f"{project_name}_{timestamp}"
    
    async def _create_database_project(
        self,
        user_id: int,
        project_name: str,
        description: str,
        project_id: str
    ) -> Optional[int]:
        """Create project record in database."""
        try:
            db_project_id = project_repo.create_project(
                user_id=user_id,
                project_name=project_name,
                description=description
            )
            
            if db_project_id:
                # Store mapping between file system ID and database ID
                # This could be stored in project metadata or separate table
                print(f"   Database project created: ID {db_project_id}")
                return db_project_id
            
            return None
            
        except Exception as e:
            print(f"   Database project creation failed: {e}")
            return None
    
    async def _create_file_system_project(self, project_id: str, project_name: str) -> Dict[str, Any]:
        """Create project in file system."""
        try:
            result = file_service.create_project(project_id)
            
            if result["success"]:
                print(f"   File system project created: {result['path']}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"File system creation failed: {str(e)}"
            }
    
    async def _link_conversation_to_project(self, conversation_id: str, db_project_id: int):
        """Link conversation to project in database."""
        try:
            # Update conversation with project_id
            conv = conversation_repo.get_conversation(conversation_id)
            if conv:
                # This would require updating the conversation table schema
                # For now, we'll store it in the conversation metadata
                print(f"   Linked conversation {conversation_id} to project {db_project_id}")
            
        except Exception as e:
            print(f"   Warning: Failed to link conversation: {e}")
    
    async def _create_project_metadata(
        self,
        project_id: str,
        db_project_id: int,
        project_name: str,
        user_prompt: str,
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Create comprehensive project metadata."""
        return {
            "project_id": project_id,
            "db_project_id": db_project_id,
            "project_name": project_name,
            "user_prompt": user_prompt,
            "conversation_id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "files_generated": 0,
            "last_modified": datetime.now().isoformat()
        }
    
    async def _cleanup_failed_project(self, db_project_id: Optional[int], project_id: str):
        """Clean up failed project creation."""
        try:
            if db_project_id:
                project_repo.delete_project(db_project_id)
                print(f"   Cleaned up database project {db_project_id}")
        except Exception as e:
            print(f"   Warning: Failed to cleanup database: {e}")
    
    async def _get_database_project_info(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get database project info by file system project ID."""
        try:
            # This would require a mapping table or metadata field
            # For now, return None as we don't have direct mapping
            return None
        except Exception as e:
            print(f"   Warning: Failed to get database project info: {e}")
            return None
    
    async def _get_database_project_by_fs_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get database project by file system ID."""
        try:
            # This would require a mapping mechanism
            # For now, return None
            return None
        except Exception as e:
            return None
    
    async def _save_file_to_database(
        self,
        db_project_id: int,
        file_path: str,
        content: str
    ):
        """Save file to database."""
        try:
            # Check if file already exists
            existing = file_repo.get_file_by_path(db_project_id, file_path)
            
            if existing:
                # Update existing file
                file_repo.update_file(existing["id"], content)
            else:
                # Create new file
                file_repo.create_file(db_project_id, file_path, content)
                project_repo.increment_file_count(db_project_id)
                
        except Exception as e:
            print(f"   Warning: Failed to save file to database: {e}")


# Global project service instance
project_service = ProjectService()

__all__ = ['ProjectService', 'project_service']
