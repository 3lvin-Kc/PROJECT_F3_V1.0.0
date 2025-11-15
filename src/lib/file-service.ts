/**
 * File Service for Project File Management
 * 
 * Handles all file-related API calls to the backend.
 */

import { apiClient } from './api';
import type { 
  FileRequest, 
  FileResponse, 
  FileListResponse,
  ProjectCreateRequest,
  ProjectInfo 
} from './types';

export class FileService {
  /**
   * Write/update a file
   */
  async writeFile(projectId: string, filePath: string, content: string): Promise<FileResponse> {
    return apiClient.post<FileResponse>('/api/file/write', {
      project_id: projectId,
      file_path: filePath,
      content
    });
  }

  /**
   * Read a file
   */
  async readFile(projectId: string, filePath: string): Promise<FileResponse> {
    return apiClient.post<FileResponse>('/api/file/read', {
      project_id: projectId,
      file_path: filePath
    });
  }

  /**
   * List files in a project directory
   */
  async listFiles(projectId: string, directory: string = ''): Promise<FileListResponse> {
    const endpoint = `/api/project/${projectId}/files${directory ? `?directory=${encodeURIComponent(directory)}` : ''}`;
    return apiClient.get<FileListResponse>(endpoint);
  }

  /**
   * Create a new project
   */
  async createProject(projectId: string, name?: string): Promise<any> {
    return apiClient.post('/api/project/create', {
      project_id: projectId,
      name
    });
  }

  /**
   * Get project information
   */
  async getProjectInfo(projectId: string): Promise<ProjectInfo> {
    return apiClient.get<ProjectInfo>(`/api/project/${projectId}`);
  }

  /**
   * Delete a project
   */
  async deleteProject(projectId: string): Promise<any> {
    return apiClient.delete(`/api/project/${projectId}`);
  }
}

// Singleton instance
export const fileService = new FileService();
