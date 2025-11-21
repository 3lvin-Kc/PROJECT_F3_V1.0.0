"""
Test script for the JSON to Flutter converter.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server.agents.json_to_flutter_converter import convert_json_to_flutter

# Test JSON structure
test_json = {
    "files": [
        {
            "path": "lib/main.dart",
            "type": "entry_point",
            "imports": ["package:flutter/material.dart", "package:app/preview/widget_preview.dart"],
            "components": [
                {
                    "name": "MyApp",
                    "type": "StatelessWidget",
                    "properties": [],
                    "build": {
                        "returns": "MaterialApp(title: 'Test App', home: Scaffold(body: Center(child: Text('Hello World'))))"
                    }
                }
            ]
        },
        {
            "path": "lib/widgets/test_widget.dart",
            "type": "widget",
            "imports": ["package:flutter/material.dart"],
            "components": [
                {
                    "name": "TestWidget",
                    "type": "StatelessWidget",
                    "properties": [
                        {"name": "title", "type": "String"}
                    ],
                    "build": {
                        "returns": "Container(padding: EdgeInsets.all(16), child: Text(title))"
                    }
                }
            ]
        }
    ]
}

def test_converter():
    """Test the JSON to Flutter converter."""
    print("Testing JSON to Flutter converter...")
    
    try:
        result = convert_json_to_flutter(test_json)
        print("Conversion successful!")
        
        for file_path, code in result.items():
            print(f"\n--- {file_path} ---")
            print(code)
            print("-" * 40)
            
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_converter()