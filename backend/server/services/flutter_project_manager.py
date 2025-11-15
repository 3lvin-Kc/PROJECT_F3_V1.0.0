from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import re


class FlutterProjectManager:
    
    def __init__(self):
        self.name = "FlutterProjectManager"
        print(f"FlutterProjectManager initialized")
    
    def initialize_project(
        self, 
        project_path: Path,
        project_name: str,
        description: str = "F3 generated project"
    ) -> Dict[str, Any]:
        
        try:
            # Create basic project structure without hardcoded templates
            self._create_basic_pubspec(project_path, project_name, description)
            
            return {
                "success": True,
                "project_name": project_name,
                "path": str(project_path)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # Removed hardcoded main.dart template - agents will generate this as needed
    def _create_main_file(self, project_path: Path, project_name: str):
        # This method is intentionally left empty
        # Agents will create main.dart files with project-specific content
        pass
    
    def _create_basic_pubspec(
        self, 
        project_path: Path, 
        project_name: str,
        description: str
    ):
        # Create a minimal pubspec.yaml - agents will update it as needed
        pubspec_content = {
            "name": project_name,
            "description": description,
            "dependencies": {
                # Dependencies will be added by agents as needed
            }
        }
        
        pubspec_file = project_path / "pubspec.yaml"
        with open(pubspec_file, 'w') as f:
            yaml.dump(pubspec_content, f, default_flow_style=False, sort_keys=False)
    
    # Removed hardcoded analysis_options.yaml template - agents will generate this as needed
    def _create_analysis_options(self, project_path: Path):
        # This method is intentionally left empty
        # Agents will create analysis_options.yaml files with project-specific content
        pass
    
    def add_dependency(
        self, 
        project_path: Path, 
        package_name: str, 
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        
        pubspec_file = project_path / "pubspec.yaml"
        
        if not pubspec_file.exists():
            return {
                "success": False,
                "error": "pubspec.yaml not found"
            }
        
        try:
            with open(pubspec_file, 'r') as f:
                pubspec_data = yaml.safe_load(f)
            
            if "dependencies" not in pubspec_data:
                pubspec_data["dependencies"] = {}
            
            pubspec_data["dependencies"][package_name] = version if version else "^1.0.0"
            
            with open(pubspec_file, 'w') as f:
                yaml.dump(pubspec_data, f, default_flow_style=False, sort_keys=False)
            
            return {
                "success": True,
                "package": package_name,
                "version": version
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def remove_dependency(
        self, 
        project_path: Path, 
        package_name: str
    ) -> Dict[str, Any]:
        
        pubspec_file = project_path / "pubspec.yaml"
        
        if not pubspec_file.exists():
            return {
                "success": False,
                "error": "pubspec.yaml not found"
            }
        
        try:
            with open(pubspec_file, 'r') as f:
                pubspec_data = yaml.safe_load(f)
            
            if "dependencies" in pubspec_data and package_name in pubspec_data["dependencies"]:
                del pubspec_data["dependencies"][package_name]
                
                with open(pubspec_file, 'w') as f:
                    yaml.dump(pubspec_data, f, default_flow_style=False, sort_keys=False)
                
                return {
                    "success": True,
                    "package": package_name
                }
            else:
                return {
                    "success": False,
                    "error": "Package not found in dependencies"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_dependencies(self, project_path: Path) -> Dict[str, Any]:
        pubspec_file = project_path / "pubspec.yaml"
        
        if not pubspec_file.exists():
            return {
                "success": False,
                "error": "pubspec.yaml not found"
            }
        
        try:
            with open(pubspec_file, 'r') as f:
                pubspec_data = yaml.safe_load(f)
            
            dependencies = pubspec_data.get("dependencies", {})
            dev_dependencies = pubspec_data.get("dev_dependencies", {})
            
            return {
                "success": True,
                "dependencies": dependencies,
                "dev_dependencies": dev_dependencies
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_project_config(
        self, 
        project_path: Path, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        pubspec_file = project_path / "pubspec.yaml"
        
        if not pubspec_file.exists():
            return {
                "success": False,
                "error": "pubspec.yaml not found"
            }
        
        try:
            with open(pubspec_file, 'r') as f:
                pubspec_data = yaml.safe_load(f)
            
            pubspec_data.update(config)
            
            with open(pubspec_file, 'w') as f:
                yaml.dump(pubspec_data, f, default_flow_style=False, sort_keys=False)
            
            return {
                "success": True,
                "updated_config": config
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_asset(
        self, 
        project_path: Path, 
        asset_path: str
    ) -> Dict[str, Any]:
        
        pubspec_file = project_path / "pubspec.yaml"
        
        if not pubspec_file.exists():
            return {
                "success": False,
                "error": "pubspec.yaml not found"
            }
        
        try:
            with open(pubspec_file, 'r') as f:
                pubspec_data = yaml.safe_load(f)
            
            if "flutter" not in pubspec_data:
                pubspec_data["flutter"] = {}
            
            if "assets" not in pubspec_data["flutter"]:
                pubspec_data["flutter"]["assets"] = []
            
            if asset_path not in pubspec_data["flutter"]["assets"]:
                pubspec_data["flutter"]["assets"].append(asset_path)
            
            with open(pubspec_file, 'w') as f:
                yaml.dump(pubspec_data, f, default_flow_style=False, sort_keys=False)
            
            return {
                "success": True,
                "asset": asset_path
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _to_pascal_case(self, snake_str: str) -> str:
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)
    
    def validate_project_structure(self, project_path: Path) -> Dict[str, Any]:
        required_files = [
            "pubspec.yaml",
            "lib/main.dart"
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in required_files:
            full_path = project_path / file_path
            if full_path.exists():
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        is_valid = len(missing_files) == 0
        
        return {
            "valid": is_valid,
            "existing_files": existing_files,
            "missing_files": missing_files
        }


flutter_project_manager = FlutterProjectManager()


__all__ = ['flutter_project_manager', 'FlutterProjectManager']