import { useState, useCallback, useEffect, useMemo } from "react";
import { useAgent } from "@/hooks/use-agent";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileTree } from "@/components/FileTree";
import { MainEditorPanel } from "@/components/editor/MainEditorPanel";
import { EditorHeader } from "@/components/EditorHeader";
import { EditorStatusBar } from "@/components/EditorStatusBar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";
import { AIAssistantPanel } from "@/components/editor/AIAssistantPanel";
import { getFileLanguage } from "@/components/editor/editorUtils";

// Add the generateProjectId function here
const generateProjectId = (): string => {
  return `proj_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const EditorPageNew = () => {
  // UI State
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [showFileExplorer, setShowFileExplorer] = useState(true);
  const [isCodeEditable, setIsCodeEditable] = useState(true);
  const [editorContent, setEditorContent] = useState<string>('// Welcome to the editor!\n// Select a file to start editing.');

  // Agent State
  const [projectId, setProjectId] = useState<string>('');
  const { state: agentState, sendMessage, initializeState } = useAgent(projectId);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams(); // Updated to include setSearchParams
  const navigate = useNavigate();

  // Preview State
  const [previewCode, setPreviewCode] = useState<string>('');

  // Project State
  const [files, setFiles] = useState<Map<string, any>>(new Map());

  // Initialize project ID from URL query params
  useEffect(() => {
    const urlProjectId = searchParams.get('projectId');
    if (urlProjectId) {
      setProjectId(urlProjectId);
    }
  }, [searchParams]);

  // Load chat history and files from database when project ID is set
  useEffect(() => {
    const loadProjectData = async () => {
      if (!projectId) return;

      try {
        let conversationHistory: any[] = [];
        
        // Load chat history
        const chatResponse = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/chat-history`);
        if (chatResponse.ok) {
          const data = await chatResponse.json();
          const chatHistory = data.chat_history || [];

          // Convert database records to conversation history format
          if (chatHistory.length > 0) {
            conversationHistory = chatHistory.flatMap((msg: any) => {
              const items = [];
              
              // Add user prompt
              items.push({
                id: `msg-${msg.id}`,
                type: 'user_prompt' as const,
                content: msg.user_prompt,
                timestamp: new Date(msg.timestamp).getTime(),
              });

              // Add AI response
              if (msg.ai_response) {
                items.push({
                  id: `response-${msg.id}`,
                  type: msg.intent === 'chat' ? 'chat_response' : 'narrative',
                  content: msg.ai_response,
                  timestamp: new Date(msg.timestamp).getTime(),
                });
              }

              return items;
            });
          }
        }

        // Load files with content
        const filesResponse = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/files-with-content`);
        if (filesResponse.ok) {
          const filesData = await filesResponse.json();
          const filesMap = new Map<string, any>();
          
          for (const file of filesData.files) {
            // Store the actual content directly, not wrapped in an object
            filesMap.set(file.path, file.content);
          }
          
          if (filesMap.size > 0) {
            setFiles(filesMap);
            // Initialize agent state with loaded data
            initializeState(conversationHistory, filesMap);
          } else if (conversationHistory.length > 0) {
            // Initialize agent state with conversation history only
            initializeState(conversationHistory, new Map());
          }
        } else if (conversationHistory.length > 0) {
          // Initialize agent state with conversation history only
          initializeState(conversationHistory, new Map());
        }
      } catch (error) {
        console.error('Failed to load project data:', error);
      }
    };

    loadProjectData();
  }, [projectId]);

  // Initialize agent with prompt from navigation state if available
  useEffect(() => {
    const state = location.state as { prompt?: string } | null;
    if (state?.prompt && !agentState.isStreaming && agentState.files.size === 0) {
      // Prompt was already sent from Index.tsx, agent should be streaming
      // This effect just ensures we're ready to display results
    }
  }, [location.state, agentState.isStreaming, agentState.files.size]);

  useEffect(() => {
    // Only combine files if we have agent-generated files and they're not already in the files state
    // This prevents overriding the loaded files from database
    if (agentState.files.size > 0) {
      let shouldUpdate = false;
      // Create a new Map instance to ensure React detects the change
      const combinedFiles = new Map(files);
      
      agentState.files.forEach((content, path) => {
        // Store content directly as string
        if (!combinedFiles.has(path)) {
          combinedFiles.set(path, content);
          shouldUpdate = true;
        } else {
          // Also update existing files if content has changed
          const existingFile = combinedFiles.get(path);
          if (existingFile !== content) {
            combinedFiles.set(path, content);
            shouldUpdate = true;
          }
        }
      });
      
      if (shouldUpdate) {
        setFiles(combinedFiles);
      }
    }
  }, [agentState.files]);

  useEffect(() => {
    if (agentState.activeFile) {
      setSelectedFile(agentState.activeFile);
      const fileContent = agentState.files.get(agentState.activeFile);
      // Handle content directly as string
      setEditorContent(fileContent || '');
    }
  }, [agentState.activeFile, agentState.files]);

  // Effect to detect when code generation is complete and trigger refresh
  useEffect(() => {
    if (!agentState.isStreaming && agentState.files.size > 0) {
      // Force a re-render of the file tree by updating the files state
      // This ensures the file tree automatically refreshes after code generation
      setFiles(prevFiles => {
        const newFiles = new Map(prevFiles);
        let hasChanges = false;
        
        // Update files with agent-generated content
        agentState.files.forEach((content, path) => {
          const existingFile = newFiles.get(path);
          // Store content directly as string
          if (existingFile !== content) {
            newFiles.set(path, content);
            hasChanges = true;
          }
        });
        
        return hasChanges ? newFiles : prevFiles;
      });
    }
  }, [agentState.isStreaming, agentState.files]);

  const [projectName, setProjectName] = useState<string>('Frontend-Only Project');

  // Add handler for project name change
  const handleProjectNameChange = (name: string) => {
    setProjectName(name);
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setEditorContent(value);
      const currentContent = files.get(selectedFile);
      // Handle content directly as string
      let existingContent = '';
      if (currentContent !== undefined && currentContent !== null) {
        existingContent = String(currentContent);
      }
      setHasUnsavedChanges(value !== existingContent);
    }
  };

  const saveCurrentFile = async (): Promise<void> => {
    if (selectedFile) {
      console.log(`File "${selectedFile}" would be saved here.`);
      setHasUnsavedChanges(false);
    }
  };

  const shouldShowFileExplorer = useCallback(() => {
    return showFileExplorer && files.size > 0;
  }, [showFileExplorer, files.size]);

  // Convert files Map to object structure
  const projectFiles = useMemo(() => {
    const filesObj: Record<string, string> = {};
    files.forEach((value, key) => {
      // Ensure value is a string
      filesObj[key] = value !== undefined && value !== null ? String(value) : '';
    });
    return filesObj;
  }, [files]);

  // Build tree structure for file explorer
  const buildStructure = useCallback((filesMap: Map<string, any>) => {
    const root: any = { type: 'folder', name: '', children: [] };
    
    for (const fullPath of filesMap.keys()) {
      // Skip null or empty paths
      if (!fullPath) continue;
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
  }, []);

  const handlePreviewLoad = useCallback((success: boolean) => {
    console.log('Preview load status:', success);
  }, []);

  const handleFollowUpMessage = useCallback((message: string) => {
    // Send follow-up message to agent with project ID
    sendMessage(message, projectId);
    // Already on editor page, no redirect needed
  }, [sendMessage, projectId]);

  // New function to handle creating a new project
  const handleNewProject = useCallback(() => {
    const newProjectId = generateProjectId();
    // Update the URL with the new project ID to refresh the page with new data
    setSearchParams({ projectId: newProjectId });
    
    // Reset the editor state for a fresh start
    setFiles(new Map());
    setSelectedFile('');
    setEditorContent('// Welcome to the editor!\n// Select a file to start editing.');
    setHasUnsavedChanges(false);
    initializeState([], new Map());
  }, [setSearchParams, initializeState]);

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="h-screen bg-background flex flex-col w-full">
        <EditorHeader
          projectName={projectName}
          showFileExplorer={shouldShowFileExplorer()}
          onToggleFileExplorer={() => setShowFileExplorer(!showFileExplorer)}
          onNewProject={handleNewProject}
          onProjectNameChange={handleProjectNameChange}
        />

        <div className="flex-1 overflow-hidden">
          <ResizablePanelGroup direction="horizontal" className="h-full">
            {/* AI Assistant Panel - Resizable */}
            <ResizablePanel defaultSize={25} minSize={15} maxSize={40} className="border-r">
              <AIAssistantPanel 
                showAIAssistant={true} 
                agentState={agentState}
                onSendMessage={handleFollowUpMessage}
              />
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
                    isStreaming={agentState.isStreaming}
                    streamingContent={agentState.activeFile ? agentState.files.get(agentState.activeFile) || '' : ''}
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
                          const fileContent = files.get(path);
                          // Handle content directly as string
                          setEditorContent(fileContent ? String(fileContent) : '');
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