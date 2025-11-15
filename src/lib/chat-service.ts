/**
 * Chat Service for AI Assistant Communication
 * 
 * Handles all chat-related API calls to the backend.
 */

import { apiClient } from './api';
import type { 
  ChatRequest, 
  ChatResponse, 
  IntentClassification,
  ConversationState 
} from './types';

export class ChatService {
  /**
   * Send a message to the AI assistant
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>('/api/chat', request);
  }

  /**
   * Test intent classification (for debugging)
   */
  async testIntentClassification(message: string): Promise<IntentClassification> {
    return apiClient.post<IntentClassification>('/api/test/intent', { message });
  }

  /**
   * Get conversation statistics
   */
  async getConversationStats(conversationId: string): Promise<any> {
    return apiClient.get(`/api/conversation/${conversationId}/stats`);
  }

  /**
   * Clear a conversation
   */
  async clearConversation(conversationId: string): Promise<{ message: string }> {
    return apiClient.delete(`/api/conversation/${conversationId}`);
  }

  /**
   * Set conversation mode
   */
  async setMode(conversationId: string, mode: 'chat' | 'code'): Promise<any> {
    return apiClient.post('/api/mode/set', {
      conversation_id: conversationId,
      mode
    });
  }

  /**
   * Get system statistics
   */
  async getSystemStats(): Promise<any> {
    return apiClient.get('/api/stats');
  }
}

// Singleton instance
export const chatService = new ChatService();
