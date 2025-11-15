import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime


class FileService:
    
    def __init__(self, base_directory: str = "projects"):
        self.name = "FileService"
        self.base_dir = Path(base_directory)
        self.base_dir.mkdir(exist_ok=True)
        print(f"FileService initialized (base: {self.base_dir})")
    
    def create_project(self, project_id: str) -> Dict[str, Any]:
        project_path = self.base_dir / project_id
        
        if project_path.exists():
            return {
                "success": False,
                "error": "Project already exists",
                "path": str(project_path)
            }
        
        # Generic project structure - let agents define specific files
        structure = {
            "lib": [],
            "test": [],
            "assets": []
        }
        
        try:
            project_path.mkdir(parents=True)
            
            for folder, contents in structure.items():
                folder_path = project_path / folder
                folder_path.mkdir(exist_ok=True)
                
                for item in contents:
                    if item.endswith('/'):
                        (folder_path / item.rstrip('/')).mkdir(exist_ok=True)
                    else:
                        (folder_path / item).touch()
            
            # Create a simple placeholder pubspec.yaml
            self._create_basic_pubspec(project_path, project_id)
            
            metadata = {
                "project_id": project_id,
                "created_at": datetime.now().isoformat(),
                "structure": structure
            }
            
            (project_path / ".f3_metadata.json").write_text(
                json.dumps(metadata, indent=2)
            )
            
            return {
                "success": True,
                "path": str(project_path),
                "structure": structure
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": str(project_path)
            }
    
    def _create_basic_pubspec(self, project_path: Path, project_name: str):
        # Create a minimal pubspec.yaml - agents will update it as needed
        pubspec_content = f"""name: {project_name}
description: F3 generated project
dependencies:
  # Dependencies will be added by agents as needed
"""
        (project_path / "pubspec.yaml").write_text(pubspec_content)
    
    # Removed hardcoded Flutter templates - agents will generate these as needed
    def _create_utils_files(self, project_path: Path):
        # This method is intentionally left empty
        # Agents will create utils files as needed based on the project requirements
        pass
    
    # Removed hardcoded README template - agents will generate this as needed
    def _create_readme(self, project_path: Path, project_name: str):
        # This method is intentionally left empty
        # Agents will create README files with project-specific content
        pass
    
    def write_file(
        self, 
        project_id: str, 
        file_path: str, 
        content: str
    ) -> Dict[str, Any]:
        project_path = self.base_dir / project_id
        
        if not project_path.exists():
            return {
                "success": False,
                "error": "Project not found"
            }
        
        full_path = project_path / file_path
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            
            return {
                "success": True,
                "path": str(full_path),
                "size": len(content)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_file(self, project_id: str, file_path: str) -> Dict[str, Any]:
        project_path = self.base_dir / project_id
        full_path = project_path / file_path
        
        if not full_path.exists():
            return {
                "success": False,
                "error": "File not found"
            }
        
        try:
            content = full_path.read_text(encoding='utf-8')
            
            return {
                "success": True,
                "content": content,
                "path": str(full_path)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, project_id: str, file_path: str) -> Dict[str, Any]:
        project_path = self.base_dir / project_id
        full_path = project_path / file_path
        
        if not full_path.exists():
            return {
                "success": False,
                "error": "File not found"
            }
        
        try:
            full_path.unlink()
            
            return {
                "success": True,
                "path": str(full_path)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_files(self, project_id: str, directory: str = "") -> Dict[str, Any]:
        project_path = self.base_dir / project_id
        
        if not project_path.exists():
            return {
                "success": False,
                "error": "Project not found"
            }
        
        search_path = project_path / directory if directory else project_path
        
        try:
            files = []
            directories = []
            
            for item in search_path.iterdir():
                relative_path = str(item.relative_to(project_path))
                
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": relative_path,
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
                elif item.is_dir():
                    directories.append({
                        "name": item.name,
                        "path": relative_path
                    })
            
            return {
                "success": True,
                "files": files,
                "directories": directories,
                "path": str(search_path)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        project_path = self.base_dir / project_id
        
        if not project_path.exists():
            return {
                "success": False,
                "error": "Project not found"
            }
        
        try:
            shutil.rmtree(project_path)
            
            return {
                "success": True,
                "project_id": project_id
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_project_info(self, project_id: str) -> Dict[str, Any]:
        project_path = self.base_dir / project_id
        
        if not project_path.exists():
            return {
                "success": False,
                "error": "Project not found"
            }
        
        metadata_file = project_path / ".f3_metadata.json"
        
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
        else:
            metadata = {"project_id": project_id}
        
        return {
            "success": True,
            "project_id": project_id,
            "path": str(project_path),
            "metadata": metadata
        }


file_service = FileService()


__all__ = ['file_service', 'FileService']