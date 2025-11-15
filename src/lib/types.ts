/**
 * TypeScript interfaces for backend communication
 * 
 * These match the dataclass models in the backend for type safety.
 */

// Enums matching backend
export enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SYSTEM = "system"
}

export enum IntentType {
  CHAT = "chat",
  CODE = "code",
  EXPLAIN = "explain",
  ERROR_CLARIFICATION = "error"
}

export enum ModeType {
  CHAT_MODE = "chat",
  CODE_MODE = "code"
}

export enum ErrorSeverity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high"
}

// Message Types
export interface ChatMessage {
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  project_context?: Record<string, any>;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  mode: ModeType;
  files_changed?: string[];
  preview_update_required?: boolean;
  error?: string;
  metadata?: Record<string, any>;
}

// Intent Classification
export interface IntentClassification {
  intent: IntentType;
  confidence: number;
  suggested_mode: ModeType;
  reasoning?: string;
}

// File Operations
export interface FileRequest {
  project_id: string;
  file_path: string;
  content?: string;
}

export interface FileResponse {
  success: boolean;
  content?: string;
  error?: string;
  file_path?: string;
}

export interface FileListResponse {
  success: boolean;
  files?: string[];
  error?: string;
}

// Project Operations
export interface ProjectInfo {
  project_id: string;
  name: string;
  files: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface ProjectCreateRequest {
  project_id: string;
  name?: string;
}

// Code Operations
export interface CompileRequest {
  code: string;
  file_name?: string;
}

export interface CompileResponse {
  success: boolean;
  output?: string;
  errors?: string[];
  warnings?: string[];
}

export interface PreviewRequest {
  code: string;
  file_path: string;
}

export interface PreviewResponse {
  success: boolean;
  preview_data?: any;
  error?: string;
}

// Error Types
export interface ErrorDetails {
  error_type: string;
  severity: ErrorSeverity;
  message: string;
  file_path?: string;
  line_number?: number;
  stack_trace?: string;
  context?: string;
}

// Conversation State
export interface ConversationState {
  conversation_id: string;
  current_mode: ModeType;
  message_history: ChatMessage[];
  project_files?: Record<string, string>;
  error_history?: ErrorDetails[];
  retry_counts?: Record<string, number>;
  context?: Record<string, any>;
}

// API Response Wrappers
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Health Check Response
export interface HealthCheckResponse {
  status: string;
  agents: {
    intent_classifier: string;
    planning_agent: string;
    coding_agent: string;
    error_recovery_agent: string;
    chat_agent: string;
  };
  services: {
    compiler: string;
    file_service: string;
    preview: string;
    project_manager: string;
  };
  statistics?: Record<string, any>;
}

// Hook State Types
export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  conversationId?: string;
}

export interface FileState {
  files: Map<string, any>;
  isLoading: boolean;
  error: string | null;
  selectedFile?: string;
}

export interface ProjectState {
  currentProject?: ProjectInfo;
  isLoading: boolean;
  error: string | null;
}

export interface PreviewState {
  previewCode: string;
  isLoading: boolean;
  error: string | null;
  lastUpdate?: Date;
}

// Backend Connection State
export interface BackendState {
  isConnected: boolean;
  isChecking: boolean;
  lastCheck?: Date;
  error?: string;
}
