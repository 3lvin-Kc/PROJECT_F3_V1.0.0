import { useState } from 'react';
import { AgentState, AgentStreamEvent } from '../lib/types';

const API_URL = 'http://127.0.0.1:8000/api/agent/stream';

const initialState: AgentState = {
  isStreaming: false,
  intent: null,
  conversationHistory: [],
  currentChatMessage: '',
  currentProgress: null,
  narrativeBlocks: [],
  files: new Map(),
  error: null,
  activeFile: null,
};

export const useAgent = () => {
  const [state, setState] = useState<AgentState>(initialState);

  const sendMessage = async (message: string) => {
    // Add user prompt to conversation history (don't reset state)
    const messageId = `msg-${Date.now()}`;
    setState(prev => ({
      ...prev,
      isStreaming: true,
      conversationHistory: [
        ...prev.conversationHistory,
        {
          id: messageId,
          type: 'user_prompt',
          content: message,
          timestamp: Date.now(),
        }
      ],
      currentChatMessage: '',
      currentProgress: null,
    }));

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentResponseId = `response-${Date.now()}`;
      let accumulatedResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6);
            try {
              const event: AgentStreamEvent = JSON.parse(data);
              setState(prev => {
                const newState = { ...prev };
                switch (event.event) {
                  case 'intent.classified':
                    newState.intent = event.intent;
                    break;
                  case 'chat.chunk':
                    // Accumulate chat content
                    if (newState.intent === 'chat') {
                      newState.currentChatMessage += event.content;
                      accumulatedResponse += event.content;
                    }
                    break;
                  case 'design.phase':
                    // Design narration shows in AI panel for code intent
                    if (newState.intent === 'code') {
                      newState.currentProgress = event.details;
                      // Add progress to history
                      if (!newState.conversationHistory.find(m => m.id === `progress-${event.details}`)) {
                        newState.conversationHistory = [
                          ...newState.conversationHistory,
                          {
                            id: `progress-${Date.now()}`,
                            type: 'progress',
                            content: event.details,
                            timestamp: Date.now(),
                          }
                        ];
                      }
                    }
                    break;
                  case 'design.completed':
                    if (newState.intent === 'code') {
                      newState.currentProgress = 'Design complete, generating code...';
                    }
                    break;
                  case 'code.started':
                    if (newState.intent === 'code') {
                      newState.currentProgress = 'Generating code...';
                    }
                    break;
                  case 'code.file_started':
                    // Create a new Map to ensure React detects the change
                    const filesWithNewFile = new Map(prev.files);
                    filesWithNewFile.set(event.file, '');
                    newState.files = filesWithNewFile;
                    newState.activeFile = event.file;
                    break;
                  case 'code.chunk':
                    // Create a new Map to ensure React detects the change
                    const updatedFiles = new Map(prev.files);
                    const currentContent = updatedFiles.get(event.file) || '';
                    updatedFiles.set(event.file, currentContent + event.content);
                    newState.files = updatedFiles;
                    break;
                  case 'file.create':
                    // Create a new Map to ensure React detects the change
                    const filesWithCreatedFile = new Map(prev.files);
                    filesWithCreatedFile.set(event.path, '');
                    newState.files = filesWithCreatedFile;
                    newState.activeFile = event.path;
                    break;
                  case 'file.chunk':
                    // Create a new Map to ensure React detects the change
                    const filesWithChunk = new Map(prev.files);
                    const fileContent = filesWithChunk.get(event.path) || '';
                    filesWithChunk.set(event.path, fileContent + event.content);
                    newState.files = filesWithChunk;
                    break;
                  case 'file.narrative':
                    if (newState.intent === 'code') {
                      const newBlock = {
                        id: prev.narrativeBlocks.length,
                        type: 'narrative' as const,
                        content: event.narrative,
                      };
                      newState.narrativeBlocks = [...prev.narrativeBlocks, newBlock];
                      // Add narrative to conversation history
                      newState.conversationHistory = [
                        ...newState.conversationHistory,
                        {
                          id: `narrative-${Date.now()}-${newBlock.id}`,
                          type: 'narrative',
                          content: event.narrative,
                          timestamp: Date.now(),
                        }
                      ];
                    }
                    break;
                  case 'pipeline.completed':
                    newState.activeFile = null;
                    newState.currentProgress = null;
                    // Add final response to history if it's a chat
                    if (newState.intent === 'chat' && accumulatedResponse) {
                      newState.conversationHistory = [
                        ...newState.conversationHistory,
                        {
                          id: currentResponseId,
                          type: 'chat_response',
                          content: accumulatedResponse,
                          timestamp: Date.now(),
                        }
                      ];
                    }
                    break;
                }
                return newState;
              });
            } catch (e) {
              console.error('Failed to parse event:', data);
            }
          }
        }
      }
    } catch (error) {
      setState(prev => ({ ...prev, error: 'Failed to connect to the agent service.' }));
    } finally {
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  };

  return { state, sendMessage };
};