
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";


interface CodeViewerProps {
  file: string;
  code: string;
  language: string;
}

export const CodeViewer = ({ file, code, language }: CodeViewerProps) => {
  // Simple syntax highlighting for Dart
  const highlightCode = (code: string) => {
    const keywords = ['class', 'void', 'String', 'int', 'bool', 'var', 'final', 'const', 'if', 'else', 'for', 'while', 'return', 'import', 'extends', 'implements', 'abstract', 'static', 'Widget', 'State', 'StatelessWidget', 'StatefulWidget'];
    const types = ['Widget', 'String', 'int', 'bool', 'double', 'List', 'Map', 'BuildContext'];
    
    let highlighted = code;
    
    // Highlight keywords
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b${keyword}\\b`, 'g');
      highlighted = highlighted.replace(regex, `<span class="text-blue-400 font-medium">${keyword}</span>`);
    });
    
    // Highlight types
    types.forEach(type => {
      const regex = new RegExp(`\\b${type}\\b`, 'g');
      highlighted = highlighted.replace(regex, `<span class="text-green-400">${type}</span>`);
    });
    
    // Highlight strings
    highlighted = highlighted.replace(/'([^']*)'/g, `<span class="text-yellow-400">'$1'</span>`);
    highlighted = highlighted.replace(/"([^"]*)"/g, `<span class="text-yellow-400">"$1"</span>`);
    
    // Highlight comments
    highlighted = highlighted.replace(/\/\/.*$/gm, `<span class="text-gray-500">$&</span>`);
    
    return highlighted;
  };

  const getFileExtension = (filename: string) => {
    return filename.split('.').pop() || '';
  };

  const getLineNumbers = (code: string) => {
    const lines = code.split('\n');
    return lines.map((_, index) => index + 1);
  };

  const lines = code.split('\n');
  const lineNumbers = getLineNumbers(code);

  return (
    <div className="h-full flex flex-col bg-editor">
      {/* File Header */}
      <div className="flex items-center gap-2 p-3 border-b border-editor-border">
        <span className="text-sm text-editor-foreground font-medium truncate">
          {file}
        </span>
        
      </div>

      {/* Code Content */}
      <ScrollArea className="flex-1">
        <div className="flex min-h-full font-mono text-sm">
          {/* Line Numbers */}
          <div className="select-none bg-editor-panel px-3 py-4 text-editor-foreground/50 text-right border-r border-editor-border">
            {lineNumbers.map(num => (
              <div key={num} className="leading-6 h-6">
                {num}
              </div>
            ))}
          </div>

          {/* Code */}
          <div className="flex-1 p-4 text-editor-foreground overflow-auto">
            <pre className="leading-6">
              {lines.map((line, index) => (
                <div key={index} className="h-6">
                  <code
                    dangerouslySetInnerHTML={{
                      __html: highlightCode(line) || ' '
                    }}
                  />
                </div>
              ))}
            </pre>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
};
