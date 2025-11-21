"""
Module for converting JSON structures to Flutter code.
"""
import json
import logging

logger = logging.getLogger(__name__)

def convert_json_to_flutter(json_structure):
    """
    Converts a JSON structure to Flutter code.
    
    Args:
        json_structure (dict): The JSON structure containing file definitions
        
    Returns:
        dict: A dictionary mapping file paths to their generated code
    """
    try:
        # Parse the JSON if it's a string
        if isinstance(json_structure, str):
            json_structure = json.loads(json_structure)
        
        generated_files = {}
        
        # Process each file in the structure
        for file_info in json_structure.get("files", []):
            file_path = file_info.get("path")
            if not file_path:
                continue
                
            # Generate code for this file
            code = _generate_file_code(file_info)
            generated_files[file_path] = code
            
        return generated_files
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON structure: {e}")
        raise
    except Exception as e:
        logger.error(f"Error converting JSON to Flutter code: {e}")
        raise

def _generate_file_code(file_info):
    """
    Generates Flutter code for a single file.
    
    Args:
        file_info (dict): Information about the file to generate
        
    Returns:
        str: The generated Flutter code
    """
    file_type = file_info.get("type", "")
    
    # Handle files with direct content (like pubspec.yaml, README.md)
    if "content" in file_info:
        return file_info["content"]
    
    # Handle Flutter code files
    imports = file_info.get("imports", [])
    components = file_info.get("components", [])
    
    code_lines = []
    
    # Add imports
    for import_path in imports:
        code_lines.append(f"import '{import_path}';")
    
    if imports:
        code_lines.append("")  # Blank line after imports
    
    # Generate components
    for component in components:
        component_code = _generate_component_code(component)
        code_lines.append(component_code)
        code_lines.append("")  # Blank line between components
    
    return "\n".join(code_lines)

def _generate_component_code(component):
    """
    Generates code for a single component.
    
    Args:
        component (dict): Component definition
        
    Returns:
        str: The generated component code
    """
    component_type = component.get("type", "StatelessWidget")
    component_name = component.get("name", "UnnamedWidget")
    
    if component_type == "StatelessWidget":
        return _generate_stateless_widget(component)
    elif component_type == "StatefulWidget":
        return _generate_stateful_widget(component)
    else:
        # Default to stateless widget for unknown types
        return _generate_stateless_widget(component)

def _generate_stateless_widget(component):
    """
    Generates a StatelessWidget.
    
    Args:
        component (dict): Component definition
        
    Returns:
        str: The generated StatelessWidget code
    """
    name = component.get("name", "UnnamedWidget")
    properties = component.get("properties", [])
    build_info = component.get("build", {})
    
    lines = []
    lines.append(f"class {name} extends StatelessWidget {{")
    
    # Constructor
    if properties:
        lines.append("  const " + name + "({")
        for prop in properties:
            prop_name = prop.get("name", "property")
            prop_type = prop.get("type", "dynamic")
            lines.append(f"    required this.{prop_name},")
        lines.append("  });")
        lines.append("")
        
        # Properties
        for prop in properties:
            prop_name = prop.get("name", "property")
            prop_type = prop.get("type", "dynamic")
            lines.append(f"  final {prop_type} {prop_name};")
        lines.append("")
    else:
        lines.append("  const " + name + "({super.key});")
        lines.append("")
    
    # Build method
    lines.append("  @override")
    lines.append("  Widget build(BuildContext context) {")
    
    build_returns = build_info.get("returns", "Container()")
    lines.append(f"    return {build_returns};")
    
    lines.append("  }")
    lines.append("}")
    
    return "\n".join(lines)

def _generate_stateful_widget(component):
    """
    Generates a StatefulWidget and its State class.
    
    Args:
        component (dict): Component definition
        
    Returns:
        str: The generated StatefulWidget code
    """
    name = component.get("name", "UnnamedWidget")
    properties = component.get("properties", [])
    build_info = component.get("build", {})
    
    lines = []
    
    # StatefulWidget class
    lines.append(f"class {name} extends StatefulWidget {{")
    
    # Constructor
    if properties:
        lines.append("  const " + name + "({")
        for prop in properties:
            prop_name = prop.get("name", "property")
            prop_type = prop.get("type", "dynamic")
            lines.append(f"    required this.{prop_name},")
        lines.append("  });")
        lines.append("")
        
        # Properties
        for prop in properties:
            prop_name = prop.get("name", "property")
            prop_type = prop.get("type", "dynamic")
            lines.append(f"  final {prop_type} {prop_name};")
        lines.append("")
    else:
        lines.append("  const " + name + "({super.key});")
        lines.append("")
    
    lines.append("  @override")
    lines.append(f"  State<{name}> createState() => _{name}State();")
    lines.append("}")
    lines.append("")
    
    # State class
    lines.append(f"class _{name}State extends State<{name}> {{")
    
    # Build method
    lines.append("  @override")
    lines.append("  Widget build(BuildContext context) {")
    
    build_returns = build_info.get("returns", "Container()")
    lines.append(f"    return {build_returns};")
    
    lines.append("  }")
    lines.append("}")
    
    return "\n".join(lines)