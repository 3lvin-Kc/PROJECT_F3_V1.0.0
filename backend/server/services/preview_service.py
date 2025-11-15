import re
from typing import Dict, Any, List, Optional
import hashlib
from datetime import datetime


class PreviewService:
    
    def __init__(self):
        self.name = "PreviewService"
        self.preview_cache: Dict[str, Dict] = {}
        print(f"PreviewService initialized")
    
    def generate_preview_data(self, dart_code: str, file_path: str) -> Dict[str, Any]:
        code_hash = self._hash_code(dart_code)
        
        if code_hash in self.preview_cache:
            cached = self.preview_cache[code_hash]
            return {
                "success": True,
                "cached": True,
                "preview": cached
            }
        
        widget_info = self._extract_widget_info(dart_code)
        widget_tree = self._build_widget_tree(dart_code)
        properties = self._extract_properties(dart_code)
        
        preview_data = {
            "file_path": file_path,
            "widget_info": widget_info,
            "widget_tree": widget_tree,
            "properties": properties,
            "timestamp": datetime.now().isoformat(),
            "code_hash": code_hash
        }
        
        self.preview_cache[code_hash] = preview_data
        
        return {
            "success": True,
            "cached": False,
            "preview": preview_data
        }
    
    def _hash_code(self, code: str) -> str:
        return hashlib.md5(code.encode()).hexdigest()
    
    def _extract_widget_info(self, dart_code: str) -> Dict[str, Any]:
        class_match = re.search(r'class\s+(\w+)\s+extends\s+(\w+)', dart_code)
        
        if class_match:
            class_name = class_match.group(1)
            parent_class = class_match.group(2)
        else:
            class_name = "Unknown"
            parent_class = "Unknown"
        
        is_stateful = "StatefulWidget" in dart_code or "State<" in dart_code
        is_stateless = "StatelessWidget" in dart_code
        
        return {
            "class_name": class_name,
            "parent_class": parent_class,
            "type": "StatefulWidget" if is_stateful else "StatelessWidget" if is_stateless else "Unknown",
            "is_stateful": is_stateful,
            "is_stateless": is_stateless
        }
    
    def _build_widget_tree(self, dart_code: str) -> List[Dict[str, Any]]:
        widgets = []
        
        common_widgets = [
            'Container', 'Column', 'Row', 'Stack', 'Text', 'Button',
            'ElevatedButton', 'TextButton', 'OutlinedButton', 'IconButton',
            'Card', 'ListTile', 'AppBar', 'Scaffold', 'Center', 'Padding',
            'Align', 'SizedBox', 'Expanded', 'Flexible', 'Image', 'Icon'
        ]
        
        for widget_name in common_widgets:
            pattern = rf'{widget_name}\s*\('
            matches = re.finditer(pattern, dart_code)
            
            for match in matches:
                start_pos = match.start()
                line_number = dart_code[:start_pos].count('\n') + 1
                
                widgets.append({
                    "name": widget_name,
                    "line": line_number,
                    "position": start_pos
                })
        
        widgets.sort(key=lambda x: x['position'])
        
        for widget in widgets:
            del widget['position']
        
        return widgets
    
    def _extract_properties(self, dart_code: str) -> Dict[str, Any]:
        properties = {
            "colors": self._extract_colors(dart_code),
            "text_content": self._extract_text_content(dart_code),
            "dimensions": self._extract_dimensions(dart_code),
            "imports": self._extract_imports(dart_code)
        }
        
        return properties
    
    def _extract_colors(self, dart_code: str) -> List[str]:
        colors = []
        
        color_patterns = [
            r'Colors\.(\w+)',
            r'Color\(0x[0-9A-Fa-f]{8}\)',
            r'Color\.fromRGBO\([^)]+\)'
        ]
        
        for pattern in color_patterns:
            matches = re.findall(pattern, dart_code)
            colors.extend(matches)
        
        return list(set(colors))
    
    def _extract_text_content(self, dart_code: str) -> List[str]:
        text_matches = re.findall(r'Text\s*\(\s*[\'"]([^\'"]+)[\'"]', dart_code)
        return list(set(text_matches))
    
    def _extract_dimensions(self, dart_code: str) -> Dict[str, List]:
        dimensions = {
            "width": [],
            "height": [],
            "padding": [],
            "margin": []
        }
        
        width_matches = re.findall(r'width:\s*(\d+(?:\.\d+)?)', dart_code)
        dimensions["width"] = [float(w) for w in width_matches]
        
        height_matches = re.findall(r'height:\s*(\d+(?:\.\d+)?)', dart_code)
        dimensions["height"] = [float(h) for h in height_matches]
        
        padding_matches = re.findall(r'padding:\s*EdgeInsets\.\w+\(([^)]+)\)', dart_code)
        dimensions["padding"] = padding_matches
        
        margin_matches = re.findall(r'margin:\s*EdgeInsets\.\w+\(([^)]+)\)', dart_code)
        dimensions["margin"] = margin_matches
        
        return dimensions
    
    def _extract_imports(self, dart_code: str) -> List[str]:
        import_matches = re.findall(r"import\s+['\"]([^'\"]+)['\"]", dart_code)
        return import_matches
    
    def generate_hot_reload_data(
        self, 
        old_code: str, 
        new_code: str
    ) -> Dict[str, Any]:
        old_hash = self._hash_code(old_code)
        new_hash = self._hash_code(new_code)
        
        if old_hash == new_hash:
            return {
                "success": True,
                "changed": False,
                "message": "No changes detected"
            }
        
        old_widgets = set([w['name'] for w in self._build_widget_tree(old_code)])
        new_widgets = set([w['name'] for w in self._build_widget_tree(new_code)])
        
        added_widgets = new_widgets - old_widgets
        removed_widgets = old_widgets - new_widgets
        
        return {
            "success": True,
            "changed": True,
            "added_widgets": list(added_widgets),
            "removed_widgets": list(removed_widgets),
            "old_hash": old_hash,
            "new_hash": new_hash
        }
    
    def validate_preview_compatibility(self, dart_code: str) -> Dict[str, Any]:
        issues = []
        
        if "async" in dart_code and "await" in dart_code:
            issues.append({
                "type": "warning",
                "message": "Async code may not render in preview"
            })
        
        if "Navigator" in dart_code:
            issues.append({
                "type": "warning",
                "message": "Navigation requires full app context"
            })
        
        if "Provider" in dart_code or "BlocProvider" in dart_code:
            issues.append({
                "type": "warning",
                "message": "State management may need initialization"
            })
        
        return {
            "compatible": len([i for i in issues if i['type'] == 'error']) == 0,
            "issues": issues
        }
    
    def clear_cache(self):
        self.preview_cache.clear()
        return {"success": True, "message": "Preview cache cleared"}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "cached_previews": len(self.preview_cache),
            "cache_keys": list(self.preview_cache.keys())
        }


preview_service = PreviewService()


__all__ = ['preview_service', 'PreviewService']