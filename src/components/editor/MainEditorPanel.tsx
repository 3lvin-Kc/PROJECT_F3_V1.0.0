import { useState, useEffect, useRef } from "react";
import Editor, { type Monaco } from '@monaco-editor/react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { File, Smartphone } from "lucide-react";
import { PreviewPanel } from "@/components/PreviewPanel";

interface MainEditorPanelProps {
  project: any | null;
  selectedFile: string;
  isBuilding: boolean;
  isCodeEditable: boolean;
  editorContent: string;
  hasUnsavedChanges: boolean;
  isStreaming?: boolean;
  streamingContent?: string;
  previewCode?: string; // Composed Dart code for DartPad preview
  onPreviewLoad?: (success: boolean) => void; // Callback when preview loads
  getFileLanguage: (filename: string) => string;
  handleEditorChange: (value: string | undefined) => void;
  saveCurrentFile: () => Promise<void>;
  setIsCodeEditable: (editable: boolean) => void;
}

export const MainEditorPanel = ({
  project,
  selectedFile,
  isBuilding,
  isCodeEditable,
  editorContent,
  hasUnsavedChanges,
  isStreaming = false,
  streamingContent = '',
  previewCode,
  onPreviewLoad,
  getFileLanguage,
  handleEditorChange,
  saveCurrentFile,
  setIsCodeEditable
}: MainEditorPanelProps) => {
  const editorRef = useRef<any>(null);
  
  // Ensure content is a valid string
  const safeEditorContent = typeof editorContent === "string" ? editorContent : 
    (editorContent && typeof editorContent === "object" ? JSON.stringify(editorContent, null, 2) : 
    (editorContent ? String(editorContent) : ''));
  const safeStreamingContent = typeof streamingContent === "string" ? streamingContent : 
    (streamingContent && typeof streamingContent === "object" ? JSON.stringify(streamingContent, null, 2) : 
    (streamingContent ? String(streamingContent) : ''));
  const displayContent = isStreaming && safeStreamingContent ? safeStreamingContent : safeEditorContent;

  // Auto-scroll to end during streaming
  useEffect(() => {
    if (isStreaming && editorRef.current) {
      const editor = editorRef.current;
      const model = editor.getModel();
      if (model) {
        const lineCount = model.getLineCount();
        editor.revealLine(lineCount, 0); // Smooth scroll to bottom
        
        // Set cursor to end
        const lastLineLength = model.getLineLength(lineCount);
        editor.setPosition({ lineNumber: lineCount, column: lastLineLength + 1 });
      }
    }
  }, [displayContent, isStreaming]);

  const handleEditorMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor;
    
    // Add save command
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      saveCurrentFile();
    });
    
    // Smooth scrolling configuration
    editor.updateOptions({
      smoothScrolling: true,
      cursorSmoothCaretAnimation: 'on',
    });
  };

  // Get the language and ensure it's a supported one
  const language = selectedFile ? getFileLanguage(selectedFile) : 'plaintext';
  const validLanguage = language === 'flutter' ? 'dart' : language;

  return (
    <div className="h-full flex flex-col glass-panel">
      <Tabs defaultValue="code" className="h-full flex flex-col">
        <div className="h-10 border-b px-3 flex items-center justify-between bg-background/50">
          <TabsList className="h-7 bg-muted/50">
            <TabsTrigger value="code" className="text-xs h-6 px-3 data-[state=active]:bg-background data-[state=active]:shadow-sm">
              <File className="w-3 h-3 mr-1" />
              Code
            </TabsTrigger>
            <TabsTrigger value="preview" className="text-xs h-6 px-3 data-[state=active]:bg-background data-[state=active]:shadow-sm">
              <Smartphone className="w-3 h-3 mr-1" />
              Preview
            </TabsTrigger>
          </TabsList>
          
          <div className="flex items-center gap-4">
            {selectedFile && (
              <div className="flex items-center gap-2">
                {hasUnsavedChanges && (
                  <div className="w-2 h-2 rounded-full bg-orange-500" title="Unsaved changes" />
                )}
                <span className="text-sm text-muted-foreground font-mono">{selectedFile}</span>
              </div>
            )}
            
            <div className="flex items-center gap-2">
              <Label htmlFor="editable-toggle" className="text-xs">
                Edit
              </Label>
              <Switch
                id="editable-toggle"
                checked={isCodeEditable}
                onCheckedChange={setIsCodeEditable}
              />
            </div>
          </div>
        </div>

        <TabsContent value="code" className="flex-1 m-0">
          <div className="h-full">
            {project && !isBuilding && selectedFile ? (
              <>
                {isStreaming && (
                  <div className="absolute top-2 right-2 z-10 flex items-center gap-2 bg-yellow-500/10 text-yellow-600 border border-yellow-500/20 px-3 py-1.5 rounded-md text-xs font-medium">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                    Generating code...
                  </div>
                )}
                <Editor
                  height="100%"
                  defaultLanguage={validLanguage}
                  language={validLanguage}
                  value={displayContent}
                  onChange={handleEditorChange}
                  theme="vs-dark"
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: 'JetBrains Mono, Monaco, Consolas, "Courier New", monospace',
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    readOnly: !isCodeEditable || isStreaming,
                    wordWrap: 'on',
                    folding: true,
                    renderLineHighlight: 'line',
                    selectionHighlight: true,
                    occurrencesHighlight: "singleFile",
                    bracketPairColorization: { enabled: true },
                    smoothScrolling: true,
                    cursorBlinking: isStreaming ? 'solid' : 'smooth',
                    cursorSmoothCaretAnimation: 'on',
                    formatOnPaste: true,
                    formatOnType: true,
                    tabSize: 2,
                    insertSpaces: true,
                    detectIndentation: true
                  }}
                  onMount={handleEditorMount}
                />
              </>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <File className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-sm text-muted-foreground mb-2">
                    {isBuilding ? 'Generating your widget...' : 'No files to edit'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Create or generate files to start coding
                  </p>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="preview" className="flex-1 m-0">
          <PreviewPanel 
            code={previewCode || editorContent}
            onPreviewLoad={onPreviewLoad}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};