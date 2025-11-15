import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileTree } from "@/components/FileTree";
import { MainEditorPanel } from "@/components/editor/MainEditorPanel";
import { EditorHeader } from "@/components/EditorHeader";
import { EditorStatusBar } from "@/components/EditorStatusBar";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";
import { AIAssistantPanel } from "@/components/editor/AIAssistantPanel";
import { getFileLanguage } from "@/components/editor/editorUtils";

const EditorPageNew = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // UI State
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [showFileExplorer, setShowFileExplorer] = useState(true);
  const [isCodeEditable, setIsCodeEditable] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Preview State
  const [previewCode, setPreviewCode] = useState<string>('');

  // Project State
  const [files, setFiles] = useState<Map<string, any>>(new Map());
  const [projectId, setProjectId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [projectName, setProjectName] = useState<string>('New Flutter Widget');
  const [isLoadingProject, setIsLoadingProject] = useState(false);

  // Load project from URL parameters
  useEffect(() => {
    const projectParam = searchParams.get('project');
    const conversationParam = searchParams.get('conversation');
    
    if (projectParam) {
      setProjectId(projectParam);
      setConversationId(conversationParam);
      loadProject(projectParam);
    } else {
      // Initialize with empty files if no project
      const emptyFiles = new Map<string, any>();
      setFiles(emptyFiles);
      setSelectedFile('');
      setEditorContent('');
    }
  }, [searchParams]);

  // Load project files from backend
  const loadProject = async (projectId: string) => {
    setIsLoadingProject(true);
    try {
      console.log('Loading project:', projectId);
      
      const response = await fetch(`/api/projects/${projectId}`);
      if (!response.ok) {
        throw new Error('Failed to load project');
      }
      
      const projectData = await response.json();
      console.log('Project data loaded:', projectData);
      
      // Set project name from metadata
      if (projectData.metadata?.project_name) {
        setProjectName(projectData.metadata.project_name);
      }
      
      // Load project files
      const filesResponse = await fetch(`/api/projects/${projectId}/files`);
      if (filesResponse.ok) {
        const filesData = await filesResponse.json();
        
        if (filesData.success && filesData.files) {
          const projectFiles = new Map<string, any>();
          
          // Convert file list to Map format
          filesData.files.forEach((file: any) => {
            projectFiles.set(file.path, {
              name: file.name,
              content: '', // Will be loaded when file is selected
              type: 'file',
              size: file.size,
              modified: file.modified
            });
          });
          
          setFiles(projectFiles);
          
          // Auto-select first Dart file if available
          const dartFiles = filesData.files.filter((f: any) => f.name.endsWith('.dart'));
          if (dartFiles.length > 0) {
            setSelectedFile(dartFiles[0].path);
          }
        }
      }
      
    } catch (error) {
      console.error('Failed to load project:', error);
      // Initialize with empty files on error
      const emptyFiles = new Map<string, any>();
      setFiles(emptyFiles);
    } finally {
      setIsLoadingProject(false);
    }
  };

  // Update editor content when selected file changes
  useEffect(() => {
    if (selectedFile && projectId) {
      loadFileContent(selectedFile);
    } else if (selectedFile) {
      const fileData = files.get(selectedFile);
      const content = fileData?.content || '';
      setEditorContent(content);
      setHasUnsavedChanges(false);
    }
  }, [selectedFile, files, projectId]);

  // Load file content from backend
  const loadFileContent = async (filePath: string) => {
    if (!projectId) return;
    
    try {
      const response = await fetch('/api/files/read', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          file_path: filePath
        })
      });
      
      if (response.ok) {
        const fileData = await response.json();
        if (fileData.success) {
          setEditorContent(fileData.content);
          setHasUnsavedChanges(false);
          
          // Update files map with loaded content
          const updatedFiles = new Map(files);
          const existingFile = updatedFiles.get(filePath);
          if (existingFile) {
            updatedFiles.set(filePath, {
              ...existingFile,
              content: fileData.content
            });
            setFiles(updatedFiles);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load file content:', error);
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setEditorContent(value);
      const fileData = files.get(selectedFile);
      setHasUnsavedChanges(value !== (fileData?.content || ''));
    }
  };

  const saveCurrentFile = async (): Promise<void> => {
    if (selectedFile && hasUnsavedChanges) {
      try {
        if (projectId) {
          // Save to backend project
          const response = await fetch('/api/files/write', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              project_id: projectId,
              file_path: selectedFile,
              content: editorContent
            })
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              console.log(`Saved ${selectedFile} to project ${projectId}`);
            }
          }
        }
        
        // Update local state
        const updatedFiles = new Map(files);
        const fileData = updatedFiles.get(selectedFile);
        if (fileData) {
          updatedFiles.set(selectedFile, {
            ...fileData,
            content: editorContent
          });
          setFiles(updatedFiles);
          setHasUnsavedChanges(false);
        }
        
      } catch (error) {
        console.error('Failed to save file:', error);
      }
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
          projectName={isLoadingProject ? "Loading project..." : projectName}
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
                        onFileSelect={setSelectedFile}
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