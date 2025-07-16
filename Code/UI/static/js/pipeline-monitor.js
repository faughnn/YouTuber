/**
 * Pipeline Real-time Monitoring - SocketIO Integration
 * 
 * This file provides comprehensive real-time monitoring capabilities for the YouTube Pipeline UI,
 * including stage progress tracking, sub-stage updates, log streaming, error notifications,
 * and connection management with auto-reconnection.
 * 
 * Created: June 20, 2025
 * Agent: Agent_Realtime_System
 * Task Reference: Phase 4, Task 4.1 - SocketIO Integration
 */

class PipelineMonitor {
    constructor() {
        this.socket = null;
        this.currentSession = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.logBuffer = [];
        this.maxLogBufferSize = 1000;
        
        // UI element references
        this.progressContainer = null;
        this.logContainer = null;
        this.statusIndicator = null;
        this.notificationArea = null;
        
        // Progress tracking
        this.stageProgress = {};
        this.currentStage = null;
        this.currentSubStage = null;
        
        this.initializeUI();
        this.initializeSocketIO();
    }
    
    /**
     * Initialize UI elements and event listeners
     */
    initializeUI() {
        // Create or find main progress container
        this.progressContainer = document.getElementById('pipeline-progress') || this.createProgressContainer();
        
        // Create or find log container
        this.logContainer = document.getElementById('pipeline-logs') || this.createLogContainer();
        
        // Create or find status indicator
        this.statusIndicator = document.getElementById('connection-status') || this.createStatusIndicator();
        
        // Create or find notification area
        this.notificationArea = document.getElementById('notifications') || this.createNotificationArea();
        
        // Add log filtering controls
        this.createLogControls();
        
        console.log('🖥️ Pipeline Monitor UI initialized');
    }
    
    /**
     * Create progress container if it doesn't exist
     */
    createProgressContainer() {
        const container = document.createElement('div');
        container.id = 'pipeline-progress';
        container.className = 'pipeline-progress-container bg-white rounded-lg shadow-md p-6 mb-6';
        container.innerHTML = `
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Pipeline Progress</h3>
            <div id="stage-progress-bars" class="space-y-4"></div>
            <div id="current-stage-detail" class="mt-4 p-4 bg-gray-50 rounded-md hidden">
                <h4 class="font-medium text-gray-900" id="current-stage-name"></h4>
                <p class="text-sm text-gray-600" id="current-stage-description"></p>
                <div class="mt-2">
                    <div class="flex justify-between text-sm text-gray-700">
                        <span id="current-sub-stage">Initializing...</span>
                        <span id="current-progress-percent">0%</span>
                    </div>
                    <div class="mt-1 bg-gray-200 rounded-full h-2">
                        <div id="current-progress-bar" class="bg-blue-600 h-2 rounded-full transition-all duration-500" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert after the main content or at the top of main
        const main = document.querySelector('main') || document.body;
        main.insertBefore(container, main.firstChild);
        
        return container;
    }
    
    /**
     * Create log container if it doesn't exist
     */
    createLogContainer() {
        const container = document.createElement('div');
        container.id = 'pipeline-logs';
        container.className = 'pipeline-logs-container bg-white rounded-lg shadow-md p-6 mb-6';
        container.innerHTML = `
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-gray-900">Pipeline Logs</h3>
                <div id="log-controls" class="flex space-x-2">
                    <select id="log-level-filter" class="text-sm border border-gray-300 rounded px-2 py-1">
                        <option value="all">All Levels</option>
                        <option value="INFO">Info</option>
                        <option value="WARNING">Warning</option>
                        <option value="ERROR">Error</option>
                    </select>
                    <button id="clear-logs" class="text-sm bg-gray-500 text-white px-3 py-1 rounded hover:bg-gray-600">Clear</button>
                    <button id="download-logs" class="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">Download</button>
                </div>
            </div>
            <div id="log-output" class="log-output bg-gray-900 text-green-400 font-mono text-sm p-4 rounded-md h-64 overflow-y-auto">
                <div class="text-gray-500">Waiting for logs...</div>
            </div>
        `;
        
        // Insert after progress container
        const progressContainer = document.getElementById('pipeline-progress');
        if (progressContainer) {
            progressContainer.parentNode.insertBefore(container, progressContainer.nextSibling);
        } else {
            const main = document.querySelector('main') || document.body;
            main.appendChild(container);
        }
        
        return container;
    }
    
    /**
     * Create status indicator if it doesn't exist
     */
    createStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'connection-status';
        indicator.className = 'connection-status fixed top-4 right-4 z-50';
        indicator.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg p-3 border-l-4 border-gray-400">
                <div class="flex items-center">
                    <div id="status-dot" class="w-2 h-2 rounded-full bg-gray-400 mr-2"></div>
                    <span id="status-text" class="text-sm font-medium text-gray-700">Connecting...</span>
                </div>
            </div>
        `;
        
        document.body.appendChild(indicator);
        return indicator;
    }
    
