import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowRight, 
  Server, 
  Globe, 
  Monitor, 
  Activity, 
  Clock,
  Database,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

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

const FlowDashboard: React.FC = () => {
  const [flowSteps, setFlowSteps] = useState<FlowStep[]>([]);
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [activeFlow, setActiveFlow] = useState<string | null>(null);

  const simulateFlow = () => {
    const operations = [
      'list_projects', 
      'get_project', 
      'list_users', 
      'get_user_by_email',
      'get_system_status'
    ];
    
    const operation = operations[Math.floor(Math.random() * operations.length)];
    const requestId = `req-${Date.now()}`;
    
    setActiveFlow(requestId);

    // Step 1: MCP Client -> MCP Server
    const step1: FlowStep = {
      id: `${requestId}-1`,
      timestamp: new Date(),
      source: 'mcp-client',
      target: 'mcp-server',
      operation: operation,
      status: 'pending'
    };

    setFlowSteps(prev => [...prev.slice(-9), step1]);
    
    // Add log entry
    addLogEntry('info', 'mcp.client', `📤 Calling ${operation}`, requestId);

    setTimeout(() => {
      // Step 2: MCP Server -> Cway API
      const step2: FlowStep = {
        id: `${requestId}-2`,
        timestamp: new Date(),
        source: 'mcp-server',
        target: 'cway-api',
        operation: `GraphQL: ${operation}`,
        status: 'pending'
      };

      setFlowSteps(prev => [...prev.slice(-9), step2]);
      addLogEntry('info', 'mcp.server', `🔄 Forwarding to Cway API: ${operation}`, requestId);

      // Update step1 to success
      setFlowSteps(prev => prev.map(step => 
        step.id === step1.id ? { ...step, status: 'success' as const, duration: 100 } : step
      ));

      setTimeout(() => {
        // Step 3: Cway API Response
        const success = Math.random() > 0.1; // 90% success rate
        const step3: FlowStep = {
          id: `${requestId}-3`,
          timestamp: new Date(),
          source: 'cway-api',
          target: 'response',
          operation: `Response: ${operation}`,
          status: success ? 'success' : 'error',
          duration: Math.floor(Math.random() * 500) + 100,
          details: success ? 
            { records: Math.floor(Math.random() * 50) + 1, size: `${(Math.random() * 10 + 1).toFixed(1)}KB` } :
            { error: 'API timeout' }
        };

        setFlowSteps(prev => [...prev.slice(-9), step3]);
        
        // Update step2 status
        setFlowSteps(prev => prev.map(step => 
          step.id === step2.id ? { ...step, status: success ? 'success' as const : 'error' as const, duration: step3.duration } : step
        ));

        addLogEntry(
          success ? 'info' : 'error', 
          'cway.api', 
          success ? 
            `✅ Success: ${operation} (${step3.details.records} records, ${step3.details.size})` :
            `❌ Error: ${operation} - ${step3.details.error}`,
          requestId
        );

        setTimeout(() => {
          setActiveFlow(null);
        }, 1000);

      }, Math.floor(Math.random() * 800) + 200);
    }, Math.floor(Math.random() * 300) + 100);
  };

  // Simulate real-time data flow
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate a new request flow
      if (Math.random() > 0.7) { // 30% chance each second
        simulateFlow();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);


  const addLogEntry = (level: 'info' | 'warn' | 'error', source: string, message: string, requestId?: string) => {
    const entry: LogEntry = {
      id: `log-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      level,
      source,
      message,
      requestId
    };
    
    setLogEntries(prev => [...prev.slice(-99), entry]);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending': return <AlertCircle className="w-4 h-4 text-yellow-500 animate-pulse" />;
      default: return null;
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'mcp-client': return <Monitor className="w-6 h-6 text-mcp-blue" />;
      case 'mcp-server': return <Server className="w-6 h-6 text-mcp-green" />;
      case 'cway-api': return <Globe className="w-6 h-6 text-cway-purple" />;
      default: return <Database className="w-6 h-6 text-gray-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🔄 Cway MCP Server Flow Dashboard
          </h1>
          <p className="text-gray-600">
            Real-time visualization of data flow from MCP Client → MCP Server → Cway API
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div 
            className="bg-white rounded-lg shadow p-6"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-mcp-blue" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Flows</p>
                <p className="text-2xl font-bold text-gray-900">
                  {flowSteps.filter(s => s.status === 'pending').length}
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-white rounded-lg shadow p-6"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round((flowSteps.filter(s => s.status === 'success').length / Math.max(flowSteps.length, 1)) * 100)}%
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-white rounded-lg shadow p-6"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-flow-orange" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Response</p>
                <p className="text-2xl font-bold text-gray-900">
                  {flowSteps.filter(s => s.duration).reduce((acc, s) => acc + (s.duration || 0), 0) / Math.max(flowSteps.filter(s => s.duration).length, 1) || 0}ms
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            className="bg-white rounded-lg shadow p-6"
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center">
              <Zap className="h-8 w-8 text-cway-purple" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Requests</p>
                <p className="text-2xl font-bold text-gray-900">{flowSteps.length}</p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Main Flow Visualization */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Flow Diagram */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center">
              <ArrowRight className="w-5 h-5 mr-2 text-flow-orange" />
              Data Flow Visualization
            </h2>
            
            <div className="space-y-6">
              {/* Flow Architecture */}
              <div className="flex items-center justify-between">
                <div className="flex flex-col items-center p-4 bg-mcp-blue/10 rounded-lg">
                  <Monitor className="w-12 h-12 text-mcp-blue mb-2" />
                  <span className="text-sm font-medium text-mcp-blue">MCP Client</span>
                  <span className="text-xs text-gray-500">Claude, etc.</span>
                </div>
                
                <motion.div
                  className="flex-1 mx-4"
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                  <ArrowRight className="w-8 h-8 text-flow-orange mx-auto" />
                </motion.div>
                
                <div className="flex flex-col items-center p-4 bg-mcp-green/10 rounded-lg">
                  <Server className="w-12 h-12 text-mcp-green mb-2" />
                  <span className="text-sm font-medium text-mcp-green">MCP Server</span>
                  <span className="text-xs text-gray-500">Proxy/Adapter</span>
                </div>
                
                <motion.div
                  className="flex-1 mx-4"
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                >
                  <ArrowRight className="w-8 h-8 text-flow-orange mx-auto" />
                </motion.div>
                
                <div className="flex flex-col items-center p-4 bg-cway-purple/10 rounded-lg">
                  <Globe className="w-12 h-12 text-cway-purple mb-2" />
                  <span className="text-sm font-medium text-cway-purple">Cway API</span>
                  <span className="text-xs text-gray-500">GraphQL</span>
                </div>
              </div>

              {/* Recent Flow Steps */}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                <h3 className="text-lg font-medium mb-4">Recent Flow Steps</h3>
                <AnimatePresence>
                  {flowSteps.slice(-10).reverse().map((step, index) => (
                    <motion.div
                      key={step.id}
                      initial={{ opacity: 0, y: -20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 20 }}
                      className={`flex items-center p-3 rounded-lg border ${
                        step.id.includes(activeFlow || '') ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        {getSourceIcon(step.source)}
                        <ArrowRight className="w-4 h-4 text-gray-400" />
                        {getSourceIcon(step.target)}
                      </div>
                      <div className="ml-4 flex-1">
                        <p className="text-sm font-medium text-gray-900">{step.operation}</p>
                        <p className="text-xs text-gray-500">
                          {step.timestamp.toLocaleTimeString()}
                          {step.duration && ` • ${step.duration}ms`}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(step.status)}
                        {step.details && step.status === 'success' && (
                          <span className="text-xs text-green-600">
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
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-green-600" />
              Live Logs
            </h2>
            
            <div className="bg-black rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
              <AnimatePresence>
                {logEntries.slice(-20).reverse().map((entry) => (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className={`mb-2 ${
                      entry.level === 'error' ? 'text-red-400' :
                      entry.level === 'warn' ? 'text-yellow-400' :
                      'text-green-400'
                    }`}
                  >
                    <span className="text-gray-500">
                      [{entry.timestamp.toLocaleTimeString()}]
                    </span>{' '}
                    <span className="text-blue-400">{entry.source}</span>:{' '}
                    {entry.message}
                    {entry.requestId && (
                      <span className="text-gray-400 text-xs ml-2">
                        ({entry.requestId})
                      </span>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Controls</h2>
          <div className="flex space-x-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={simulateFlow}
              className="px-4 py-2 bg-mcp-blue text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Simulate Request
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setFlowSteps([]);
                setLogEntries([]);
              }}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Clear Logs
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowDashboard;