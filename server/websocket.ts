import { WebSocketServer, WebSocket } from 'ws';
import { Server } from 'http';

interface ExtendedWebSocket extends WebSocket {
  isAlive?: boolean;
}

let wss: WebSocketServer;

export function setupWebSocket(server: Server) {
  wss = new WebSocketServer({ server });
  
  // WebSocket connection handling
  wss.on('connection', (ws: ExtendedWebSocket) => {
    console.log('WebSocket client connected');
    ws.isAlive = true;
    
    // Handle pong responses for heartbeat
    ws.on('pong', () => {
      ws.isAlive = true;
    });
    
    // Handle client messages
    ws.on('message', (message) => {
      try {
        const data = JSON.parse(message.toString());
        console.log('WebSocket message received:', data);
        
        // Echo back for testing
        ws.send(JSON.stringify({
          type: 'echo',
          data: data,
          timestamp: new Date().toISOString()
        }));
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    });
    
    ws.on('close', () => {
      console.log('WebSocket client disconnected');
    });
    
    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });
  
  // Heartbeat mechanism to detect dead connections
  const heartbeatInterval = setInterval(() => {
    wss.clients.forEach((ws: ExtendedWebSocket) => {
      if (!ws.isAlive) {
        console.log('Terminating dead WebSocket connection');
        return ws.terminate();
      }
      
      ws.isAlive = false;
      ws.ping();
    });
  }, 30000); // 30 seconds
  
  // Cleanup on server close
  wss.on('close', () => {
    clearInterval(heartbeatInterval);
  });
  
  console.log('WebSocket server initialized with heartbeat monitoring');
}

export function broadcastToClients(data: any) {
  if (!wss) {
    console.error('WebSocket server not initialized');
    return { success: false, clientCount: 0 };
  }
  
  let successCount = 0;
  let failCount = 0;
  
  wss.clients.forEach((client: ExtendedWebSocket) => {
    if (client.readyState === WebSocket.OPEN) {
      try {
        client.send(JSON.stringify(data));
        successCount++;
      } catch (error) {
        console.error('Failed to send to WebSocket client:', error);
        failCount++;
      }
    }
  });
  
  return {
    success: true,
    clientCount: wss.clients.size,
    successCount,
    failCount
  };
}

export function getWebSocketStats() {
  if (!wss) {
    return { connected: false, clientCount: 0 };
  }
  
  return {
    connected: true,
    clientCount: wss.clients.size,
    activeClients: Array.from(wss.clients).filter(
      (client: ExtendedWebSocket) => client.readyState === WebSocket.OPEN
    ).length
  };
}