import { useState } from "react";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { MessageSquare, Code } from "lucide-react";

interface ModeToggleProps {
  mode: 'chat' | 'code';
  onModeChange: (mode: 'chat' | 'code') => void;
}

export const ModeToggle = ({ mode, onModeChange }: ModeToggleProps) => {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">Mode:</span>
      <ToggleGroup 
        type="single" 
        value={mode}
        onValueChange={(value: 'chat' | 'code') => value && onModeChange(value)}
        className="gap-0"
      >
        <ToggleGroupItem 
          value="chat" 
          className="h-7 px-2 text-xs rounded-r-none border-r-0 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
          title="Chat Mode"
        >
          <MessageSquare className="w-3 h-3 mr-1" />
          Chat
        </ToggleGroupItem>
        <ToggleGroupItem 
          value="code" 
          className="h-7 px-2 text-xs rounded-l-none border-l data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
          title="Code Generation Mode"
        >
          <Code className="w-3 h-3 mr-1" />
          Code
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
};