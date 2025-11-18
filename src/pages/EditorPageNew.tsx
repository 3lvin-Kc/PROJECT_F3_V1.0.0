import { useState, useCallback } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileTree } from "@/components/FileTree";
import { MainEditorPanel } from "@/components/editor/MainEditorPanel";
import { EditorHeader } from "@/components/EditorHeader";
import { EditorStatusBar } from "@/components/EditorStatusBar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";
import { AIAssistantPanel } from "@/components/editor/AIAssistantPanel";
import { getFileLanguage } from "@/components/editor/editorUtils";

const EditorPageNew = () => {
  // UI State
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [showFileExplorer, setShowFileExplorer] = useState(true);
  const [isCodeEditable, setIsCodeEditable] = useState(true);
  const [editorContent, setEditorContent] = useState('// Welcome to the editor!\n// Select a file to start editing.');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Preview State
  const [previewCode, setPreviewCode] = useState<string>('');

  // Project State
  const [files, setFiles] = useState<Map<string, any>>(new Map());
  const [projectName, setProjectName] = useState<string>('Frontend-Only Project');

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setEditorContent(value);
      const fileData = files.get(selectedFile);
      setHasUnsavedChanges(value !== (fileData?.content || ''));
    }
  };

  const saveCurrentFile = async (): Promise<void> => {
    if (selectedFile) {
      console.log(`File "${selectedFile}" would be saved here.`);
      setHasUnsavedChanges(false);
    }
  };

  const shouldShowFileExplorer = () => {
    return showFileExplorer && files.size > 0;
  };

  // Convert files Map to object structure
  const projectFiles = Object.fromEntries(files);

  // Build tree structure for file explorer
  const buildStructure = (filesMap: Map<string, any>) => {
    const root: any = { type: 'folder', name: '', children: [] };
    
    for (const fullPath of filesMap.keys()) {
      const parts = fullPath.split('/');
      let node = root;
      
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        const isFile = i === parts.length - 1;
        
        if (isFile) {
          node.children.push({ type: 'file', name: part, path: fullPath });
        } else {
          let next = node.children.find((c: any) => c.type === 'folder' && c.name === part);
          if (!next) {
            next = { type: 'folder', name: part, children: [] };
            node.children.push(next);
          }
          node = next;
        }
      }
    }
    
    return root.children;
  };

  const handlePreviewLoad = useCallback((success: boolean) => {
    console.log('Preview load status:', success);
  }, []);

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="h-screen bg-background flex flex-col w-full">
        <EditorHeader
          projectName={projectName}
          showFileExplorer={shouldShowFileExplorer()}
          onToggleFileExplorer={() => setShowFileExplorer(!showFileExplorer)}
        />

        <div className="flex-1 overflow-hidden">
          <ResizablePanelGroup direction="horizontal" className="h-full">
            {/* AI Assistant Panel - Resizable */}
            <ResizablePanel defaultSize={25} minSize={15} maxSize={40} className="border-r">
              <AIAssistantPanel showAIAssistant={true} />
            </ResizablePanel>
            
            <ResizableHandle withHandle />
            
            {/* Main Content with Fixed File Tree */}
            <ResizablePanel defaultSize={75} minSize={60}>
              <div className="h-full flex">
                {/* Main Content Area */}
                <div className="flex-1">
                  <MainEditorPanel
                    project={{ files: projectFiles } as any}
                    selectedFile={selectedFile}
                    isBuilding={false}
                    isCodeEditable={isCodeEditable}
                    editorContent={editorContent}
                    hasUnsavedChanges={hasUnsavedChanges}
                    isStreaming={false}
                    streamingContent={''}
                    previewCode={previewCode}
                    onPreviewLoad={handlePreviewLoad}
                    getFileLanguage={getFileLanguage}
                    handleEditorChange={handleEditorChange}
                    saveCurrentFile={saveCurrentFile}
                    setIsCodeEditable={setIsCodeEditable}
                  />
                </div>

                {/* Fixed Width File Explorer - Only show when files exist */}
                {shouldShowFileExplorer() && (
                  <div className="w-80 h-full glass-panel border-l flex-shrink-0">
                    <div className="h-10 px-4 border-b flex items-center justify-between bg-background/50">
                      <div className="flex items-center">
                        <span className="text-sm font-medium">Files</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {files.size || 0} files
                      </div>
                    </div>
                    <ScrollArea className="h-[calc(100%-2.5rem)] px-1 py-1">
                      <FileTree
                        files={buildStructure(files)}
                        onFileSelect={(path) => {
                          setSelectedFile(path);
                          setEditorContent(files.get(path)?.content || '');
                        }}
                        selectedFile={selectedFile}
                      />
                    </ScrollArea>
                  </div>
                )}
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>

        <EditorStatusBar 
          selectedFile={selectedFile}
          fileCount={files.size}
          showFileExplorer={shouldShowFileExplorer()}
          hasFiles={files.size > 0}
          onToggleFileExplorer={() => setShowFileExplorer(!showFileExplorer)}
        />
      </div>
    </SidebarProvider>
  );
};

export default EditorPageNew;