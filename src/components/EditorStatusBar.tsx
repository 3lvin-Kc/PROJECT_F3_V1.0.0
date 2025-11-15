
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  CheckCircle2, 
  AlertCircle, 
  Zap, 
  Globe,
  Wifi,
  HardDrive
} from "lucide-react";

interface EditorStatusBarProps {
  selectedFile: string;
  fileCount: number;
  showFileExplorer?: boolean;
  hasFiles?: boolean;
  onToggleFileExplorer?: () => void;
}

export const EditorStatusBar = ({ 
  selectedFile, 
  fileCount, 
  showFileExplorer = false,
  hasFiles = false,
  onToggleFileExplorer 
}: EditorStatusBarProps) => {
  return (
    <div className="h-6 bg-background/95 backdrop-blur border-t flex items-center justify-between px-4 text-xs">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-3 h-3 text-success" />
          <span className="text-muted-foreground">Ready</span>
        </div>
        <div className="flex items-center gap-1">
          <HardDrive className="w-3 h-3 text-muted-foreground" />
          <span>{fileCount} files</span>
        </div>
        {selectedFile && (
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">Editing:</span>
            <code className="bg-muted px-1 rounded text-xs">{selectedFile}</code>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        {hasFiles && (
          <button 
            onClick={onToggleFileExplorer} 
            className={`flex items-center gap-1 px-2 py-0.5 rounded hover:bg-muted transition-colors ${showFileExplorer ? 'bg-muted' : ''}`}
            title={showFileExplorer ? 'Hide file explorer' : 'Show file explorer'}
          >
            <HardDrive className="w-3 h-3 text-primary" />
            <span className="text-xs">{showFileExplorer ? 'Hide files' : 'Show files'}</span>
          </button>
        )}
        <div className="flex items-center gap-2">
          <Wifi className="w-3 h-3 text-success" />
          <span className="text-muted-foreground">Connected</span>
        </div>
        <Badge variant="outline" className="h-5 text-xs">
          <Zap className="w-3 h-3 mr-1" />
          Flutter
        </Badge>
      </div>
    </div>
  );
};
