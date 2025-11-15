/**
 * Chat Hook for AI Assistant State Management
 * 
 * Manages chat state, messages, and backend communication.
 */

import { useState, useCallback, useRef } from 'react';
import { chatService } from '@/lib/chat-service';
import type { ChatMessage, ChatResponse, ModeType } from '@/lib/types';
import { MessageRole } from '@/lib/types';

export interface UseChatOptions {
  conversationId?: string;
  projectContext?: Record<string, any>;
}

export interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  conversationId: string | null;
  currentMode: ModeType | null;
  sendMessage: (content: string, additionalContext?: Record<string, any>) => Promise<ChatResponse | null>;
  clearMessages: () => void;
  clearError: () => void;
  retryLastMessage: () => Promise<void>;
}

export const useChat = (options: UseChatOptions = {}): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(options.conversationId || null);
  const [currentMode, setCurrentMode] = useState<ModeType | null>(null);
  
  // Keep track of the last message for retry functionality
  const lastMessageRef = useRef<string>('');

  const sendMessage = useCallback(async (content: string, additionalContext?: Record<string, any>): Promise<ChatResponse | null> => {
    if (!content.trim()) return null;

    setIsLoading(true);
    setError(null);
    lastMessageRef.current = content;

    // Add user message immediately for better UX
    const userMessage: ChatMessage = {
      role: MessageRole.USER,
      content: content.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await chatService.sendMessage({
        message: content.trim(),
        conversation_id: conversationId || additionalContext?.conversation_id || undefined,
        project_context: { ...options.projectContext, ...additionalContext }
      });

      // Add assistant response
      const assistantMessage: ChatMessage = {
        role: MessageRole.ASSISTANT,
        content: response.message,
        timestamp: new Date(),
        metadata: response.metadata
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update conversation state
      setConversationId(response.conversation_id);
      setCurrentMode(response.mode);

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      // Remove the user message that failed
      setMessages(prev => prev.slice(0, -1));
      
      console.error('Chat error:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, options.projectContext]);

  const retryLastMessage = useCallback(async (): Promise<void> => {
    if (lastMessageRef.current && !isLoading) {
      await sendMessage(lastMessageRef.current);
    }
  }, [sendMessage, isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    lastMessageRef.current = '';
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    conversationId,
    currentMode,
    sendMessage,
    clearMessages,
    clearError,
    retryLastMessage
  };
};
