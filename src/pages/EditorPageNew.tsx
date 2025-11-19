import { useState, useCallback, useEffect } from "react";
import { useAgent } from "@/hooks/use-agent";
import { useLocation, useSearchParams } from "react-router-dom";
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

  // Agent State
  const [projectId, setProjectId] = useState<string>('');
  const { state: agentState, sendMessage } = useAgent(projectId);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const location = useLocation();
  const [searchParams] = useSearchParams();

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

  // Load chat history from database when project ID is set
  useEffect(() => {
    const loadChatHistory = async () => {
      if (!projectId) return;

      try {
        const response = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/chat-history`);
        if (!response.ok) return;

        const data = await response.json();
        const chatHistory = data.chat_history || [];

        // Convert database records to conversation history format
        if (chatHistory.length > 0) {
          const conversationHistory = chatHistory.flatMap((msg: any) => {
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

          // Update agent state with loaded history
          // Note: We'll need to use sendMessage or update state directly
          // For now, we'll store this in a way that the agent can access it
          sessionStorage.setItem(`chatHistory_${projectId}`, JSON.stringify(conversationHistory));
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    };

    loadChatHistory();
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
    // Combine initial files with agent-generated files
    // Create a new Map to ensure React detects the change
    const combinedFiles = new Map(files);
    agentState.files.forEach((content, path) => {
      combinedFiles.set(path, { content });
    });
    setFiles(combinedFiles);
  }, [agentState.files]);

  useEffect(() => {
    if (agentState.activeFile) {
      setSelectedFile(agentState.activeFile);
      setEditorContent(agentState.files.get(agentState.activeFile) || '');
    }
  }, [agentState.activeFile, agentState.files]);
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
  };

  const handlePreviewLoad = useCallback((success: boolean) => {
    console.log('Preview load status:', success);
  }, []);

  const handleFollowUpMessage = useCallback((message: string) => {
    // Send follow-up message to agent with project ID
    sendMessage(message, projectId);
    // Already on editor page, no redirect needed
  }, [sendMessage, projectId]);

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