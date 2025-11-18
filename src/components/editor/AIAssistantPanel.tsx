import { Sparkles } from "lucide-react";

interface AIAssistantPanelProps {
  showAIAssistant: boolean;
}

export const AIAssistantPanel = ({ showAIAssistant }: AIAssistantPanelProps) => {
  if (!showAIAssistant) return null;

  return (
    <div className="w-full h-full flex flex-col min-w-0">
      <div className="h-10 px-3 border-b flex items-center bg-sidebar flex-shrink-0">
        <Sparkles className="w-4 h-4 text-primary mr-2 flex-shrink-0" />
        <span className="text-sm font-medium truncate">AI Assistant</span>
      </div>
      <div className="flex-1 flex flex-col overflow-hidden min-h-0 p-4">
        <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground px-2">
          <Sparkles className="w-8 h-8 sm:w-12 sm:h-12 mb-3 opacity-50 flex-shrink-0" />
          <p className="text-xs sm:text-sm mb-1 font-medium break-words">AI Assistant Disabled</p>
          <p className="text-xs break-words">The backend has been removed, so the AI assistant is no longer available.</p>
        </div>
      </div>
    </div>
  );
};
