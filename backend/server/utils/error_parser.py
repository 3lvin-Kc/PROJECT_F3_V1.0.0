import re
from typing import Dict, Any, List, Optional
from ..models.message_models import ErrorDetails, ErrorSeverity


class ErrorParser:
    
    def __init__(self):
        self.name = "ErrorParser"
        self.error_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, Dict]:
        return {
            "syntax_error": {
                "pattern": r"(Syntax|syntax)\s+error[:\s]+(.+)",
                "severity": ErrorSeverity.LOW,
                "type": "syntax"
            },
            "compile_error": {
                "pattern": r"(Error|error)[:\s]+(.+)",
                "severity": ErrorSeverity.MEDIUM,
                "type": "compile"
            },
            "undefined": {
                "pattern": r"Undefined\s+(name|class|method)[:\s]+['\"]?(\w+)['\"]?",
                "severity": ErrorSeverity.MEDIUM,
                "type": "compile"
            },
            "type_error": {
                "pattern": r"(Type|type)\s+['\"]?(\w+)['\"]?\s+(is not|isn't)\s+a\s+subtype",
                "severity": ErrorSeverity.MEDIUM,
                "type": "runtime"
            },
            "null_error": {
                "pattern": r"(Null|null)\s+(check|safety|reference)",
                "severity": ErrorSeverity.HIGH,
                "type": "runtime"
            },
            "constraint_error": {
                "pattern": r"(Constraint|constraint|overflow|Overflow)",
                "severity": ErrorSeverity.MEDIUM,
                "type": "validation"
            }
        }
    
    def parse_dart_analyzer_output(self, output: str) -> List[ErrorDetails]:
        errors = []
        
        lines = output.split('\n')
        
        for line in lines:
            if not line.strip() or line.startswith('Analyzing'):
                continue
            
            error = self._parse_error_line(line)
            if error:
                errors.append(error)
        
        return errors
    
    def _parse_error_line(self, line: str) -> Optional[ErrorDetails]:
        line_pattern = r'^\s*(.+?):(\d+):(\d+):\s*(error|warning|info):\s*(.+)$'
        match = re.match(line_pattern, line)
        
        if match:
            file_path = match.group(1)
            line_number = int(match.group(2))
            severity_str = match.group(4)
            message = match.group(5)
            
            severity = self._map_severity(severity_str)
            error_type = self._categorize_error(message)
            
            return ErrorDetails(
                error_type=error_type,
                severity=severity,
                message=message,
                file_path=file_path,
                line_number=line_number
            )
        
        for pattern_name, pattern_info in self.error_patterns.items():
            match = re.search(pattern_info["pattern"], line, re.IGNORECASE)
            if match:
                return ErrorDetails(
                    error_type=pattern_info["type"],
                    severity=pattern_info["severity"],
                    message=line.strip(),
                    line_number=0
                )
        
        return None
    
    def _map_severity(self, severity_str: str) -> ErrorSeverity:
        severity_map = {
            "error": ErrorSeverity.HIGH,
            "warning": ErrorSeverity.LOW,
            "info": ErrorSeverity.LOW
        }
        return severity_map.get(severity_str.lower(), ErrorSeverity.MEDIUM)
    
    def _categorize_error(self, message: str) -> str:
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["syntax", "expected", "unexpected"]):
            return "syntax"
        
        if any(keyword in message_lower for keyword in ["undefined", "not found", "doesn't exist"]):
            return "compile"
        
        if any(keyword in message_lower for keyword in ["null", "nullptr"]):
            return "runtime"
        
        if any(keyword in message_lower for keyword in ["type", "subtype", "cast"]):
            return "runtime"
        
        if any(keyword in message_lower for keyword in ["constraint", "overflow", "bounds"]):
            return "validation"
        
        return "unknown"
    
    def parse_compilation_errors(
        self, 
        error_output: str,
        source_code: Optional[str] = None
    ) -> List[ErrorDetails]:
        
        errors = []
        
        error_blocks = re.split(r'\n(?=\w+:)', error_output)
        
        for block in error_blocks:
            if not block.strip():
                continue
            
            error = self._parse_error_block(block, source_code)
            if error:
                errors.append(error)
        
        return errors
    
    def _parse_error_block(
        self, 
        block: str, 
        source_code: Optional[str]
    ) -> Optional[ErrorDetails]:
        
        lines = block.split('\n')
        if not lines:
            return None
        
        first_line = lines[0]
        
        file_line_match = re.search(r'(.+?):(\d+):(\d+)', first_line)
        
        if file_line_match:
            file_path = file_line_match.group(1)
            line_number = int(file_line_match.group(2))
            message = first_line.split(':', 3)[-1].strip()
        else:
            file_path = None
            line_number = 0
            message = first_line.strip()
        
        error_type = self._categorize_error(message)
        severity = self._determine_severity(message, error_type)
        
        context = None
        if source_code and line_number > 0:
            context = self._extract_code_context(source_code, line_number)
        
        return ErrorDetails(
            error_type=error_type,
            severity=severity,
            message=message,
            file_path=file_path,
            line_number=line_number,
            context=context
        )
    
    def _determine_severity(self, message: str, error_type: str) -> ErrorSeverity:
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["fatal", "critical", "null"]):
            return ErrorSeverity.HIGH
        
        if error_type in ["syntax", "compile"]:
            return ErrorSeverity.MEDIUM
        
        if "warning" in message_lower:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _extract_code_context(
        self, 
        source_code: str, 
        line_number: int, 
        context_lines: int = 2
    ) -> str:
        
        lines = source_code.split('\n')
        
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context_lines_list = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            context_lines_list.append(f"{prefix}{i+1}: {lines[i]}")
        
        return '\n'.join(context_lines_list)
    
    def parse_runtime_error(
        self, 
        error_message: str, 
        stack_trace: Optional[str] = None
    ) -> ErrorDetails:
        
        error_type = "runtime"
        severity = ErrorSeverity.HIGH
        
        if "null" in error_message.lower():
            error_type = "runtime"
            severity = ErrorSeverity.HIGH
        elif "range" in error_message.lower() or "index" in error_message.lower():
            error_type = "runtime"
            severity = ErrorSeverity.MEDIUM
        
        file_path = None
        line_number = 0
        
        if stack_trace:
            first_line_match = re.search(r'(.+?):(\d+)', stack_trace)
            if first_line_match:
                file_path = first_line_match.group(1)
                line_number = int(first_line_match.group(2))
        
        return ErrorDetails(
            error_type=error_type,
            severity=severity,
            message=error_message,
            file_path=file_path,
            line_number=line_number,
            stack_trace=stack_trace
        )
    
    def extract_error_suggestions(self, error: ErrorDetails) -> List[str]:
        suggestions = []
        message_lower = error.message.lower()
        
        if "undefined" in message_lower:
            suggestions.append("Check if the name is spelled correctly")
            suggestions.append("Ensure the required import statement is present")
            suggestions.append("Verify the variable/class is declared before use")
        
        if "null" in message_lower:
            suggestions.append("Initialize the variable before using it")
            suggestions.append("Add null-safety checks (? or !)")
            suggestions.append("Use null-aware operators (?? or ?.)")
        
        if "type" in message_lower and ("mismatch" in message_lower or "subtype" in message_lower):
            suggestions.append("Check the type of the value being assigned")
            suggestions.append("Ensure proper type casting if needed")
            suggestions.append("Verify generic type parameters")
        
        if "syntax" in message_lower:
            suggestions.append("Check for missing semicolons")
            suggestions.append("Verify all brackets are properly closed")
            suggestions.append("Ensure correct use of keywords")
        
        if not suggestions:
            suggestions.append("Review the error message carefully")
            suggestions.append("Check Flutter documentation for this error")
        
        return suggestions
    
    def format_error_for_display(self, error: ErrorDetails) -> str:
        parts = [
            f"Error Type: {error.error_type}",
            f"Severity: {error.severity.value}",
            f"Message: {error.message}"
        ]
        
        if error.file_path:
            parts.append(f"File: {error.file_path}")
        
        if error.line_number:
            parts.append(f"Line: {error.line_number}")
        
        if error.context:
            parts.append(f"\nContext:\n{error.context}")
        
        suggestions = self.extract_error_suggestions(error)
        if suggestions:
            parts.append("\nSuggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                parts.append(f"  {i}. {suggestion}")
        
        return '\n'.join(parts)


error_parser = ErrorParser()


__all__ = ['error_parser', 'ErrorParser']