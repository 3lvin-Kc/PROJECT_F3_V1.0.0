import { useState, useRef, useEffect } from 'react';
import { Sparkles, Send, Loader2 } from 'lucide-react';
import { AgentState } from '@/lib/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface AIAssistantPanelProps {
  showAIAssistant: boolean;
  agentState: AgentState;
  onSendMessage: (message: string) => void;
}

export const AIAssistantPanel = ({ showAIAssistant, agentState, onSendMessage }: AIAssistantPanelProps) => {
  const [inputValue, setInputValue] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        setTimeout(() => {
          scrollElement.scrollTop = scrollElement.scrollHeight;
        }, 0);
      }
    }
  }, [agentState.conversationHistory, agentState.currentChatMessage, agentState.currentProgress]);

  if (!showAIAssistant) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  return (
    <div className="w-full h-full flex flex-col min-w-0">
      <div className="h-10 px-3 border-b flex items-center bg-sidebar flex-shrink-0">
        <Sparkles className="w-4 h-4 text-primary mr-2 flex-shrink-0" />
        <span className="text-sm font-medium truncate">AI Assistant</span>
      </div>
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-3">
          {/* Display full conversation history */}
          {agentState.conversationHistory.map((msg) => {
            if (msg.type === 'user_prompt') {
              return (
                <div key={msg.id} className="flex justify-end">
                  <div className="max-w-xs px-3 py-2 bg-primary/15 dark:bg-primary/25 rounded-lg text-sm text-foreground border border-primary/30">
                    <p>{msg.content}</p>
                  </div>
                </div>
              );
            } else if (msg.type === 'narrative') {
              return (
                <div key={msg.id} className="flex justify-start">
                  <div className="max-w-xs px-3 py-2 bg-muted/60 dark:bg-muted/40 rounded-lg text-xs text-muted-foreground border border-border/50">
                    <p>{msg.content}</p>
                  </div>
                </div>
              );
            } else if (msg.type === 'chat_response') {
              return (
                <div key={msg.id} className="flex justify-start">
                  <div className="max-w-xs px-3 py-2 bg-secondary/50 dark:bg-secondary/30 rounded-lg text-sm text-foreground">
                    <p>{msg.content}</p>
                  </div>
                </div>
              );
            }
            return null;
          })}

          {/* Show current streaming chat response with inline spinner */}
          {agentState.isStreaming && agentState.currentChatMessage && (
            <div className="flex justify-start">
              <div className="max-w-xs px-3 py-2 bg-secondary/50 dark:bg-secondary/30 rounded-lg text-sm text-foreground">
                <p>{agentState.currentChatMessage}</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">generating...</span>
                </div>
              </div>
            </div>
          )}

          {/* Minimal progress indicator - only show when streaming and no chat message */}
          {agentState.isStreaming && !agentState.currentChatMessage && agentState.currentProgress && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-pulse" />
                <span>{agentState.currentProgress}</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
      <div className="p-2 border-t">
        <form onSubmit={handleSubmit} className="flex items-center space-x-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask the AI to build or chat..."
            disabled={agentState.isStreaming}
          />
          <Button type="submit" size="icon" disabled={agentState.isStreaming}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
};
