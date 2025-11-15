import subprocess
import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class CompilerService:
    
    def __init__(self):
        self.name = "CompilerService"
        self.dart_sdk_path = self._find_dart_sdk()
        self.has_dart = self.dart_sdk_path is not None
        print(f"CompilerService initialized (Dart SDK: {'Found' if self.has_dart else 'Not Found'})")
    
    def _find_dart_sdk(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ["dart", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "dart" if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    async def compile_code(self, dart_code: str, file_name: str = "temp.dart") -> Dict[str, Any]:
        if not self.has_dart:
            return self._mock_compilation(dart_code)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / file_name
            file_path.write_text(dart_code)
            
            result = await self._run_dart_analyze(str(file_path))
            
            return {
                "success": result["success"],
                "errors": result["errors"],
                "warnings": result["warnings"],
                "file_path": file_name
            }
    
    async def _run_dart_analyze(self, file_path: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["dart", "analyze", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            errors, warnings = self._parse_analyze_output(output)
            
            return {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "raw_output": output
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "errors": [{"message": "Compilation timeout", "line": 0}],
                "warnings": []
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [{"message": str(e), "line": 0}],
                "warnings": []
            }
    
    def _parse_analyze_output(self, output: str) -> Tuple[List[Dict], List[Dict]]:
        errors = []
        warnings = []
        
        for line in output.split('\n'):
            if 'error' in line.lower():
                errors.append(self._parse_error_line(line))
            elif 'warning' in line.lower():
                warnings.append(self._parse_error_line(line))
        
        return errors, warnings
    
    def _parse_error_line(self, line: str) -> Dict[str, Any]:
        parts = line.split(':')
        
        line_number = 0
        message = line
        
        if len(parts) >= 2:
            try:
                line_number = int(parts[1].strip())
                message = ':'.join(parts[2:]).strip()
            except ValueError:
                pass
        
        return {
            "line": line_number,
            "message": message,
            "severity": "error" if "error" in line.lower() else "warning"
        }
    
    def _mock_compilation(self, dart_code: str) -> Dict[str, Any]:
        errors = []
        
        if not dart_code.strip():
            errors.append({"line": 0, "message": "Empty code", "severity": "error"})
        
        if dart_code.count('{') != dart_code.count('}'):
            errors.append({"line": 0, "message": "Unbalanced braces", "severity": "error"})
        
        if dart_code.count('(') != dart_code.count(')'):
            errors.append({"line": 0, "message": "Unbalanced parentheses", "severity": "error"})
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": [],
            "file_path": "mock",
            "note": "Mock compilation (Dart SDK not available)"
        }
    
    async def validate_widget(self, dart_code: str) -> Dict[str, Any]:
        basic_checks = self._basic_validation(dart_code)
        
        if not basic_checks["valid"]:
            return {
                "valid": False,
                "errors": basic_checks["errors"]
            }
        
        compile_result = await self.compile_code(dart_code)
        
        return {
            "valid": compile_result["success"],
            "errors": compile_result["errors"],
            "warnings": compile_result["warnings"]
        }
    
    def _basic_validation(self, dart_code: str) -> Dict[str, Any]:
        errors = []
        
        required_patterns = {
            "class_definition": "class ",
            "widget_type": "Widget",
        }
        
        for pattern_name, pattern in required_patterns.items():
            if pattern not in dart_code:
                errors.append({
                    "message": f"Missing {pattern_name.replace('_', ' ')}",
                    "line": 0,
                    "severity": "error"
                })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def check_imports(self, dart_code: str) -> Dict[str, Any]:
        imports = []
        missing_imports = []
        
        for line in dart_code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('import '):
                imports.append(stripped)
        
        if 'StatelessWidget' in dart_code or 'StatefulWidget' in dart_code:
            material_import = "import 'package:flutter/material.dart';"
            if material_import not in imports:
                missing_imports.append(material_import)
        
        return {
            "imports": imports,
            "missing_imports": missing_imports,
            "has_all_imports": len(missing_imports) == 0
        }


compiler_service = CompilerService()


__all__ = ['compiler_service', 'CompilerService']