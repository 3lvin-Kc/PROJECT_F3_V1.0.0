/**
 * WebSocket Hook for F3 Platform
 * Handles real-time AI progress updates
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export interface AIProgressUpdate {
  type: 'ai_progress';
  conversation_id: string;
  status: 'analyzing' | 'planning' | 'coding' | 'validating' | 'compiling' | 'complete' | 'error';
  message: string;
  timestamp: string;
  details?: any;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  url?: string;
  clientId: string;
  conversationId?: string;
  onAIProgress?: (update: AIProgressUpdate) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
}

export const useWebSocket = ({
  url = 'ws://localhost:8000/ws',
  clientId,
  conversationId,
  onAIProgress,
  onMessage,
  onError,
  autoReconnect = true
}: UseWebSocketOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [aiStatus, setAiStatus] = useState<string>('');
  const [aiMessage, setAiMessage] = useState<string>('');
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    
    try {
      const wsUrl = `${url}/${clientId}`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('F3 WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;

        // Join conversation if provided
        if (conversationId) {
          ws.current?.send(JSON.stringify({
            type: 'join_conversation',
            conversation_id: conversationId
          }));
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Handle AI progress updates
          if (message.type === 'ai_progress') {
            const progressUpdate = message as AIProgressUpdate;
            setAiStatus(progressUpdate.status);
            setAiMessage(progressUpdate.message);
            onAIProgress?.(progressUpdate);
          }

          // Call general message handler
          onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = () => {
        console.log('F3 WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        setAiStatus('');
        setAiMessage('');

        // Auto-reconnect if enabled
        if (autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectAttempts.current++;
          
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      ws.current.onerror = (error) => {
        console.error('F3 WebSocket error:', error);
        setConnectionStatus('error');
        onError?.(error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [url, clientId, conversationId, onAIProgress, onMessage, onError, autoReconnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
    setAiStatus('');
    setAiMessage('');
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  const joinConversation = useCallback((newConversationId: string) => {
    sendMessage({
      type: 'join_conversation',
      conversation_id: newConversationId
    });
  }, [sendMessage]);

  const leaveConversation = useCallback((conversationIdToLeave: string) => {
    sendMessage({
      type: 'leave_conversation',
      conversation_id: conversationIdToLeave
    });
  }, [sendMessage]);

  // Connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    aiStatus,
    aiMessage,
    connect,
    disconnect,
    sendMessage,
    joinConversation,
    leaveConversation
  };
};