    /**
     * Create notification area if it doesn't exist
     */
    createNotificationArea() {
        const area = document.createElement('div');
        area.id = 'notifications';
        area.className = 'notifications-area fixed top-16 right-4 z-40 space-y-2';
        area.style.maxHeight = '400px';
        area.style.overflowY = 'auto';
        
        document.body.appendChild(area);
        return area;
    }
    
    /**
     * Create log control event listeners
     */
    createLogControls() {
        // Log level filter
        const levelFilter = document.getElementById('log-level-filter');
        if (levelFilter) {
            levelFilter.addEventListener('change', (e) => this.filterLogs(e.target.value));
        }
        
        // Clear logs button
        const clearBtn = document.getElementById('clear-logs');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearLogs());
        }
        
        // Download logs button
        const downloadBtn = document.getElementById('download-logs');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadLogs());
        }
    }
    
    /**
     * Initialize SocketIO connection with enhanced error handling and reconnection
     */
    initializeSocketIO() {
        try {
            if (typeof io === 'undefined') {
                console.error('❌ SocketIO library not loaded');
                this.updateConnectionStatus(false, 'SocketIO library not found');
                return;
            }
            
            // Initialize socket connection
            this.socket = io({
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: this.reconnectDelay,
                timeout: 10000,
                forceNew: true
            });
            
            this.setupSocketEventHandlers();
            
            console.log('🔌 SocketIO initialization started');
            
        } catch (error) {
            console.error('❌ SocketIO initialization failed:', error);
            this.updateConnectionStatus(false, 'Connection failed');
        }
    }
    
    /**
     * Setup comprehensive socket event handlers
     */
    setupSocketEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('✅ SocketIO connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this.updateConnectionStatus(true, 'Connected');
            
            // Check for running pipeline on reconnection
            this.checkForRunningPipeline();
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('❌ SocketIO disconnected:', reason);
            this.isConnected = false;
            this.updateConnectionStatus(false, 'Disconnected');
            
            // Auto-reconnect for certain disconnect reasons
            if (reason === 'io server disconnect') {
                this.socket.connect();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('❌ SocketIO connection error:', error);
            this.reconnectAttempts++;
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30 seconds
            this.updateConnectionStatus(false, `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        });
        
        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`🔄 SocketIO reconnected after ${attemptNumber} attempts`);
            this.updateConnectionStatus(true, 'Reconnected');
        });
        
        this.socket.on('reconnect_failed', () => {
            console.error('❌ SocketIO reconnection failed after maximum attempts');
            this.updateConnectionStatus(false, 'Connection failed');
            this.showNotification('Connection lost. Please refresh the page.', 'error', 0);
        });
        
        // Pipeline events
        this.socket.on('pipeline_progress', (data) => this.handlePipelineProgress(data));
        this.socket.on('pipeline_update', (data) => this.handlePipelineUpdate(data));
        this.socket.on('pipeline_transition', (data) => this.handleStageTransition(data));
        this.socket.on('pipeline_error', (data) => this.handlePipelineError(data));
        this.socket.on('pipeline_completion', (data) => this.handlePipelineCompletion(data));
        
        // Log streaming
        this.socket.on('log_stream', (data) => this.handleLogStream(data));
    }
    
    /**
     * Update connection status indicator
     */
    updateConnectionStatus(connected, message = '') {
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        
        if (statusDot && statusText) {
            if (connected) {
                statusDot.className = 'w-2 h-2 rounded-full bg-green-500 mr-2';
                statusText.textContent = message || 'Connected';
                statusText.className = 'text-sm font-medium text-green-700';
            } else {
                statusDot.className = 'w-2 h-2 rounded-full bg-red-500 mr-2';
                statusText.textContent = message || 'Disconnected';
                statusText.className = 'text-sm font-medium text-red-700';
            }
        }
    }
    
    /**
     * Check for running pipeline on page load/reconnection
     */
    checkForRunningPipeline() {
        // Check if there's a stored session ID
        const storedSession = localStorage.getItem('current_pipeline_session');
        if (storedSession) {
            try {
                const sessionData = JSON.parse(storedSession);
                if (sessionData.status === 'running') {
                    this.currentSession = sessionData.session_id;
                    this.restoreProgressDisplay(sessionData);
                    
                    // Request current status from server
                    fetch(`/pipeline/status/${this.currentSession}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'running') {
                                this.showNotification('Reconnected to running pipeline', 'info', 3000);
                            } else {
                                // Pipeline finished while disconnected
                                localStorage.removeItem('current_pipeline_session');
                                this.hideProgressDisplay();
                            }
                        })
                        .catch(error => {
                            console.error('Failed to check pipeline status:', error);
                        });
                }
            } catch (error) {
                console.error('Failed to parse stored session data:', error);
                localStorage.removeItem('current_pipeline_session');
            }
        }
    }

    /**
     * Restore progress display for reconnected session
     */
    restoreProgressDisplay(sessionData) {
        this.showProgressDisplay();
        this.updateProgressBars(sessionData.selected_stages || []);
        this.showNotification('Restoring pipeline progress...', 'info', 2000);
    }
    
    /**
     * Handle pipeline progress updates
     */
    handlePipelineProgress(data) {
        console.log('📊 Pipeline progress update:', data);
        
        // Store session info
        if (data.session_id && data.status === 'running') {
            this.currentSession = data.session_id;
            localStorage.setItem('current_pipeline_session', JSON.stringify({
                session_id: data.session_id,
                status: 'running',
                timestamp: new Date().toISOString()
            }));
        }
        
        // Update progress display
        this.updateStageProgress(data);
        this.updateCurrentStageDetail(data);
    }
    
    /**
     * Handle pipeline update events (legacy compatibility)
     */
    handlePipelineUpdate(data) {
        this.handlePipelineProgress(data);
    }
    
    /**
     * Handle stage transition notifications
     */
    handleStageTransition(data) {
        console.log('🔄 Stage transition:', data);
        
        this.showNotification(
            `Stage ${data.from_stage} completed, starting Stage ${data.to_stage}`,
            'info',
            3000
        );
        
        // Update stage progress bars
        this.markStageCompleted(data.from_stage);
        this.markStageActive(data.to_stage);
    }
    
    /**
     * Handle pipeline error notifications
     */
    handlePipelineError(data) {
        console.error('❌ Pipeline error:', data);
        
        const severityClass = {
            'warning': 'warning',
            'error': 'error',
            'critical': 'error'
        }[data.severity] || 'error';
        
        this.showNotification(
            `${data.error_type}: ${data.message}`,
            severityClass,
            data.severity === 'critical' ? 0 : 8000
        );
        
        // Update stage status to show error
        if (data.stage) {
            this.markStageError(data.stage);
        }
    }
    
    /**
     * Handle pipeline completion notifications
     */
    handlePipelineCompletion(data) {
        console.log('✅ Pipeline completed:', data);
        
        // Clear stored session
        localStorage.removeItem('current_pipeline_session');
        this.currentSession = null;
        
        // Show completion notification
        const isSuccess = data.status === 'completed';
        this.showNotification(
            isSuccess ? 'Pipeline completed successfully!' : 'Pipeline finished with errors',
            isSuccess ? 'success' : 'warning',
            5000
        );
        
        // Update all completed stages
        if (data.completed_stages) {
            data.completed_stages.forEach(stage => this.markStageCompleted(stage));
        }
        
        // Hide current stage detail after delay
        setTimeout(() => {
            this.hideCurrentStageDetail();
        }, 3000);
    }
    
    /**
     * Handle log stream events
     */
    handleLogStream(data) {
        // Add to log buffer
        this.logBuffer.push(data);
        
        // Limit buffer size
        if (this.logBuffer.length > this.maxLogBufferSize) {
            this.logBuffer.shift();
        }
        
        // Display log entry
        this.displayLogEntry(data);
    }
    
    /**
     * Display a log entry in the log container
     */
    displayLogEntry(logData) {
        const logOutput = document.getElementById('log-output');
        if (!logOutput) return;
        
        // Check if log should be filtered
        const levelFilter = document.getElementById('log-level-filter');
        const currentFilter = levelFilter ? levelFilter.value : 'all';
        
        if (currentFilter !== 'all' && logData.level !== currentFilter) {
            return;
        }
        
        // Create log entry element
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-level-${logData.level.toLowerCase()}`;
        
        const levelColors = {
            'INFO': 'text-green-400',
            'WARNING': 'text-yellow-400',
            'ERROR': 'text-red-400',
            'DEBUG': 'text-blue-400'
        };
        
        const timestamp = new Date(logData.timestamp).toLocaleTimeString();
        
        logEntry.innerHTML = `
            <span class="text-gray-500">[${timestamp}]</span>
            <span class="${levelColors[logData.level] || 'text-green-400'}">[${logData.level}]</span>
            <span class="text-gray-300">${logData.logger}:</span>
            <span class="text-white">${this.escapeHtml(logData.message)}</span>
        `;
        
        // Remove placeholder text if it exists
        const placeholder = logOutput.querySelector('.text-gray-500');
        if (placeholder && placeholder.textContent === 'Waiting for logs...') {
            placeholder.remove();
        }
        
        // Append log entry
        logOutput.appendChild(logEntry);
        
        // Auto-scroll to bottom
        logOutput.scrollTop = logOutput.scrollHeight;
        
        // Limit displayed logs to prevent memory issues
        const logEntries = logOutput.querySelectorAll('.log-entry');
        if (logEntries.length > 500) {
            logEntries[0].remove();
        }
    }
    
    /**
     * Update stage progress display
     */
    updateStageProgress(data) {
        const stageNum = data.stage;
        if (!stageNum) return;
        
        // Store stage progress
        this.stageProgress[stageNum] = {
            progress: data.progress,
            status: data.status,
            sub_stage: data.sub_stage,
            stage_name: data.stage_name
        };
        
        // Update progress bar for this stage
        const progressBar = document.getElementById(`stage-${stageNum}-progress`);
        if (progressBar) {
            progressBar.style.width = `${data.progress}%`;
            
            // Update status classes
            const container = progressBar.closest('.stage-progress-item');
            if (container) {
                container.classList.remove('stage-pending', 'stage-running', 'stage-completed', 'stage-error');
                
                switch (data.status) {
                    case 'running':
                    case 'initializing':
                        container.classList.add('stage-running');
                        break;
                    case 'completed':
                        container.classList.add('stage-completed');
                        break;
                    case 'failed':
                        container.classList.add('stage-error');
                        break;
                    default:
                        container.classList.add('stage-pending');
                }
            }
        }
    }
    
    /**
     * Update current stage detail display
     */
    updateCurrentStageDetail(data) {
        if (data.status === 'running' || data.status === 'initializing') {
            this.showCurrentStageDetail(data);
        }
    }
    
    /**
     * Show current stage detail panel
     */
    showCurrentStageDetail(data) {
        const detailPanel = document.getElementById('current-stage-detail');
        const stageName = document.getElementById('current-stage-name');
        const stageDescription = document.getElementById('current-stage-description');
        const subStage = document.getElementById('current-sub-stage');
        const progressPercent = document.getElementById('current-progress-percent');
        const progressBar = document.getElementById('current-progress-bar');
        
        if (detailPanel && stageName && stageDescription && subStage && progressPercent && progressBar) {
            detailPanel.classList.remove('hidden');
            
            stageName.textContent = data.stage_name || `Stage ${data.stage}`;
            stageDescription.textContent = data.stage_description || '';
            subStage.textContent = data.sub_stage || 'Processing...';
            progressPercent.textContent = `${Math.round(data.progress)}%`;
            progressBar.style.width = `${data.progress}%`;
            
            // Update progress bar color based on status
            progressBar.classList.remove('bg-blue-600', 'bg-green-600', 'bg-red-600');
            switch (data.status) {
                case 'completed':
                    progressBar.classList.add('bg-green-600');
                    break;
                case 'failed':
                    progressBar.classList.add('bg-red-600');
                    break;
                default:
                    progressBar.classList.add('bg-blue-600');
            }
        }
    }
    
    /**
     * Hide current stage detail panel
     */
    hideCurrentStageDetail() {
        const detailPanel = document.getElementById('current-stage-detail');
        if (detailPanel) {
            detailPanel.classList.add('hidden');
        }
    }
    
    /**
     * Show progress display
     */
    showProgressDisplay() {
        if (this.progressContainer) {
            this.progressContainer.classList.remove('hidden');
        }
    }
    
    /**
     * Hide progress display
     */
    hideProgressDisplay() {
        if (this.progressContainer) {
            this.progressContainer.classList.add('hidden');
        }
        this.hideCurrentStageDetail();
    }
    
    /**
     * Create progress bars for selected stages
     */
    updateProgressBars(selectedStages) {
        const container = document.getElementById('stage-progress-bars');
        if (!container) return;
        
        container.innerHTML = '';
        
        const stageDefinitions = {
            1: 'Media Extraction',
            2: 'Transcript Generation',
            3: 'Content Analysis',
            4: 'Narrative Generation',
            5: 'Audio Generation',
            6: 'Video Clipping',
            7: 'Video Compilation'
        };
        
        selectedStages.forEach(stageNum => {
            const stageItem = document.createElement('div');
            stageItem.className = 'stage-progress-item stage-pending';
            stageItem.innerHTML = `
                <div class="flex justify-between items-center mb-1">
                    <span class="text-sm font-medium text-gray-700">Stage ${stageNum}: ${stageDefinitions[stageNum]}</span>
                    <span id="stage-${stageNum}-percent" class="text-sm text-gray-500">0%</span>
                </div>
                <div class="bg-gray-200 rounded-full h-2">
                    <div id="stage-${stageNum}-progress" class="bg-gray-400 h-2 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
            `;
            container.appendChild(stageItem);
        });
    }
    
    /**
     * Mark stage as completed
     */
    markStageCompleted(stageNum) {
        const container = document.querySelector(`#stage-${stageNum}-progress`)?.closest('.stage-progress-item');
        if (container) {
            container.classList.remove('stage-pending', 'stage-running', 'stage-error');
            container.classList.add('stage-completed');
            
            const progressBar = document.getElementById(`stage-${stageNum}-progress`);
            const percentSpan = document.getElementById(`stage-${stageNum}-percent`);
            
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.classList.remove('bg-gray-400', 'bg-blue-600', 'bg-red-600');
                progressBar.classList.add('bg-green-600');
            }
            
            if (percentSpan) {
                percentSpan.textContent = '100%';
            }
        }
    }
    
    /**
     * Mark stage as active
     */
    markStageActive(stageNum) {
        const container = document.querySelector(`#stage-${stageNum}-progress`)?.closest('.stage-progress-item');
        if (container) {
            container.classList.remove('stage-pending', 'stage-completed', 'stage-error');
            container.classList.add('stage-running');
            
            const progressBar = document.getElementById(`stage-${stageNum}-progress`);
            if (progressBar) {
                progressBar.classList.remove('bg-gray-400', 'bg-green-600', 'bg-red-600');
                progressBar.classList.add('bg-blue-600');
            }
        }
    }
    
    /**
     * Mark stage as error
     */
    markStageError(stageNum) {
        const container = document.querySelector(`#stage-${stageNum}-progress`)?.closest('.stage-progress-item');
        if (container) {
            container.classList.remove('stage-pending', 'stage-running', 'stage-completed');
            container.classList.add('stage-error');
            
            const progressBar = document.getElementById(`stage-${stageNum}-progress`);
            if (progressBar) {
                progressBar.classList.remove('bg-gray-400', 'bg-blue-600', 'bg-green-600');
                progressBar.classList.add('bg-red-600');
            }
        }
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        if (!this.notificationArea) return;
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} transform transition-all duration-300 translate-x-full`;
        
        const typeClasses = {
            'info': 'bg-blue-50 border-blue-200 text-blue-800',
            'success': 'bg-green-50 border-green-200 text-green-800',
            'warning': 'bg-yellow-50 border-yellow-200 text-yellow-800',
            'error': 'bg-red-50 border-red-200 text-red-800'
        };
        
        const typeIcons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        };
        
        notification.innerHTML = `
            <div class="border rounded-lg p-3 shadow-lg ${typeClasses[type] || typeClasses.info}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <span class="mr-2">${typeIcons[type] || typeIcons.info}</span>
                        <span class="text-sm font-medium">${this.escapeHtml(message)}</span>
                    </div>
                    <button class="ml-3 text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <span class="text-lg">&times;</span>
                    </button>
                </div>
            </div>
        `;
        
        this.notificationArea.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto-remove after duration (if duration > 0)
        if (duration > 0) {
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }, duration);
        }
    }
    
    /**
     * Filter logs by level
     */
    filterLogs(level) {
        const logOutput = document.getElementById('log-output');
        if (!logOutput) return;
        
        const logEntries = logOutput.querySelectorAll('.log-entry');
        logEntries.forEach(entry => {
            if (level === 'all') {
                entry.style.display = 'block';
            } else {
                const hasLevel = entry.classList.contains(`log-level-${level.toLowerCase()}`);
                entry.style.display = hasLevel ? 'block' : 'none';
            }
        });
    }
    
    /**
     * Clear all logs
     */
    clearLogs() {
        const logOutput = document.getElementById('log-output');
        if (logOutput) {
            logOutput.innerHTML = '<div class="text-gray-500">Logs cleared...</div>';
        }
        this.logBuffer = [];
    }
    
    /**
     * Download logs as file
     */
    downloadLogs() {
        if (this.logBuffer.length === 0) {
            this.showNotification('No logs to download', 'warning', 3000);
            return;
        }
        
        const logText = this.logBuffer.map(log => 
            `[${log.timestamp}] [${log.level}] ${log.logger}: ${log.message}`
        ).join('\n');
        
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pipeline-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showNotification('Logs downloaded successfully', 'success', 3000);
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Start monitoring a pipeline session
     */
    startMonitoring(sessionId, selectedStages) {
        this.currentSession = sessionId;
        this.showProgressDisplay();
        this.updateProgressBars(selectedStages);
        
        // Store session info
        localStorage.setItem('current_pipeline_session', JSON.stringify({
            session_id: sessionId,
            status: 'running',
            selected_stages: selectedStages,
            timestamp: new Date().toISOString()
        }));
        
        console.log(`🎬 Started monitoring pipeline session: ${sessionId}`);
    }
    
    /**
     * Stop monitoring current session
     */
    stopMonitoring() {
        this.currentSession = null;
        localStorage.removeItem('current_pipeline_session');
        this.hideProgressDisplay();
        console.log('🛑 Stopped pipeline monitoring');
    }
    
    /**
     * Public method to get connection status
     */
    isSocketConnected() {
        return this.isConnected && this.socket && this.socket.connected;
    }
    
    /**
     * Public method to get current session
     */
    getCurrentSession() {
        return this.currentSession;
    }
}

// Initialize pipeline monitor when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.YouTubePipelineUI === 'undefined') {
        window.YouTubePipelineUI = {};
    }
    
    // Initialize pipeline monitor
    window.YouTubePipelineUI.pipelineMonitor = new PipelineMonitor();
    
    console.log('🚀 Pipeline Monitor initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PipelineMonitor;
}
