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
  private disconnectCallbacks: Array<() => void> = [];

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
        this.disconnectCallbacks.forEach(callback => callback());
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

  onDisconnect(callback: () => void): void {
    this.disconnectCallbacks.push(callback);
  }

  removeDisconnectCallback(callback: () => void): void {
    this.disconnectCallbacks = this.disconnectCallbacks.filter(cb => cb !== callback);
  }
}

export default WebSocketService;