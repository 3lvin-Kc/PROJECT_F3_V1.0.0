
import { useState } from "react";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from "lucide-react";

interface FileTreeProps {
  files: any;
  selectedFile: string;
  onFileSelect: (file: string) => void;
}

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  path?: string;
}

const FileTreeItem = ({ 
  node, 
  depth = 0, 
  selectedFile, 
  onFileSelect 
}: { 
  node: FileNode; 
  depth?: number; 
  selectedFile: string;
  onFileSelect: (file: string) => void;
}) => {
  const [isExpanded, setIsExpanded] = useState(depth < 2);

  const handleClick = () => {
    if (node.type === 'folder') {
      setIsExpanded(!isExpanded);
    } else if (node.path) {
      onFileSelect(node.path);
    }
  };

  const isSelected = node.path === selectedFile;

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-2 py-1.5 cursor-pointer hover:bg-accent/70 rounded-md text-sm group transition-colors duration-150 ${
          isSelected ? 'bg-accent text-accent-foreground font-medium' : 'text-foreground'
        }`}
        style={{ paddingLeft: `${depth * 12 + 12}px`, marginBottom: '2px' }}
        onClick={handleClick}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {node.type === 'folder' ? (
            <>
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0 transition-transform duration-200" />
              ) : (
                <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0 transition-transform duration-200" />
              )}
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 text-blue-500 flex-shrink-0 transition-colors duration-200" />
              ) : (
                <Folder className="w-4 h-4 text-blue-500 flex-shrink-0 transition-colors duration-200" />
              )}
            </>
          ) : (
            <>
              <div className="w-4" />
              <File className="w-4 h-4 text-primary/70 flex-shrink-0" />
            </>
          )}
          <span className="truncate">
            {node.name}
          </span>
        </div>
      </div>

      {node.type === 'folder' && isExpanded && node.children && (
        <div>
          {node.children.map((child, index) => (
            <FileTreeItem
              key={index}
              node={child}
              depth={depth + 1}
              selectedFile={selectedFile}
              onFileSelect={onFileSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const FileTree = ({ files, selectedFile, onFileSelect }: FileTreeProps) => {
  return (
    <div className="py-2">
      {files && files.length > 0 ? (
        files.map((node: FileNode, index: number) => (
          <FileTreeItem
            key={index}
            node={node}
            selectedFile={selectedFile}
            onFileSelect={onFileSelect}
          />
        ))
      ) : (
        <div className="px-4 py-6 text-center">
          <Folder className="w-8 h-8 text-muted-foreground/50 mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">No files available</p>
          <p className="text-xs text-muted-foreground/70 mt-1">Create or upload files to see them here</p>
        </div>
      )}
    </div>
  );
};
