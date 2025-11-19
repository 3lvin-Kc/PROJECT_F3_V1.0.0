

// Conversation Message Types
export interface ConversationMessage {
  id: string;
  type: 'user_prompt' | 'chat_response' | 'progress' | 'narrative';
  content: string;
  timestamp: number;
}

// Agent Streaming Events
export type AgentStreamEvent =
  | { event: 'pipeline.started' }
  | { event: 'intent.classified', intent: 'chat' | 'code' }
  | { event: 'chat.chunk', content: string }
  | { event: 'design.started' }
  | { event: 'design.phase', details: string }
  | { event: 'design.completed', files: string[] }
  | { event: 'code.started' }
  | { event: 'code.file_started', file: string }
  | { event: 'code.chunk', content: string, file: string }
  | { event: 'code.completed', files_generated?: number, error?: string }
  | { event: 'file.create', path: string }
  | { event: 'file.chunk', path: string, content: string }
  | { event: 'file.narrative', path: string, narrative: string }
  | { event: 'file.complete', path: string }
  | { event: 'pipeline.completed' };

// State for the useAgent hook
export interface AgentState {
  isStreaming: boolean;
  intent: 'chat' | 'code' | null;
  conversationHistory: ConversationMessage[];
  currentChatMessage: string;
  currentProgress: string | null;
  narrativeBlocks: { id: number; type: 'narrative'; content: string }[];
  files: Map<string, string>;
  error: string | null;
  activeFile: string | null;
}
