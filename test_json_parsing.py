"""
Test script for JSON parsing with markdown code blocks.
"""
import json
import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.agents.json_to_flutter_converter import convert_json_to_flutter

# Sample AI response with markdown code blocks
sample_response = """```json
{
  "files": [
    {
      "path": "lib/main.dart",
      "type": "entry_point",
      "imports": [
        "package:flutter/material.dart",
        "package:input_widgets_app/preview/input_widget_preview.dart"
      ],
      "components": [
        {
          "name": "MyApp",
          "type": "StatelessWidget",
          "properties": [],
          "build": {
            "returns": "MaterialApp(title: 'Input Widgets App', theme: ThemeData(useMaterial3: true), home: const InputWidgetPreview())"
          }
        }
      ]
    },
    {
      "path": "lib/widgets/input_widget.dart",
      "type": "widget",
      "imports": [
        "package:flutter/material.dart"
      ],
      "components": [
        {
          "name": "InputWidget",
          "type": "StatefulWidget",
          "properties": [
            {
              "name": "labelText",
              "type": "String?"
            },
            {
              "name": "hintText",
              "type": "String?"
            },
            {
              "name": "initialValue",
              "type": "String?"
            },
            {
              "name": "onChanged",
              "type": "void Function(String)?"
            }
          ],
          "build": {
            "returns": "Padding(padding: const EdgeInsets.all(8.0), child: TextField(controller: _controller, decoration: InputDecoration(labelText: widget.labelText, hintText: widget.hintText, border: const OutlineInputBorder()), onChanged: widget.onChanged))"
          }
        }
      ]
    },
    {
      "path": "pubspec.yaml",
      "type": "config",
      "content": "name: input_widgets_app\\ndescription: A new Flutter project showcasing input widgets.\\npublish_to: 'none'\\nversion: 1.0.0+1\\n\\nenvironment:\\n  sdk: '>=3.0.0 <4.0.0'\\n\\ndependencies:\\n  flutter:\\n    sdk: flutter\\n  cupertino_icons: ^1.0.2\\n\\ndev_dependencies:\\n  flutter_test:\\n    sdk: flutter\\n  flutter_lints: ^2.0.0\\n\\nflutter:\\n  uses-material-design: true\\n"
    }
  ]
}
```"""

def test_json_parsing():
    """Test JSON parsing with markdown code blocks."""
    print("Testing JSON parsing with markdown code blocks...")
    
    try:
        # Clean the response by removing markdown code blocks
        cleaned_response = sample_response.strip()
        # Remove markdown code block markers
        cleaned_response = re.sub(r'^```(?:json)?', '', cleaned_response)
        cleaned_response = re.sub(r'```$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()
        
        print("✓ Response cleaned successfully")
        print(f"  Cleaned response length: {len(cleaned_response)} characters")
        
        # Parse the JSON structure
        json_structure = json.loads(cleaned_response)
        print("✓ JSON parsed successfully")
        print(f"  Files found: {len(json_structure.get('files', []))}")
        
        # Convert JSON structure to Flutter code
        file_contents = convert_json_to_flutter(json_structure)
        print("✓ JSON converted to Flutter code successfully")
        print(f"  Files generated: {len(file_contents)}")
        
        # Show file contents
        for file_path, content in file_contents.items():
            print(f"  {file_path}: {len(content)} characters")
            if file_path.endswith('.dart'):
                print(f"    Dart code preview: {content[:100]}...")
            else:
                print(f"    Content preview: {content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("Testing JSON parsing and conversion...\n")
    
    success = test_json_parsing()
    
    print("\n" + "="*50)
    print("TEST RESULT:")
    print(f"JSON parsing and conversion: {'✓ PASS' if success else '✗ FAIL'}")
    print("="*50)
    
    if success:
        print("JSON parsing and conversion is working correctly!")
    else:
        print("There are issues with JSON parsing or conversion.")

if __name__ == "__main__":
    main()