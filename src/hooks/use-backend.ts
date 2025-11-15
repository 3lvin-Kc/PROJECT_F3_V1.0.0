/**
 * Backend Connection Hook
 * 
 * Manages overall backend connection state and health monitoring.
 */

import { useState, useEffect, useCallback } from 'react';
import { checkBackendConnection } from '@/lib/api';

export interface UseBackendReturn {
  isConnected: boolean;
  isChecking: boolean;
  lastCheck: Date | null;
  error: string | null;
  checkConnection: () => Promise<boolean>;
  retryConnection: () => Promise<void>;
}

export const useBackend = (): UseBackendReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkConnection = useCallback(async (): Promise<boolean> => {
    setIsChecking(true);
    setError(null);

    try {
      const connected = await checkBackendConnection();
      setIsConnected(connected);
      setLastCheck(new Date());
      
      if (!connected) {
        setError('Backend server is not responding');
      }
      
      return connected;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection check failed';
      setError(errorMessage);
      setIsConnected(false);
      setLastCheck(new Date());
      return false;
    } finally {
      setIsChecking(false);
    }
  }, []);

  const retryConnection = useCallback(async (): Promise<void> => {
    await checkConnection();
  }, [checkConnection]);

  // Initial connection check
  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  // Periodic health check (every 30 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isChecking) {
        checkConnection();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [checkConnection, isChecking]);

  return {
    isConnected,
    isChecking,
    lastCheck,
    error,
    checkConnection,
    retryConnection
  };
};
