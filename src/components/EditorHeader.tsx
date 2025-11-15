import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SidebarTrigger } from "@/components/ui/sidebar";

import { 
  Download, 
  Github, 
  Play, 
  FolderTree, 
  Code2, 
  Smartphone,
  MoreHorizontal,
  Settings,
  PanelLeftClose,
  PanelRightClose,
  ExternalLink
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface EditorHeaderProps {
  projectName: string;
  showFileExplorer: boolean;
  onToggleFileExplorer: () => void;
  currentProject?: any;
}

export const EditorHeader = ({ 
  projectName, 
  showFileExplorer, 
  onToggleFileExplorer, 
  currentProject
}: EditorHeaderProps) => {
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const handlePreview = () => {
    setIsPreviewLoading(true);
    setTimeout(() => setIsPreviewLoading(false), 2000);
  };

  return (
    <header className="glass-panel border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 h-14 px-4 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-4">
        <SidebarTrigger />
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center">
            <Code2 className="w-4 h-4 text-white" />
          </div>
          <div className="flex flex-col">
            <h1 className="font-semibold text-sm leading-none">{projectName}</h1>
            <span className="text-xs text-muted-foreground">Flutter Project</span>
          </div>
        </div>
        
      </div>

      <div className="flex items-center gap-1">
        {/* Panel Controls */}
        


        <div className="w-px h-6 bg-border mx-2" />

        {/* Action Buttons */}
        

        

       

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 hover:bg-accent transition-all duration-200">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem>
              <Settings className="w-4 h-4 mr-2" />
              Project Settings
            </DropdownMenuItem>
            <DropdownMenuItem>
              <ExternalLink className="w-4 h-4 mr-2" />
              Documentation
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};
