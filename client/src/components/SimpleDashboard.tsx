import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowRight, 
  Server, 
  Globe, 
  Monitor, 
  Activity, 
  Clock,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
  Wifi,
  WifiOff
} from 'lucide-react';
import WebSocketService from '../services/websocketService';

interface FlowStep {
  id: string;
  timestamp: Date;
  source: 'mcp-client' | 'mcp-server' | 'cway-api';
  target: 'mcp-server' | 'cway-api' | 'response';
  operation: string;
  status: 'pending' | 'success' | 'error';
  duration?: number;
  details?: any;
}

interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'info' | 'warn' | 'error';
  source: string;
  message: string;
  requestId?: string;
}

const SimpleDashboard: React.FC = () => {
  const [flowSteps, setFlowSteps] = useState<FlowStep[]>([]);
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [activeFlow, setActiveFlow] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [wsService] = useState(() => new WebSocketService('ws://localhost:8080'));

  const addLogEntry = useCallback((level: 'info' | 'warn' | 'error', source: string, message: string, requestId?: string) => {
    const entry: LogEntry = {
      id: `log-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      level,
      source,
      message,
      requestId
    };
    
    setLogEntries(prev => [...prev.slice(-99), entry]);
  }, []);

  const addFlowStep = useCallback((flowData: any) => {
    const step: FlowStep = {
      id: flowData.id || `${flowData.requestId}-${Date.now()}`,
      timestamp: new Date(flowData.timestamp || Date.now()),
      source: flowData.source,
      target: flowData.target,
      operation: flowData.operation,
      status: flowData.status,
      duration: flowData.duration,
      details: flowData.details
    };
    
    setFlowSteps(prev => [...prev.slice(-19), step]);
    
    if (flowData.requestId) {
      setActiveFlow(flowData.requestId);
      setTimeout(() => setActiveFlow(null), 2000);
    }
  }, []);

  // Connect to WebSocket for real-time data
  useEffect(() => {
    let mounted = true;
    
    const connectToServer = async () => {
      if (!mounted) return;
      
      setConnectionStatus('connecting');
      addLogEntry('info', 'dashboard', '🔌 Attempting to connect to MCP server...');
      
      try {
        const connected = await wsService.connect();
        
        if (!mounted) return;
        
        if (connected) {
          setIsConnected(true);
          setConnectionStatus('connected');
          addLogEntry('info', 'dashboard', '✅ Connected to MCP server WebSocket');
          
          // Set up event listeners
          wsService.onLogMessage((logData) => {
            if (mounted) {
              addLogEntry(logData.level, logData.source, logData.message, logData.requestId);
            }
          });
          
          wsService.onFlowMessage((flowData) => {
            if (mounted) {
              addFlowStep(flowData);
            }
          });
          
          // Request historical data
          wsService.requestHistoricalData();
          
          // Listen for disconnection
          wsService.onDisconnect(() => {
            if (mounted) {
              setIsConnected(false);
              setConnectionStatus('disconnected');
              addLogEntry('warn', 'dashboard', '⚠️ Disconnected from MCP server');
            }
          });
          
        } else {
          setIsConnected(false);
          setConnectionStatus('disconnected');
          addLogEntry('warn', 'dashboard', '⚠️ Could not connect to MCP server - please start the server');
        }
      } catch (error) {
        if (mounted) {
          setIsConnected(false);
          setConnectionStatus('disconnected');
          addLogEntry('error', 'dashboard', `❌ Connection failed: ${error}`);
        }
      }
    };
    
    connectToServer();
    
    // Try to reconnect every 10 seconds if not connected
    const reconnectInterval = setInterval(() => {
      if (mounted && !isConnected) {
        connectToServer();
      }
    }, 10000);
    
    return () => {
      mounted = false;
      clearInterval(reconnectInterval);
      wsService.disconnect();
    };
  }, [wsService, isConnected, addLogEntry, addFlowStep]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle style={{width: 16, height: 16, color: '#10b981'}} />;
      case 'error': return <XCircle style={{width: 16, height: 16, color: '#ef4444'}} />;
      case 'pending': return <AlertCircle style={{width: 16, height: 16, color: '#f59e0b'}} className="animate-pulse" />;
      default: return null;
    }
  };

  const getSourceIcon = (source: string) => {
    const iconStyle = {width: 24, height: 24};
    switch (source) {
      case 'mcp-client': return <Monitor style={{...iconStyle, color: '#3b82f6'}} />;
      case 'mcp-server': return <Server style={{...iconStyle, color: '#10b981'}} />;
      case 'cway-api': return <Globe style={{...iconStyle, color: '#8b5cf6'}} />;
      default: return <Server style={{...iconStyle, color: '#6b7280'}} />;
    }
  };

  const clearLogs = () => {
    setFlowSteps([]);
    setLogEntries([]);
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4" style={{color: '#111827'}}>
            🔄 Cway MCP Server Flow Dashboard
          </h1>
          <p style={{color: '#6b7280'}}>
            Real-time visualization of data flow from MCP Client → MCP Server → Cway API
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 mb-8">
          <motion.div 
            className="stat-card"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center">
              <Activity style={{width: 32, height: 32, color: '#3b82f6'}} />
              <div className="ml-4">
                <p className="text-sm font-medium" style={{color: '#6b7280'}}>Active Flows</p>
                <p className="text-2xl font-bold" style={{color: '#111827'}}>
                  {flowSteps.filter(s => s.status === 'pending').length}
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="stat-card"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center">
              <CheckCircle style={{width: 32, height: 32, color: '#10b981'}} />
              <div className="ml-4">
                <p className="text-sm font-medium" style={{color: '#6b7280'}}>Success Rate</p>
                <p className="text-2xl font-bold" style={{color: '#111827'}}>
                  {Math.round((flowSteps.filter(s => s.status === 'success').length / Math.max(flowSteps.length, 1)) * 100)}%
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="stat-card"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center">
              <Clock style={{width: 32, height: 32, color: '#f59e0b'}} />
              <div className="ml-4">
                <p className="text-sm font-medium" style={{color: '#6b7280'}}>Avg Response</p>
                <p className="text-2xl font-bold" style={{color: '#111827'}}>
                  {Math.round(flowSteps.filter(s => s.duration).reduce((acc, s) => acc + (s.duration || 0), 0) / Math.max(flowSteps.filter(s => s.duration).length, 1) || 0)}ms
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="stat-card"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center">
              <Zap style={{width: 32, height: 32, color: '#8b5cf6'}} />
              <div className="ml-4">
                <p className="text-sm font-medium" style={{color: '#6b7280'}}>Total Requests</p>
                <p className="text-2xl font-bold" style={{color: '#111827'}}>{flowSteps.length}</p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Main Flow Visualization */}
        <div className="grid grid-cols-2">
          
          {/* Flow Diagram */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-6 flex items-center">
              <ArrowRight style={{width: 20, height: 20, color: '#f59e0b'}} className="ml-2" />
              Data Flow Visualization
            </h2>
            
            <div>
              {/* Flow Architecture */}
              <div className="flow-architecture">
                <div className="flow-node client">
                  <Monitor style={{width: 48, height: 48}} />
                  <span className="text-sm font-medium">MCP Client</span>
                  <span className="text-sm" style={{color: '#6b7280'}}>Claude, etc.</span>
                </div>
                
                <motion.div
                  className="flow-arrow"
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                  <ArrowRight style={{width: 32, height: 32}} />
                </motion.div>
                
                <div className="flow-node server">
                  <Server style={{width: 48, height: 48}} />
                  <span className="text-sm font-medium">MCP Server</span>
                  <span className="text-sm" style={{color: '#6b7280'}}>Proxy/Adapter</span>
                </div>
                
                <motion.div
                  className="flow-arrow"
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                >
                  <ArrowRight style={{width: 32, height: 32}} />
                </motion.div>
                
                <div className="flow-node api">
                  <Globe style={{width: 48, height: 48}} />
                  <span className="text-sm font-medium">Cway API</span>
                  <span className="text-sm" style={{color: '#6b7280'}}>GraphQL</span>
                </div>
              </div>

              {/* Recent Flow Steps */}
              <div style={{maxHeight: 400, overflowY: 'auto'}}>
                <h3 className="text-lg font-medium mb-4">Recent Flow Steps</h3>
                <AnimatePresence>
                  {flowSteps.slice(-10).reverse().map((step) => (
                    <motion.div
                      key={step.id}
                      initial={{ opacity: 0, y: -20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 20 }}
                      className={`flow-step ${step.id.includes(activeFlow || '') ? 'active' : ''}`}
                    >
                      <div className="flex items-center" style={{gap: 12}}>
                        {getSourceIcon(step.source)}
                        <ArrowRight style={{width: 16, height: 16, color: '#6b7280'}} />
                        {getSourceIcon(step.target)}
                      </div>
                      <div className="ml-4" style={{flex: 1}}>
                        <p className="text-sm font-medium" style={{color: '#111827'}}>{step.operation}</p>
                        <p className="text-sm" style={{color: '#6b7280'}}>
                          {step.timestamp.toLocaleTimeString()}
                          {step.duration && ` • ${step.duration}ms`}
                        </p>
                      </div>
                      <div className="flex items-center" style={{gap: 8}}>
                        {getStatusIcon(step.status)}
                        {step.details && step.status === 'success' && (
                          <span className="text-sm" style={{color: '#10b981'}}>
                            {step.details.records} records
                          </span>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </div>

          {/* Live Logs */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-6 flex items-center">
              <Activity style={{width: 20, height: 20, color: '#10b981'}} className="ml-2" />
              Live Logs
            </h2>
            
            <div className="log-container">
              <AnimatePresence>
                {logEntries.slice(-20).reverse().map((entry) => (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className={`log-entry log-${entry.level}`}
                  >
                    <span style={{color: '#6b7280'}}>
                      [{entry.timestamp.toLocaleTimeString()}]
                    </span>{' '}
                    <span style={{color: '#3b82f6'}}>{entry.source}</span>:{' '}
                    {entry.message}
                    {entry.requestId && (
                      <span style={{color: '#6b7280', fontSize: 12}} className="ml-2">
                        ({entry.requestId})
                      </span>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Connection Status & Controls */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Server Connection</h2>
            <div className="flex items-center" style={{gap: 8}}>
              {connectionStatus === 'connected' && <Wifi style={{width: 20, height: 20, color: '#10b981'}} />}
              {connectionStatus === 'connecting' && <Wifi style={{width: 20, height: 20, color: '#f59e0b'}} className="animate-pulse" />}
              {connectionStatus === 'disconnected' && <WifiOff style={{width: 20, height: 20, color: '#ef4444'}} />}
              <span style={{color: connectionStatus === 'connected' ? '#10b981' : connectionStatus === 'connecting' ? '#f59e0b' : '#ef4444'}}>
                {connectionStatus === 'connected' ? 'Connected to MCP Server' :
                 connectionStatus === 'connecting' ? 'Connecting...' :
                 'Disconnected - Start MCP server to see real data'}
              </span>
            </div>
          </div>
          
          <div className="flex space-x-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={clearLogs}
              className="btn btn-secondary"
            >
              Clear Logs
            </motion.button>
            
            {!isConnected && (
              <div className="p-4" style={{backgroundColor: '#fef3c7', borderRadius: '6px', border: '1px solid #f59e0b'}}>
                <p className="text-sm" style={{color: '#92400e'}}>
                  💡 <strong>To see real data:</strong> Start the MCP server with <code>python -m src.presentation.cway_mcp_server</code>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleDashboard;