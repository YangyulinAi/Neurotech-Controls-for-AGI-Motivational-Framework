import { useEffect, useRef, useState, useCallback } from 'react';
import { BciDataPoint, ConnectionStatus, WebSocketMessage } from '@/types/bci';
import { useToast } from '@/hooks/use-toast';

export function useWebSocket() {
  const { toast } = useToast();
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    lastUpdate: null,
    error: null,
  });
  
  const [currentData, setCurrentData] = useState<BciDataPoint | null>(null);
  const [dataHistory, setDataHistory] = useState<BciDataPoint[]>([]);
  const [totalDataPoints, setTotalDataPoints] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const maxHistorySize = 3600; // Keep 30 minutes at 2 Hz

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setConnectionStatus({
          connected: true,
          lastUpdate: new Date(),
          error: null,
        });

        // Clear any existing reconnection timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }

        // Start keepalive ping every 30 seconds
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // Debug log for incoming messages
          console.log('Received WebSocket message:', message);

          // Handle analysis completion notification
          if (message.type === 'analysis_complete') {
            toast({
              title: 'Analysis Complete',
              description: `Real data analysis finished for ${message.filename}`,
              duration: 5000,
            });
            return;
          }

          if (typeof message.valence === 'number' && typeof message.arousal === 'number') {
            // Clamp values to valid range
            const valence = Math.max(-1, Math.min(1, message.valence));
            const arousal = Math.max(-1, Math.min(1, message.arousal));

            console.log('Processing data point:', { valence, arousal, original: { valence: message.valence, arousal: message.arousal } });

            const dataPoint: BciDataPoint = {
              valence,
              arousal,
              timestamp: Date.now(),
            };

            setCurrentData(dataPoint);
            setTotalDataPoints(prev => prev + 1);

            setDataHistory(prev => {
              const updated = [...prev, dataPoint];
              // Keep only recent data points
              if (updated.length > maxHistorySize) {
                return updated.slice(-maxHistorySize);
              }
              return updated;
            });

            setConnectionStatus(prev => ({
              ...prev,
              lastUpdate: new Date(),
              error: null,
            }));
          } else {
            console.log('Message does not contain valid valence/arousal data:', message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error, 'Raw data:', event.data);
          setConnectionStatus(prev => ({
            ...prev,
            error: 'Invalid data received',
          }));
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus(prev => ({
          ...prev,
          connected: false,
          error: 'Connection error',
        }));
      };

      wsRef.current.onclose = (event) => {
        setConnectionStatus(prev => ({
          ...prev,
          connected: false,
        }));

        // Only reconnect if it wasn't a manual close (code 1000) and websocket still exists
        if (event.code !== 1000 && wsRef.current) {
          // Attempt to reconnect after 5 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            if (wsRef.current === null || wsRef.current.readyState === WebSocket.CLOSED) {
              connect();
            }
          }, 5000);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus({
        connected: false,
        lastUpdate: null,
        error: 'Failed to connect',
      });
    }
  }, [maxHistorySize]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  const clearHistory = useCallback(() => {
    setDataHistory([]);
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connectionStatus,
    currentData,
    dataHistory,
    totalDataPoints,
    clearHistory,
    reconnect: connect,
  };
}
