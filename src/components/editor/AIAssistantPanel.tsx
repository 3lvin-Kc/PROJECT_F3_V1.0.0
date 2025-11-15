import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Sparkles, Send, AlertCircle, RotateCcw } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChat } from "@/hooks/use-chat";
import { MessageRole } from "@/lib/types";
import { AIProgressDisplay } from "./AIProgressDisplay";

interface AIAssistantPanelProps {
  showAIAssistant: boolean;
}

export const AIAssistantPanel = ({ showAIAssistant }: AIAssistantPanelProps) => {
  const [input, setInput] = useState("");
  const [searchParams] = useSearchParams();
  const [aiProgress, setAiProgress] = useState<any>(null);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  
  const { messages, isLoading, error, sendMessage, clearError, retryLastMessage } = useChat();
  
  // Get initial prompt from URL
  const initialPrompt = searchParams.get('prompt');
  const conversationId = searchParams.get('conversation');
  const projectId = searchParams.get('project');

  // WebSocket connection for real-time progress updates
  useEffect(() => {
    if (conversationId || projectId) {
      const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected for AI progress updates');
        if (conversationId) {
          ws.send(JSON.stringify({
            type: 'join_conversation',
            conversation_id: conversationId
          }));
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'ai_progress') {
            setAiProgress(data);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      setWebsocket(ws);
      
      return () => {
        ws.close();
      };
    }
  }, [conversationId, projectId]);
  
  // Trigger initial AI generation if we have a prompt but no messages yet
  useEffect(() => {
    if (initialPrompt && messages.length === 0 && !isLoading && projectId && conversationId) {
      const context = {
        project_id: projectId,
        conversation_id: conversationId
      };
      sendMessage(initialPrompt, context).catch(err => {
        console.error('Failed to send initial prompt:', err);
      });
    }
  }, [initialPrompt, messages.length, isLoading, projectId, conversationId, sendMessage]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    if (!projectId || !conversationId) {
      window.alert('Missing project context. Please create a project from the home page first.');
      return;
    }
    
    const message = input.trim();
    setInput("");
    
    try {
      const context = {
        project_id: projectId,
        conversation_id: conversationId
      };
      await sendMessage(message, context);
    } catch (err) {
      // Error is handled by the hook
      console.error('Failed to send message:', err);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!showAIAssistant) return null;

  return (
    <div className="w-full h-full flex flex-col min-w-0">
      {/* Header - Responsive */}
      <div className="h-10 px-3 border-b flex items-center bg-sidebar flex-shrink-0">
        <Sparkles className="w-4 h-4 text-primary mr-2 flex-shrink-0" />
        <span className="text-sm font-medium truncate">AI Assistant</span>
        {error && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearError}
            className="ml-auto h-6 w-6 p-0"
          >
            <AlertCircle className="w-3 h-3 text-destructive" />
          </Button>
        )}
      </div>


      {/* Chat Content Area - Responsive */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        <ScrollArea className="flex-1 px-2 py-3">
          {/* Show initial prompt and AI progress */}
          {(initialPrompt || aiProgress) && (
            <AIProgressDisplay 
              initialPrompt={initialPrompt || undefined}
              progress={aiProgress}
            />
          )}
          
          {/* Regular chat messages */}
          {messages.length === 0 && !initialPrompt ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground px-2">
              <Sparkles className="w-8 h-8 sm:w-12 sm:h-12 mb-3 opacity-50 flex-shrink-0" />
              <p className="text-xs sm:text-sm mb-1 font-medium break-words">AI Assistant Ready</p>
              <p className="text-xs break-words">Ask me to create Flutter widgets, explain code, or help with your project.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === MessageRole.USER ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                      message.role === MessageRole.USER
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    <p className="whitespace-pre-wrap break-words">{message.content}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-muted text-muted-foreground rounded-lg px-3 py-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-current rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                      <span>AI is working...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </ScrollArea>

        {/* Input Area - Responsive with proper button positioning */}
        <div className="px-2 py-3 border-t bg-sidebar flex-shrink-0">
          {error && (
            <div className="mb-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-xs text-destructive">
              <div className="flex items-center justify-between">
                <span>{error}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={retryLastMessage}
                  className="h-5 w-5 p-0 ml-2"
                >
                  <RotateCcw className="w-3 h-3" />
                </Button>
              </div>
            </div>
          )}
          <div className="relative flex items-end gap-2">
            <div className="flex-1 min-w-0">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Describe the widget you want to create..."
                className="min-h-[44px] max-h-36 text-sm resize-none pr-12 w-full"
                disabled={isLoading}
              />
            </div>
            <Button
              type="button"
              size="icon"
              onClick={handleSend}
              className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 flex-shrink-0"
              disabled={isLoading || !input.trim() || !projectId || !conversationId}
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <div className="mt-2 text-xs text-muted-foreground text-center break-words">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
};
