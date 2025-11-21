import React from 'react';

interface AIProgressData {
  type: 'ai_progress';
  status: 'analyzing' | 'planning' | 'coding' | 'validating' | 'complete' | 'error';
  message: string;
  details?: {
    phase?: string;
    progress?: number;
    estimated_time?: string;
    files_created?: string[];
    file_count?: number;
    error_type?: string;
    original_error?: string;
  };
  timestamp: string;
}

interface AIProgressDisplayProps {
  progress: AIProgressData | null;
  initialPrompt?: string;
}

export const AIProgressDisplay: React.FC<AIProgressDisplayProps> = ({ 
  progress, 
  initialPrompt 
}) => {
  if (!progress && !initialPrompt) return null;

  // Determine if we're in a streaming state
  const isStreaming = progress?.status === 'coding' && progress?.details?.phase === 'Generating Code';

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-5 my-4">
      {/* Initial Prompt Display */}
      {initialPrompt && (
        <div className="mb-5 pb-4 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-2">Your Request</h3>
          <div className="bg-white border border-gray-300 rounded-md p-3">
            <p className="text-gray-600 italic leading-relaxed m-0">"{initialPrompt}"</p>
          </div>
        </div>
      )}

      {/* Progress Display */}
      {progress && (
        <div>
          <div>
            <h3 className="text-gray-600 font-semibold mb-3">AI Assistant</h3>
            {progress.details?.progress !== undefined && !isStreaming && (
              <div className="w-full h-1 bg-gray-200 rounded-full overflow-hidden mb-4">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-700 transition-all duration-300 ease-out" 
                  style={{ width: `${progress.details.progress}%` }}
                />
              </div>
            )}
          </div>
          
          <div className="my-4">
            <p className="text-gray-600 leading-relaxed m-0">{progress.message}</p>
            {isStreaming && (
              <div className="flex items-center mt-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
                <span className="text-sm text-gray-500 ml-2">Generating code...</span>
              </div>
            )}
          </div>
          
          <div className="flex justify-between text-sm text-gray-500 mt-3">
            {progress.details?.phase && (
              <span className="font-medium">{progress.details.phase}</span>
            )}
            {progress.details?.estimated_time && (
              <span className="italic">{progress.details.estimated_time}</span>
            )}
          </div>

          {/* Files Created Display */}
          {progress.details?.files_created && progress.details.files_created.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-600 mb-2">Files Created:</h4>
              <ul className="space-y-1">
                {progress.details.files_created.map((file, index) => (
                  <li key={index} className="text-sm text-gray-500 flex items-center">
                    <span className="text-green-500 font-bold mr-2">✓</span>
                    {file}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
