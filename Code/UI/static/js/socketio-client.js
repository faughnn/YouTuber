/**
 * Comprehensive SocketIO Client Integration
 * 
 * Central SocketIO event handling and real-time communication layer that coordinates
 * all client-side components with the server-side SocketIO infrastructure.
 * 
 * Created: June 20, 2025
 * Agent: Implementation Agent
 * Task Reference: Phase 4, Task 4.2 - JavaScript Client Implementation
 */

class SocketIOClient {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // Event handlers registry
        this.eventHandlers = new Map();
        
        // Connection state
        this.connectionState = 'disconnected'; // disconnected, connecting, connected, reconnecting
        this.lastConnectionTime = null;
        this.connectionMetrics = {
            totalConnections: 0,
            totalDisconnections: 0,
            totalReconnects: 0,
            averageLatency: 0
        };
        
        // Component references
        this.components = {
            pipelineController: null,
            segmentManager: null,
            mainDashboard: null,
            logHandler: null
        };
        
        // Event queue for offline events
        this.eventQueue = [];
        this.maxQueueSize = 100;
        
        // Configuration
        this.config = {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: this.reconnectDelay,
            timeout: 10000,
            forceNew: false,
            upgrade: true,
            rememberUpgrade: true
        };
        
        this.initialize();
    }
    
    /**
     * Initialize SocketIO client
     */
    initialize() {
        if (typeof io === 'undefined') {
            console.error('❌ SocketIO library not loaded');
            this.handleSocketIOUnavailable();
            return;
        }
        
        this.createConnection();
        this.setupEventHandlers();
        this.setupConnectionMonitoring();
        
        console.log('🔗 SocketIO Client initialized');
    }
    
    /**
     * Create SocketIO connection
     */
    createConnection() {
        this.connectionState = 'connecting';
        
        try {
            this.socket = io(this.config);
            this.setupSocketEventHandlers();
            
        } catch (error) {
            console.error('Failed to create SocketIO connection:', error);
            this.handleConnectionError(error);
        }
    }
    
    /**
     * Setup core SocketIO event handlers
     */
    setupSocketEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            this.handleConnect();
        });
        
        this.socket.on('disconnect', (reason) => {
            this.handleDisconnect(reason);
        });
        
        this.socket.on('connect_error', (error) => {
            this.handleConnectionError(error);
        });
        
        this.socket.on('reconnect', (attemptNumber) => {
            this.handleReconnect(attemptNumber);
        });
        
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            this.handleReconnectAttempt(attemptNumber);
        });
        
        this.socket.on('reconnect_error', (error) => {
            this.handleReconnectError(error);
        });
        
        this.socket.on('reconnect_failed', () => {
            this.handleReconnectFailed();
        });
        
        // Pipeline events
        this.socket.on('pipeline_progress', (data) => {
            this.handlePipelineProgress(data);
        });
        
        this.socket.on('pipeline_update', (data) => {
            this.handlePipelineUpdate(data);
        });
        
        this.socket.on('pipeline_error', (data) => {
            this.handlePipelineError(data);
        });
        
        this.socket.on('pipeline_completion', (data) => {
            this.handlePipelineCompletion(data);
        });
        
        this.socket.on('pipeline_interrupted', (data) => {
            this.handlePipelineInterruption(data);
        });
        
        this.socket.on('pipeline_transition', (data) => {
            this.handlePipelineTransition(data);
        });
        
        // Log events
        this.socket.on('log_stream', (data) => {
            this.handleLogStream(data);
        });
        
        this.socket.on('log_message', (data) => {
            this.handleLogMessage(data);
        });
        
        // Segment events
        this.socket.on('segment_update', (data) => {
            this.handleSegmentUpdate(data);
        });
        
        this.socket.on('segment_analysis_complete', (data) => {
            this.handleSegmentAnalysisComplete(data);
        });
        
        // System events
        this.socket.on('system_status', (data) => {
            this.handleSystemStatus(data);
        });
        
        this.socket.on('episode_update', (data) => {
            this.handleEpisodeUpdate(data);
        });
        
        this.socket.on('stats_update', (data) => {
            this.handleStatsUpdate(data);
        });
        
        this.socket.on('notification', (data) => {
            this.handleNotification(data);
        });
        
        // Error handling
        this.socket.on('error', (error) => {
            this.handleSocketError(error);
        });
        
        // Custom events for component coordination
        this.socket.on('component_sync', (data) => {
            this.handleComponentSync(data);
        });
    }
    
    /**
     * Setup custom event handlers
     */
    setupEventHandlers() {
        // Register custom event handlers
        this.registerEventHandler('pipeline_progress', this.broadcastToPipelineController.bind(this));
        this.registerEventHandler('pipeline_update', this.broadcastToPipelineController.bind(this));
        this.registerEventHandler('pipeline_error', this.broadcastToPipelineController.bind(this));
        this.registerEventHandler('pipeline_completion', this.broadcastToPipelineController.bind(this));
        
        this.registerEventHandler('segment_update', this.broadcastToSegmentManager.bind(this));
        this.registerEventHandler('segment_analysis_complete', this.broadcastToSegmentManager.bind(this));
        
        this.registerEventHandler('system_status', this.broadcastToMainDashboard.bind(this));
        this.registerEventHandler('episode_update', this.broadcastToMainDashboard.bind(this));
        this.registerEventHandler('stats_update', this.broadcastToMainDashboard.bind(this));
        
        this.registerEventHandler('log_stream', this.broadcastToLogHandler.bind(this));
        this.registerEventHandler('log_message', this.broadcastToLogHandler.bind(this));
    }
    
    /**
     * Setup connection monitoring
     */
    setupConnectionMonitoring() {
        // Ping-pong for latency measurement
        setInterval(() => {
            if (this.isConnected) {
                const start = Date.now();
                this.socket.emit('ping', start, (response) => {
                    const latency = Date.now() - start;
                    this.updateLatencyMetrics(latency);
                });
            }
        }, 30000); // Every 30 seconds
        
        // Connection health check
        setInterval(() => {
            this.checkConnectionHealth();
        }, 60000); // Every minute
    }
    
    /**
     * Handle connection events
     */
    handleConnect() {
        console.log('🔗 Connected to SocketIO server');
        
        this.isConnected = true;
        this.connectionState = 'connected';
        this.lastConnectionTime = new Date();
        this.reconnectAttempts = 0;
        this.connectionMetrics.totalConnections++;
        
        // Process queued events
        this.processEventQueue();
        
        // Notify components
        this.notifyComponents('connect');
        
        // Update UI
        this.updateConnectionStatus(true);
        
        // Request current state
        this.requestCurrentState();
        
        this.showNotification('Connected to server', 'success');
    }
    
    handleDisconnect(reason) {
        console.log('❌ Disconnected from SocketIO server:', reason);
        
        this.isConnected = false;
        this.connectionState = 'disconnected';
        this.connectionMetrics.totalDisconnections++;
        
        // Notify components
        this.notifyComponents('disconnect', { reason });
        
        // Update UI
        this.updateConnectionStatus(false);
        
        // Show appropriate notification
        if (reason === 'io server disconnect') {
            this.showNotification('Server disconnected', 'warning');
        } else if (reason === 'transport close' || reason === 'transport error') {
            this.showNotification('Connection lost - attempting to reconnect', 'warning');
        }
    }
    
    handleConnectionError(error) {
        console.error('❌ SocketIO connection error:', error);
        
        this.connectionState = 'error';
        
        // Notify components
        this.notifyComponents('connection_error', { error });
        
        this.showNotification('Connection error - retrying', 'error');
    }
    
    handleReconnect(attemptNumber) {
        console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
        
        this.connectionMetrics.totalReconnects++;
        this.connectionState = 'connected';
        
        this.showNotification('Reconnected to server', 'success');
    }
    
    handleReconnectAttempt(attemptNumber) {
        console.log(`🔄 Attempting to reconnect (${attemptNumber}/${this.maxReconnectAttempts})`);
        
        this.connectionState = 'reconnecting';
        this.reconnectAttempts = attemptNumber;
        
        // Update UI with attempt number
        this.updateReconnectStatus(attemptNumber);
    }
    
    handleReconnectError(error) {
        console.error('❌ Reconnection error:', error);
    }
    
    handleReconnectFailed() {
        console.error('❌ Failed to reconnect after maximum attempts');
        
        this.connectionState = 'failed';
        
        this.showNotification('Failed to reconnect - please refresh the page', 'error');
        
        // Show reconnection UI
        this.showReconnectionInterface();
    }
    
    /**
     * Handle pipeline events
     */
    handlePipelineProgress(data) {
        console.log('📊 Pipeline progress:', data);
        
        // Validate data
        if (!this.validatePipelineData(data)) {
            console.warn('Invalid pipeline progress data:', data);
            return;
        }
        
        // Emit to registered handlers
        this.emitToHandlers('pipeline_progress', data);
        
        // Update global state
        this.updateGlobalPipelineState(data);
    }
    
    handlePipelineUpdate(data) {
        console.log('📝 Pipeline update:', data);
        this.emitToHandlers('pipeline_update', data);
    }
    
    handlePipelineError(data) {
        console.error('❌ Pipeline error:', data);
        this.emitToHandlers('pipeline_error', data);
        
        // Show error notification
        this.showNotification(data.error || 'Pipeline error occurred', 'error');
    }
    
    handlePipelineCompletion(data) {
        console.log('✅ Pipeline completed:', data);
        this.emitToHandlers('pipeline_completion', data);
        
        // Show completion notification
        this.showNotification('Pipeline completed successfully!', 'success');
        
        // Trigger stats refresh
        this.requestStatsUpdate();
    }
    
    handlePipelineInterruption(data) {
        console.log('⏸️ Pipeline interrupted:', data);
        this.emitToHandlers('pipeline_interrupted', data);
        
        this.showNotification('Pipeline was interrupted', 'warning');
    }
    
    handlePipelineTransition(data) {
        console.log('🔄 Pipeline stage transition:', data);
        this.emitToHandlers('pipeline_transition', data);
    }
    
    /**
     * Handle log events
     */
    handleLogStream(data) {
        // High frequency event - minimal logging
        this.emitToHandlers('log_stream', data);
    }
    
    handleLogMessage(data) {
        this.emitToHandlers('log_message', data);
        
        // Show critical log messages as notifications
        if (data.level === 'ERROR' || data.level === 'CRITICAL') {
            this.showNotification(`${data.level}: ${data.message}`, 'error');
        }
    }
    
    /**
     * Handle segment events
     */
    handleSegmentUpdate(data) {
        console.log('🎬 Segment update:', data);
        this.emitToHandlers('segment_update', data);
    }
    
    handleSegmentAnalysisComplete(data) {
        console.log('🎯 Segment analysis complete:', data);
        this.emitToHandlers('segment_analysis_complete', data);
        
        this.showNotification(`Analysis complete: ${data.segments?.length || 0} segments found`, 'success');
    }
    
    /**
     * Handle system events
     */
    handleSystemStatus(data) {
        console.log('⚙️ System status update:', data);
        this.emitToHandlers('system_status', data);
    }
    
    handleEpisodeUpdate(data) {
        console.log('📺 Episode update:', data);
        this.emitToHandlers('episode_update', data);
    }
    
    handleStatsUpdate(data) {
        console.log('📈 Stats update:', data);
        this.emitToHandlers('stats_update', data);
    }
    
    handleNotification(data) {
        this.showNotification(data.message, data.type || 'info');
    }
    
    handleSocketError(error) {
        console.error('❌ Socket error:', error);
        this.showNotification('Socket error occurred', 'error');
    }
    
    handleComponentSync(data) {
        console.log('🔄 Component sync:', data);
        this.emitToHandlers('component_sync', data);
    }
    
    /**
     * Component registration and management
     */
    registerComponent(name, component) {
        this.components[name] = component;
        console.log(`🔗 Registered component: ${name}`);
        
        // If we're already connected, notify the component
        if (this.isConnected) {
            if (typeof component.handleSocketConnect === 'function') {
                component.handleSocketConnect(this.socket);
            }
        }
    }
    
    unregisterComponent(name) {
        delete this.components[name];
        console.log(`🔗 Unregistered component: ${name}`);
    }
    
    notifyComponents(eventType, data = {}) {
        Object.entries(this.components).forEach(([name, component]) => {
            if (component && typeof component[`handleSocket${eventType.charAt(0).toUpperCase() + eventType.slice(1)}`] === 'function') {
                try {
                    component[`handleSocket${eventType.charAt(0).toUpperCase() + eventType.slice(1)}`](data);
                } catch (error) {
                    console.error(`Error notifying component ${name}:`, error);
                }
            }
        });
    }
    
    /**
     * Event handler management
     */
    registerEventHandler(eventName, handler) {
        if (!this.eventHandlers.has(eventName)) {
            this.eventHandlers.set(eventName, []);
        }
        this.eventHandlers.get(eventName).push(handler);
    }
    
    unregisterEventHandler(eventName, handler) {
        if (this.eventHandlers.has(eventName)) {
            const handlers = this.eventHandlers.get(eventName);
            const index = handlers.indexOf(handler);
            if (index !== -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    emitToHandlers(eventName, data) {
        if (this.eventHandlers.has(eventName)) {
            this.eventHandlers.get(eventName).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventName}:`, error);
                }
            });
        }
    }
    
    /**
     * Component broadcast methods
     */
    broadcastToPipelineController(data) {
        if (this.components.pipelineController) {
            const methodName = `handle${data.type || 'PipelineProgress'}`;
            if (typeof this.components.pipelineController[methodName] === 'function') {
                this.components.pipelineController[methodName](data);
            }
        }
    }
    
    broadcastToSegmentManager(data) {
        if (this.components.segmentManager) {
            const eventType = data.type || 'SegmentUpdate';
            const methodName = `handle${eventType}`;
            if (typeof this.components.segmentManager[methodName] === 'function') {
                this.components.segmentManager[methodName](data);
            }
        }
    }
    
    broadcastToMainDashboard(data) {
        if (this.components.mainDashboard) {
            const eventType = data.type || 'SystemStatus';
            const methodName = `handle${eventType}`;
            if (typeof this.components.mainDashboard[methodName] === 'function') {
                this.components.mainDashboard[methodName](data);
            }
        }
    }
    
    broadcastToLogHandler(data) {
        if (this.components.logHandler) {
            if (typeof this.components.logHandler.addLogEntry === 'function') {
                this.components.logHandler.addLogEntry(data);
            }
        }
    }
    
    /**
     * State management
     */
    updateGlobalPipelineState(data) {
        if (window.YouTubePipelineUI) {
            window.YouTubePipelineUI.currentExecution = data.session_id;
            window.YouTubePipelineUI.currentStage = data.stage;
            window.YouTubePipelineUI.pipelineStatus = data.status;
        }
    }
    
    requestCurrentState() {
        if (this.isConnected) {
            this.socket.emit('request_current_state');
        }
    }
    
    requestStatsUpdate() {
        if (this.isConnected) {
            this.socket.emit('request_stats_update');
        }
    }
    
    /**
     * Connection health and monitoring
     */
    checkConnectionHealth() {
        if (!this.isConnected) {
            console.warn('⚠️ Connection health check: Not connected');
            return;
        }
        
        // Check if socket is actually responsive
        const start = Date.now();
        this.socket.emit('health_check', start, (response) => {
            const latency = Date.now() - start;
            if (latency > 5000) { // 5 second threshold
                console.warn('⚠️ High latency detected:', latency + 'ms');
                this.showNotification('Connection is slow', 'warning');
            }
        });
    }
    
    updateLatencyMetrics(latency) {
        // Simple moving average
        if (this.connectionMetrics.averageLatency === 0) {
            this.connectionMetrics.averageLatency = latency;
        } else {
            this.connectionMetrics.averageLatency = (this.connectionMetrics.averageLatency + latency) / 2;
        }
    }
    
    /**
     * UI updates
     */
    updateConnectionStatus(connected) {
        // Update connection indicators
        const indicators = document.querySelectorAll('.connection-status');
        indicators.forEach(indicator => {
            if (connected) {
                indicator.classList.remove('text-red-500', 'bg-red-100');
                indicator.classList.add('text-green-500', 'bg-green-100');
                indicator.textContent = 'Connected';
                indicator.title = `Connected (${Math.round(this.connectionMetrics.averageLatency)}ms)`;
            } else {
                indicator.classList.remove('text-green-500', 'bg-green-100');
                indicator.classList.add('text-red-500', 'bg-red-100');
                indicator.textContent = 'Disconnected';
                indicator.title = 'Disconnected from server';
            }
        });
        
        // Update global state
        if (window.YouTubePipelineUI) {
            window.YouTubePipelineUI.connectionStatus = connected ? 'connected' : 'disconnected';
        }
    }
    
    updateReconnectStatus(attemptNumber) {
        const indicators = document.querySelectorAll('.connection-status');
        indicators.forEach(indicator => {
            indicator.classList.remove('text-green-500', 'bg-green-100', 'text-red-500', 'bg-red-100');
            indicator.classList.add('text-yellow-500', 'bg-yellow-100');
            indicator.textContent = `Reconnecting (${attemptNumber}/${this.maxReconnectAttempts})`;
        });
    }
    
    showReconnectionInterface() {
        // Create reconnection modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md mx-4">
                <div class="text-center">
                    <div class="text-red-500 text-6xl mb-4">⚠️</div>
                    <h2 class="text-xl font-semibold text-gray-900 mb-2">Connection Lost</h2>
                    <p class="text-gray-600 mb-6">
                        Unable to connect to the server. Please check your internet connection and try again.
                    </p>
                    <div class="space-x-3">
                        <button onclick="window.location.reload()" 
                                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                            Refresh Page
                        </button>
                        <button onclick="this.closest('.fixed').remove()" 
                                class="px-4 py-2 text-gray-600 hover:text-gray-800">
                            Dismiss
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    /**
     * Event queue management
     */
    queueEvent(eventName, data) {
        if (this.eventQueue.length >= this.maxQueueSize) {
            this.eventQueue.shift(); // Remove oldest event
        }
        
        this.eventQueue.push({
            eventName,
            data,
            timestamp: Date.now()
        });
    }
    
    processEventQueue() {
        while (this.eventQueue.length > 0) {
            const event = this.eventQueue.shift();
            
            // Only process events that are less than 5 minutes old
            if (Date.now() - event.timestamp < 300000) {
                this.socket.emit(event.eventName, event.data);
            }
        }
    }
    
    /**
     * Validation methods
     */
    validatePipelineData(data) {
        return data && 
               typeof data.session_id === 'string' &&
               typeof data.stage === 'number' &&
               typeof data.progress === 'number' &&
               data.progress >= 0 && data.progress <= 100;
    }
    
    /**
     * SocketIO unavailable fallback
     */
    handleSocketIOUnavailable() {
        console.warn('⚠️ SocketIO not available - using fallback mode');
        
        // Create mock socket object
        this.socket = {
            connected: false,
            emit: () => {},
            on: () => {},
            off: () => {},
            connect: () => {
                this.showNotification('SocketIO not available - real-time features disabled', 'warning');
            }
        };
        
        // Show notification
        this.showNotification('Real-time features unavailable - using polling mode', 'warning');
        
        // Setup polling fallback
        this.setupPollingFallback();
    }
    
    setupPollingFallback() {
        // Poll for updates every 5 seconds
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                if (data.success) {
                    this.emitToHandlers('system_status', data);
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 5000);
    }
    
    /**
     * Notification system
     */
    showNotification(message, type = 'info') {
        // Use main dashboard notification system if available
        if (window.YouTubePipelineUI && window.YouTubePipelineUI.mainDashboard) {
            window.YouTubePipelineUI.mainDashboard.showNotification(message, type);
        } else if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    /**
     * Public API methods
     */
    emit(eventName, data, callback) {
        if (this.isConnected) {
            this.socket.emit(eventName, data, callback);
        } else {
            this.queueEvent(eventName, data);
            console.warn(`Event ${eventName} queued - not connected`);
        }
    }
    
    on(eventName, handler) {
        this.registerEventHandler(eventName, handler);
    }
    
    off(eventName, handler) {
        this.unregisterEventHandler(eventName, handler);
    }
    
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            state: this.connectionState,
            lastConnection: this.lastConnectionTime,
            metrics: this.connectionMetrics
        };
    }
    
    forceReconnect() {
        if (this.socket) {
            this.socket.disconnect();
            setTimeout(() => {
                this.socket.connect();
            }, 1000);
        }
    }
    
    getSocket() {
        return this.socket;
    }
}

// Initialize SocketIO client when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.YouTubePipelineUI = window.YouTubePipelineUI || {};
    window.YouTubePipelineUI.socketClient = new SocketIOClient();
    
    // Make socket available globally for backward compatibility
    setTimeout(() => {
        if (window.YouTubePipelineUI.socketClient.socket) {
            window.YouTubePipelineUI.socket = window.YouTubePipelineUI.socketClient.socket;
        }
    }, 100);
    
    console.log('🔗 SocketIO Client ready');
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SocketIOClient;
}
