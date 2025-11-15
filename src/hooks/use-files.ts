/**
 * Files Hook for Project File State Management
 * 
 * Manages file state and backend synchronization while maintaining
 * compatibility with existing EditorPageNew component interface.
 */

import { useState, useCallback, useEffect } from 'react';
import { fileService } from '@/lib/file-service';

export interface UseFilesOptions {
  projectId: string;
  autoLoad?: boolean;
}

export interface UseFilesReturn {
  files: Map<string, any>;
  isLoading: boolean;
  error: string | null;
  saveFile: (filePath: string, content: string) => Promise<void>;
  loadFile: (filePath: string) => Promise<string | null>;
  loadProjectFiles: () => Promise<void>;
  createFile: (filePath: string, content?: string) => void;
  deleteFile: (filePath: string) => void;
  setFiles: React.Dispatch<React.SetStateAction<Map<string, any>>>;
  clearError: () => void;
}

export const useFiles = (options: UseFilesOptions): UseFilesReturn => {
  const { projectId, autoLoad = false } = options;
  
  const [files, setFiles] = useState<Map<string, any>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const saveFile = useCallback(async (filePath: string, content: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fileService.writeFile(projectId, filePath, content);
      
      if (response.success) {
        // Update local state
        setFiles(prev => new Map(prev).set(filePath, {
          content,
          lastModified: new Date(),
          saved: true
        }));
      } else {
        throw new Error(response.error || 'Failed to save file');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save file';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const loadFile = useCallback(async (filePath: string): Promise<string | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fileService.readFile(projectId, filePath);
      
      if (response.success && response.content !== undefined) {
        // Update local state
        setFiles(prev => new Map(prev).set(filePath, {
          content: response.content,
          lastModified: new Date(),
          saved: true
        }));
        
        return response.content;
      } else {
        throw new Error(response.error || 'Failed to load file');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load file';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const loadProjectFiles = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fileService.listFiles(projectId);
      
      if (response.success && response.files) {
        // Load each file's content
        const fileMap = new Map<string, any>();
        
        for (const filePath of response.files) {
          try {
            const fileResponse = await fileService.readFile(projectId, filePath);
            if (fileResponse.success) {
              fileMap.set(filePath, {
                content: fileResponse.content || '',
                lastModified: new Date(),
                saved: true
              });
            }
          } catch (err) {
            console.warn(`Failed to load file ${filePath}:`, err);
          }
        }
        
        setFiles(fileMap);
      } else {
        throw new Error(response.error || 'Failed to load project files');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load project files';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const createFile = useCallback((filePath: string, content: string = ''): void => {
    setFiles(prev => new Map(prev).set(filePath, {
      content,
      lastModified: new Date(),
      saved: false
    }));
  }, []);

  const deleteFile = useCallback((filePath: string): void => {
    setFiles(prev => {
      const newMap = new Map(prev);
      newMap.delete(filePath);
      return newMap;
    });
  }, []);

  // Auto-load project files if requested
  useEffect(() => {
    if (autoLoad && projectId) {
      loadProjectFiles();
    }
  }, [autoLoad, projectId, loadProjectFiles]);

  return {
    files,
    isLoading,
    error,
    saveFile,
    loadFile,
    loadProjectFiles,
    createFile,
    deleteFile,
    setFiles,
    clearError
  };
};
