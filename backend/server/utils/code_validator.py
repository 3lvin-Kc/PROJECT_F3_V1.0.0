import re
from typing import Dict, Any, List, Tuple


class CodeValidator:
    
    def __init__(self):
        self.name = "CodeValidator"
    
    def validate_dart_syntax(self, code: str) -> Dict[str, Any]:
        errors = []
        warnings = []
        
        balanced, balance_errors = self._check_balanced_delimiters(code)
        errors.extend(balance_errors)
        
        syntax_errors = self._check_basic_syntax(code)
        errors.extend(syntax_errors)
        
        style_warnings = self._check_style_guidelines(code)
        warnings.extend(style_warnings)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }
    
    def _check_balanced_delimiters(self, code: str) -> Tuple[bool, List[Dict]]:
        errors = []
        
        delimiters = {
            '{': '}',
            '(': ')',
            '[': ']'
        }
        
        for open_char, close_char in delimiters.items():
            open_count = code.count(open_char)
            close_count = code.count(close_char)
            
            if open_count != close_count:
                errors.append({
                    "type": "syntax",
                    "message": f"Unbalanced {open_char}{close_char}: {open_count} open, {close_count} close",
                    "line": 0
                })
        
        return len(errors) == 0, errors
    
    def _check_basic_syntax(self, code: str) -> List[Dict]:
        errors = []
        
        if not code.strip():
            errors.append({
                "type": "syntax",
                "message": "Empty code",
                "line": 0
            })
            return errors
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                if stripped.endswith(',') and '{' not in stripped and '(' not in stripped:
                    continue
                
                if (not stripped.endswith((';', '{', '}', ',', ')', ']')) 
                    and not stripped.startswith(('@', 'import', 'export', 'part'))
                    and 'class ' not in stripped
                    and 'enum ' not in stripped
                    and '=>' not in stripped):
                    
                    if len(stripped) > 0 and stripped[-1].isalnum():
                        errors.append({
                            "type": "syntax",
                            "message": "Missing semicolon or incorrect syntax",
                            "line": i
                        })
        
        return errors
    
    def _check_style_guidelines(self, code: str) -> List[Dict]:
        warnings = []
        
        if not re.search(r'class\s+[A-Z]', code):
            if 'class ' in code:
                warnings.append({
                    "type": "style",
                    "message": "Class names should start with uppercase letter",
                    "line": 0
                })
        
        variable_pattern = r'\b[A-Z][a-zA-Z0-9_]*\s+[a-z]'
        if re.search(variable_pattern, code):
            warnings.append({
                "type": "style",
                "message": "Variable names should use camelCase",
                "line": 0
            })
        
        if code.count('\n') > 5 and not any(line.strip().startswith('//') for line in code.split('\n')):
            warnings.append({
                "type": "style",
                "message": "Consider adding comments for better code documentation",
                "line": 0
            })
        
        return warnings
    
    def validate_flutter_widget(self, code: str) -> Dict[str, Any]:
        errors = []
        warnings = []
        
        basic_validation = self.validate_dart_syntax(code)
        errors.extend(basic_validation["errors"])
        warnings.extend(basic_validation["warnings"])
        
        if 'class ' not in code:
            errors.append({
                "type": "widget",
                "message": "No class definition found",
                "line": 0
            })
        
        if not ('StatelessWidget' in code or 'StatefulWidget' in code):
            errors.append({
                "type": "widget",
                "message": "Class must extend StatelessWidget or StatefulWidget",
                "line": 0
            })
        
        if 'Widget build(' not in code and '@override' in code:
            errors.append({
                "type": "widget",
                "message": "Missing build method",
                "line": 0
            })
        
        if 'return ' not in code or 'build(' in code and code.count('return') < 1:
            warnings.append({
                "type": "widget",
                "message": "Build method should return a widget",
                "line": 0
            })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "is_widget": len([e for e in errors if e["type"] == "widget"]) == 0
        }
    
    def validate_imports(self, code: str) -> Dict[str, Any]:
        imports = []
        errors = []
        
        import_lines = [line for line in code.split('\n') if line.strip().startswith('import ')]
        
        for line in import_lines:
            if not (line.strip().endswith(';') or line.strip().endswith("'")):
                errors.append({
                    "type": "import",
                    "message": f"Invalid import statement: {line.strip()}",
                    "line": 0
                })
            else:
                match = re.search(r"import\s+['\"]([^'\"]+)['\"]", line)
                if match:
                    imports.append(match.group(1))
        
        required_imports = self._check_required_imports(code)
        missing_imports = [imp for imp in required_imports if imp not in imports]
        
        return {
            "valid": len(errors) == 0 and len(missing_imports) == 0,
            "imports": imports,
            "missing_imports": missing_imports,
            "errors": errors
        }
    
    def _check_required_imports(self, code: str) -> List[str]:
        required = []
        
        if any(widget in code for widget in ['StatelessWidget', 'StatefulWidget', 'Widget', 'BuildContext']):
            required.append('package:flutter/material.dart')
        
        if 'async' in code or 'Future' in code or 'Stream' in code:
            if 'dart:async' not in code:
                required.append('dart:async')
        
        return required
    
    def validate_state_management(self, code: str) -> Dict[str, Any]:
        issues = []
        
        if 'StatefulWidget' in code:
            if 'State<' not in code:
                issues.append({
                    "type": "state",
                    "message": "StatefulWidget requires State class",
                    "line": 0
                })
            
            if 'setState' in code:
                if 'setState(() {' not in code and 'setState((){' not in code:
                    issues.append({
                        "type": "state",
                        "message": "setState should use proper syntax: setState(() { })",
                        "line": 0
                    })
        
        if 'StatelessWidget' in code and 'setState' in code:
            issues.append({
                "type": "state",
                "message": "StatelessWidget cannot use setState",
                "line": 0
            })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def validate_constructor(self, code: str) -> Dict[str, Any]:
        issues = []
        
        class_match = re.search(r'class\s+(\w+)', code)
        if class_match:
            class_name = class_match.group(1)
            
            constructor_pattern = rf'{class_name}\s*\('
            if not re.search(constructor_pattern, code):
                issues.append({
                    "type": "constructor",
                    "message": f"Missing constructor for {class_name}",
                    "line": 0
                })
            
            if 'const ' in code and 'super.key' not in code and 'Key?' not in code:
                issues.append({
                    "type": "constructor",
                    "message": "Const constructor should include 'super.key' parameter",
                    "line": 0
                })
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def comprehensive_validation(self, code: str) -> Dict[str, Any]:
        results = {
            "syntax": self.validate_dart_syntax(code),
            "widget": self.validate_flutter_widget(code),
            "imports": self.validate_imports(code),
            "state": self.validate_state_management(code),
            "constructor": self.validate_constructor(code)
        }
        
        all_errors = []
        all_warnings = []
        
        for category, result in results.items():
            if "errors" in result:
                all_errors.extend(result["errors"])
            if "warnings" in result:
                all_warnings.extend(result["warnings"])
            if "issues" in result:
                all_errors.extend(result["issues"])
        
        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "details": results,
            "summary": {
                "total_errors": len(all_errors),
                "total_warnings": len(all_warnings),
                "syntax_valid": results["syntax"]["valid"],
                "widget_valid": results["widget"]["valid"],
                "imports_valid": results["imports"]["valid"],
                "state_valid": results["state"]["valid"],
                "constructor_valid": results["constructor"]["valid"]
            }
        }


code_validator = CodeValidator()


__all__ = ['code_validator', 'CodeValidator']