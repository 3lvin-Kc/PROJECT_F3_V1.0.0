import { ScrollArea } from "@/components/ui/scroll-area";
import { FileTree } from "@/components/FileTree";
import { FolderTree } from "lucide-react";

interface FileExplorerPanelProps {
  projectFiles: Record<string, string> | undefined;
  selectedFile: string;
  setSelectedFile: (path: string) => void;
  buildStructure: (filesMap: Record<string, string> | undefined) => any[];
}

export const FileExplorerPanel = ({
  projectFiles,
  selectedFile,
  setSelectedFile,
  buildStructure
}: FileExplorerPanelProps) => {
  return (
    <div className="h-full glass-panel border-l">
      <div className="h-10 px-4 border-b flex items-center justify-between bg-background/50">
        <div className="flex items-center">
          <FolderTree className="w-4 h-4 mr-2 text-primary" />
          <span className="text-sm font-medium">Files</span>
        </div>
        <div className="text-xs text-muted-foreground">
          {projectFiles ? Object.keys(projectFiles).length : 0} files
        </div>
      </div>
      <ScrollArea className="h-[calc(100%-2.5rem)] px-1 py-1">
        <FileTree
          files={buildStructure(projectFiles)}
          onFileSelect={(path) => setSelectedFile(path)}
          selectedFile={selectedFile}
        />
      </ScrollArea>
    </div>
  );
};