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
  
  const [dataFlowStatus, setDataFlowStatus] = useState<{
    isReceivingData: boolean;
    lastDataTime: Date | null;
    analysisActive: boolean;
  }>({
    isReceivingData: false,
    lastDataTime: null,
    analysisActive: false,
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
          
          // Enhanced debug logging for production troubleshooting
          console.log('=== WebSocket Message Debug ===');
          console.log('Raw event data:', event.data);
          console.log('Parsed message:', message);
          console.log('Message type:', message.type);
          console.log('Message keys:', Object.keys(message));
          console.log('Current environment:', {
            protocol: window.location.protocol,
            host: window.location.host,
            pathname: window.location.pathname
          });

          // Handle connection notification
          if (message.type === 'connection') {
            console.log('=== WebSocket Connection Message ===');
            console.log('Connection message:', message.message);
            console.log('Connection timestamp:', message.timestamp);
            console.log('Connection established successfully');
            setConnectionStatus(prev => ({
              ...prev,
              lastUpdate: new Date(),
              error: null,
            }));
            return;
          }

          // Handle analysis completion notification
          if (message.type === 'analysis_complete') {
            toast({
              title: 'Analysis Complete',
              description: `Real data analysis finished for ${message.filename}`,
              duration: 5000,
            });
            
            // Update analysis status
            setDataFlowStatus(prev => ({
              ...prev,
              analysisActive: false,
            }));
            return;
          }

          // Handle training progress notification (just log, don't process as BCI data)
          if (message.type === 'training_progress') {
            console.log('Training progress received in main WebSocket:', message);
            return;
          }

          // Handle different message formats from Python analysis
          if (message.type === 'bci_data' || message.type === 'prediction' || (!message.type && typeof message.valence === 'number' && typeof message.arousal === 'number')) {
            console.log('=== BCI Data Processing ===');
            console.log('Raw valence:', message.valence, 'type:', typeof message.valence);
            console.log('Raw arousal:', message.arousal, 'type:', typeof message.arousal);
            console.log('Raw phi:', message.phi, 'type:', typeof message.phi);
            
            const valence = Math.max(-1, Math.min(1, message.valence));
            const arousal = Math.max(-1, Math.min(1, message.arousal));
            const phi = typeof message.phi === 'number' ? Math.max(0, message.phi) : undefined;

            console.log('Processed BCI data point:', { valence, arousal, phi });
            console.log('Data flow status before update:', dataFlowStatus);

            const dataPoint: BciDataPoint = {
              valence,
              arousal,
              phi,
              timestamp: Date.now(),
            };

            setCurrentData(dataPoint);
            setTotalDataPoints(prev => prev + 1);

            setDataHistory(prev => {
              const updated = [...prev, dataPoint];
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
            
            setDataFlowStatus(prev => ({
              ...prev,
              isReceivingData: true,
              lastDataTime: new Date(),
              analysisActive: true,
            }));
            return;
          }

          // Handle phi update messages
          if (message.type === 'phi_update' && message.payload?.phi !== undefined) {
            console.log('Received Φ update:', message.payload);
            setCurrentData(prev => {
              if (prev) {
                return {
                  ...prev,
                  phi: message.payload!.phi
                };
              }
              return prev;
            });
            return;
          }

          // Handle phi error messages
          if (message.type === 'phi_error') {
            console.log('Φ computation error:', message.payload);
            return;
          }

          // Fallback for other valence/arousal data formats
          if (typeof message.valence === 'number' && typeof message.arousal === 'number') {
            console.log('Fallback: Processing valence/arousal data via legacy format');
          } else {
            console.log('=== UNHANDLED MESSAGE DEBUG ===');
            console.log('Message format not recognized or missing valence/arousal data');
            console.log('Full message object:', message);
            console.log('Message type check results:', {
              isBciData: message.type === 'bci_data',
              isPrediction: message.type === 'prediction',
              hasValence: typeof message.valence === 'number',
              hasArousal: typeof message.arousal === 'number',
              noType: !message.type
            });
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

  // Check for data timeout (no data received for 30 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      setDataFlowStatus(prev => {
        if (prev.lastDataTime && Date.now() - prev.lastDataTime.getTime() > 30000) {
          return {
            ...prev,
            isReceivingData: false,
          };
        }
        return prev;
      });
    }, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connectionStatus,
    dataFlowStatus,
    currentData,
    dataHistory,
    totalDataPoints,
    clearHistory,
    reconnect: connect,
  };
}
