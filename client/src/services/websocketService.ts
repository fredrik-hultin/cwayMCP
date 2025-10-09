import { io, Socket } from 'socket.io-client';

interface LogMessage {
  timestamp: string;
  level: 'info' | 'warn' | 'error';
  source: string;
  message: string;
  requestId?: string;
  operation?: string;
}

interface FlowMessage {
  requestId: string;
  step: string;
  source: string;
  target: string;
  operation: string;
  status: 'pending' | 'success' | 'error';
  duration?: number;
  details?: any;
}

export class WebSocketService {
  private socket: Socket | null = null;
  private isConnected = false;

  constructor(private serverUrl: string = 'http://localhost:8080') {}

  connect(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.socket) {
        this.socket.disconnect();
      }

      this.socket = io(this.serverUrl, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      this.socket.on('connect', () => {
        console.log('🔌 Connected to MCP server WebSocket');
        this.isConnected = true;
        resolve(true);
      });

      this.socket.on('disconnect', () => {
        console.log('🔌 Disconnected from MCP server WebSocket');
        this.isConnected = false;
      });

      this.socket.on('connect_error', (error) => {
        console.error('❌ WebSocket connection error:', error);
        this.isConnected = false;
        resolve(false);
      });

      // Set timeout for connection attempt
      setTimeout(() => {
        if (!this.isConnected) {
          resolve(false);
        }
      }, 3000);
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }

  onLogMessage(callback: (message: LogMessage) => void): void {
    if (this.socket) {
      this.socket.on('log_message', callback);
    }
  }

  onFlowMessage(callback: (message: FlowMessage) => void): void {
    if (this.socket) {
      this.socket.on('flow_message', callback);
    }
  }

  onServerStats(callback: (stats: any) => void): void {
    if (this.socket) {
      this.socket.on('server_stats', callback);
    }
  }

  requestHistoricalData(): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('request_historical_data');
    }
  }

  getConnectionStatus(): boolean {
    return this.isConnected;
  }

  // Simulate real-time data for demo purposes when server is not available
  startSimulation(
    onLog: (message: LogMessage) => void,
    onFlow: (message: FlowMessage) => void
  ): () => void {
    console.log('🎭 Starting simulation mode (server not available)');
    
    const operations = [
      'list_projects',
      'get_project', 
      'list_users',
      'get_user_by_email',
      'get_system_status'
    ];

    const sources = ['mcp.client', 'mcp.server', 'cway.api'];

    const logInterval = setInterval(() => {
      if (Math.random() > 0.6) {
        const source = sources[Math.floor(Math.random() * sources.length)];
        const operation = operations[Math.floor(Math.random() * operations.length)];
        const requestId = `sim-${Date.now()}`;

        onLog({
          timestamp: new Date().toISOString(),
          level: Math.random() > 0.1 ? 'info' : 'error',
          source,
          message: `${source === 'cway.api' ? '📡' : source === 'mcp.server' ? '🖥️' : '💻'} ${operation} operation`,
          requestId,
          operation
        });
      }
    }, 1500);

    const flowInterval = setInterval(() => {
      if (Math.random() > 0.7) {
        const operation = operations[Math.floor(Math.random() * operations.length)];
        const requestId = `flow-${Date.now()}`;

        // Simulate flow steps
        setTimeout(() => {
          onFlow({
            requestId,
            step: 'client_to_server',
            source: 'mcp-client',
            target: 'mcp-server', 
            operation,
            status: 'success',
            duration: Math.floor(Math.random() * 50) + 10
          });
        }, 100);

        setTimeout(() => {
          onFlow({
            requestId,
            step: 'server_to_api',
            source: 'mcp-server',
            target: 'cway-api',
            operation: `GraphQL: ${operation}`,
            status: 'pending'
          });
        }, 200);

        setTimeout(() => {
          const success = Math.random() > 0.1;
          onFlow({
            requestId,
            step: 'api_response',
            source: 'cway-api',
            target: 'response',
            operation: `Response: ${operation}`,
            status: success ? 'success' : 'error',
            duration: Math.floor(Math.random() * 400) + 100,
            details: success ? 
              { records: Math.floor(Math.random() * 20) + 1, size: `${(Math.random() * 5 + 0.5).toFixed(1)}KB` } :
              { error: 'Timeout or API error' }
          });
        }, 800);
      }
    }, 2000);

    // Return cleanup function
    return () => {
      clearInterval(logInterval);
      clearInterval(flowInterval);
    };
  }
}

export default WebSocketService;