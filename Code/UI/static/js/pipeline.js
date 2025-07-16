/**
 * Pipeline Control & Monitoring JavaScript
 * 
 * Comprehensive pipeline execution control with real-time monitoring, progress visualization,
 * and responsive user interface for all 7 pipeline stages with sub-stage indicators.
 * 
 * Created: June 20, 2025
 * Agent: Implementation Agent
 * Task Reference: Phase 4, Task 4.2 - JavaScript Client Implementation
 */

class PipelineController {
    constructor() {
        this.socket = null;
        this.currentSession = null;
        this.isConnected = false;
        this.currentExecution = null;
        this.executionState = 'idle'; // idle, initializing, running, completed, failed, interrupted
        
        // UI elements
        this.pipelineForm = null;
        this.startButton = null;
        this.stopButton = null;
        this.pauseButton = null;
        this.progressContainer = null;
        this.stageProgressBars = {};
        this.currentStageDetail = null;
        
        // Progress tracking
        this.stageDefinitions = {
            1: {
                name: 'Media Extraction',
                description: 'Download and extract audio/video from YouTube',
                icon: '📹',
                subStages: [
                    'Initializing download',
                    'Downloading video', 
                    'Extracting audio',
                    'Validating files',
                    'Organizing output'
                ]
            },
            2: {
                name: 'Audio Processing',
                description: 'Process and enhance audio quality',
                icon: '🎵',
                subStages: [
                    'Loading audio file',
                    'Analyzing audio quality',
                    'Applying filters',
                    'Normalizing volume',
                    'Saving processed audio'
                ]
            },
            3: {
                name: 'Content Analysis',
                description: 'Analyze content for segment detection',
                icon: '🔍',
                subStages: [
                    'Transcribing audio',
                    'Detecting speech patterns',
                    'Analyzing content themes',
                    'Identifying segments',
                    'Calculating confidence scores'
                ]
            },
            4: {
                name: 'Segment Detection',
                description: 'Detect and classify content segments',
                icon: '📊',
                subStages: [
                    'Loading analysis results',
                    'Applying detection algorithms',
                    'Classifying segment types',
                    'Merging similar segments',
                    'Finalizing segment boundaries'
                ]
            },
            5: {
                name: 'Quality Assessment',
                description: 'Assess segment quality and relevance',
                icon: '⭐',
                subStages: [
                    'Evaluating content quality',
                    'Checking audio clarity',
                    'Assessing topic relevance',
                    'Calculating quality scores',
                    'Ranking segments'
                ]
            },
            6: {
                name: 'Selection Processing',
                description: 'Process selected segments for compilation',
                icon: '✂️',
                subStages: [
                    'Loading segment selections',
                    'Extracting selected clips',
                    'Applying transitions',
                    'Synchronizing audio',
                    'Preparing for compilation'
                ]
            },
            7: {
                name: 'Final Compilation',
                description: 'Compile and export final video',
                icon: '🎬',
                subStages: [
                    'Setting up compilation',
                    'Merging video clips',
                    'Adding audio tracks',
                    'Applying final effects',
                    'Exporting final video'
                ]
            }
        };
        
        this.stageProgress = {};
        this.currentStage = null;
        this.currentSubStage = null;
        
        this.initialize();
    }
    
    /**
     * Initialize the pipeline controller
     */
    initialize() {
        this.initializeUI();
        this.initializeSocketIO();
        this.setupEventListeners();
        this.checkForRunningPipeline();
        
        console.log('🎯 Pipeline Controller initialized');
    }
    
    /**
     * Initialize UI elements
     */
    initializeUI() {
        // Find or create pipeline form
        this.pipelineForm = document.getElementById('pipeline-form');
        if (!this.pipelineForm) {
            console.warn('⚠️ Pipeline form not found');
            return;
        }
        
        // Find control buttons
        this.startButton = document.getElementById('start-pipeline-btn') || 
                          this.pipelineForm.querySelector('button[type="submit"]');
        this.stopButton = document.getElementById('stop-pipeline-btn');
        this.pauseButton = document.getElementById('pause-pipeline-btn');
        
        // Create missing buttons
        if (!this.stopButton) {
            this.stopButton = this.createControlButton('stop', 'Stop Pipeline', 'bg-red-600 hover:bg-red-700');
        }
        if (!this.pauseButton) {
            this.pauseButton = this.createControlButton('pause', 'Pause Pipeline', 'bg-yellow-600 hover:bg-yellow-700');
        }
        
        // Find or create progress container
        this.progressContainer = document.getElementById('pipeline-progress');
        if (!this.progressContainer) {
            this.progressContainer = this.createProgressContainer();
        }
        
        this.createStageProgressBars();
        this.updateButtonStates();
    }
    
    /**
     * Create control button
     */
    createControlButton(action, text, classes) {
        const button = document.createElement('button');
        button.type = 'button';
        button.id = `${action}-pipeline-btn`;
        button.className = `px-4 py-2 text-white rounded-lg font-medium transition-colors ${classes} disabled:opacity-50 disabled:cursor-not-allowed ml-3`;
        button.textContent = text;
        button.disabled = true;
        
        // Insert after start button
        if (this.startButton && this.startButton.parentNode) {
            this.startButton.parentNode.insertBefore(button, this.startButton.nextSibling);
        }
        
        return button;
    }
    
    /**
     * Create progress container
     */
    createProgressContainer() {
        const container = document.createElement('div');
        container.id = 'pipeline-progress';
        container.className = 'bg-white rounded-lg shadow-md p-6 mb-6 hidden';
        container.innerHTML = `
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-lg font-semibold text-gray-900">Pipeline Progress</h3>
                <div id="pipeline-status" class="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                    Idle
                </div>
            </div>
            <div id="stage-progress-bars" class="space-y-4 mb-6"></div>
            <div id="current-stage-detail" class="p-4 bg-gray-50 rounded-lg hidden">
                <div class="flex items-center mb-2">
                    <span id="current-stage-icon" class="text-2xl mr-3">📹</span>
                    <div>
                        <h4 id="current-stage-name" class="font-medium text-gray-900">Stage Name</h4>
                        <p id="current-stage-description" class="text-sm text-gray-600">Stage Description</p>
                    </div>
                </div>
                <div class="mt-3">
                    <div class="flex justify-between text-sm text-gray-700 mb-1">
                        <span id="current-sub-stage">Initializing...</span>
                        <span id="current-progress-percent">0%</span>
                    </div>
                    <div class="bg-gray-200 rounded-full h-2">
                        <div id="current-progress-bar" class="bg-blue-600 h-2 rounded-full transition-all duration-500" style="width: 0%"></div>
                    </div>
                </div>
                <div id="stage-timing" class="mt-2 text-xs text-gray-500">
                    <span id="stage-elapsed">Elapsed: 00:00</span>
                    <span id="stage-estimated" class="ml-4">Estimated: --:--</span>
                </div>
            </div>
        `;
        
        // Insert after pipeline form
        if (this.pipelineForm && this.pipelineForm.parentNode) {
            this.pipelineForm.parentNode.insertBefore(container, this.pipelineForm.nextSibling);
        } else {
            document.querySelector('main').appendChild(container);
        }
        
        return container;
    }
    
    /**
     * Create progress bars for all stages
     */
    createStageProgressBars() {
        const container = document.getElementById('stage-progress-bars');
        if (!container) return;
        
        container.innerHTML = '';
        
        Object.entries(this.stageDefinitions).forEach(([stageNum, stageInfo]) => {
            const stageBar = document.createElement('div');
            stageBar.className = 'stage-progress-item';
            stageBar.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center">
                        <span class="text-lg mr-2">${stageInfo.icon}</span>
                        <span class="font-medium text-gray-900">Stage ${stageNum}: ${stageInfo.name}</span>
                        <span id="stage-${stageNum}-status" class="ml-2 px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600">Pending</span>
                    </div>
                    <span id="stage-${stageNum}-percent" class="text-sm text-gray-500">0%</span>
                </div>
                <div class="bg-gray-200 rounded-full h-2">
                    <div id="stage-${stageNum}-progress" class="bg-blue-600 h-2 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
                <div id="stage-${stageNum}-substage" class="text-xs text-gray-500 mt-1 hidden">Waiting...</div>
            `;
            
            container.appendChild(stageBar);
            
            // Initialize progress tracking
            this.stageProgress[stageNum] = {
                progress: 0,
                status: 'pending',
                subStage: null,
                startTime: null,
                endTime: null
            };
        });
    }
    
    /**
     * Initialize SocketIO connection
     */
    initializeSocketIO() {
        if (typeof io === 'undefined') {
            console.error('❌ SocketIO not loaded');
            return;
        }
        
        this.socket = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 10000,
            forceNew: false
        });
        
        this.setupSocketEventHandlers();
    }
    
    /**
     * Setup SocketIO event handlers
     */
    setupSocketEventHandlers() {
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.updateConnectionStatus(true);
            console.log('🔗 Connected to pipeline server');
        });
        
        this.socket.on('disconnect', () => {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            console.log('❌ Disconnected from pipeline server');
        });
        
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
        
        this.socket.on('log_stream', (data) => {
            this.handleLogStream(data);
        });
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Form submission
        if (this.pipelineForm) {
            this.pipelineForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startPipelineExecution();
            });
        }
        
        // Control buttons
        if (this.stopButton) {
            this.stopButton.addEventListener('click', () => {
                this.stopPipelineExecution();
            });
        }
        
        if (this.pauseButton) {
            this.pauseButton.addEventListener('click', () => {
                this.pausePipelineExecution();
            });
        }
        
        // Stage selection validation
        const stageCheckboxes = document.querySelectorAll('input[name="selected_stages"]');
        stageCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.validateStageSelection();
            });
        });
    }
    
    /**
     * Start pipeline execution
     */
    async startPipelineExecution() {
        if (this.currentExecution) {
            this.showNotification('Pipeline is already running', 'warning');
            return;
        }
        
        // Validate form
        if (!this.validateForm()) {
            return;
        }
        
        // Show progress container
        this.progressContainer.classList.remove('hidden');
        this.updateExecutionState('initializing');
        
        try {
            // Convert form data to JSON
            const formData = new FormData(this.pipelineForm);
            const jsonData = {};
            formData.forEach((value, key) => {
                if (jsonData[key]) {
                    if (!Array.isArray(jsonData[key])) jsonData[key] = [jsonData[key]];
                    jsonData[key].push(value);
                } else {
                    jsonData[key] = value;
                }
            });
            const response = await fetch('/pipeline/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jsonData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentExecution = result.session_id;
                this.currentSession = result.session_id;
                this.updateExecutionState('running');
                this.showNotification('Pipeline started successfully', 'success');
                
                // Reset progress tracking
                this.resetProgressTracking();
                
            } else {
                this.updateExecutionState('failed');
                this.showNotification(result.error || 'Failed to start pipeline', 'error');
            }
            
        } catch (error) {
            this.updateExecutionState('failed');
            this.showNotification('Network error: ' + error.message, 'error');
            console.error('Pipeline start error:', error);
        }
    }
    
    /**
     * Stop pipeline execution
     */
    async stopPipelineExecution() {
        if (!this.currentExecution) {
            this.showNotification('No pipeline is currently running', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/pipeline/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.currentExecution
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Pipeline stop requested', 'info');
            } else {
                this.showNotification(result.error || 'Failed to stop pipeline', 'error');
            }
            
        } catch (error) {
            this.showNotification('Network error: ' + error.message, 'error');
            console.error('Pipeline stop error:', error);
        }
    }
    
    /**
     * Pause pipeline execution
     */
    async pausePipelineExecution() {
        if (!this.currentExecution) {
            this.showNotification('No pipeline is currently running', 'warning');
            return;
        }
        
        // Implementation for pause functionality
        this.showNotification('Pause functionality coming soon', 'info');
    }
    
    /**
     * Handle pipeline progress updates
     */
    handlePipelineProgress(data) {
        if (data.session_id !== this.currentSession) return;
        
        const stage = parseInt(data.stage);
        const progress = parseFloat(data.progress) || 0;
        
        // Update stage progress
        if (this.stageProgress[stage]) {
            this.stageProgress[stage].progress = progress;
            this.stageProgress[stage].status = data.status || 'running';
            this.stageProgress[stage].subStage = data.sub_stage;
            
            if (data.status === 'running' && !this.stageProgress[stage].startTime) {
                this.stageProgress[stage].startTime = new Date();
            }
        }
        
        // Update UI
        this.updateStageProgressBar(stage, progress, data.status);
        
        if (data.status === 'running') {
            this.updateCurrentStageDetail(stage, data.sub_stage, progress);
        }
        
        // Update overall status
        if (stage !== this.currentStage) {
            this.currentStage = stage;
            this.markPreviousStagesComplete(stage);
        }
    }
    
    /**
     * Handle pipeline update
     */
    handlePipelineUpdate(data) {
        console.log('Pipeline update:', data);
        
        if (data.message) {
            this.showNotification(data.message, 'info');
        }
    }
    
    /**
     * Handle pipeline error
     */
    handlePipelineError(data) {
        console.error('Pipeline error:', data);
        
        this.updateExecutionState('failed');
        this.showNotification(data.error || 'Pipeline error occurred', 'error');
        
        // Mark current stage as failed
        if (this.currentStage && this.stageProgress[this.currentStage]) {
            this.stageProgress[this.currentStage].status = 'failed';
            this.updateStageProgressBar(this.currentStage, this.stageProgress[this.currentStage].progress, 'failed');
        }
    }
    
    /**
     * Handle pipeline completion
     */
    handlePipelineCompletion(data) {
        console.log('Pipeline completed:', data);
        
        this.updateExecutionState('completed');
        this.showNotification('Pipeline completed successfully!', 'success');
        
        // Mark all stages as complete
        Object.keys(this.stageProgress).forEach(stage => {
            this.stageProgress[stage].status = 'completed';
            this.stageProgress[stage].progress = 100;
            this.stageProgress[stage].endTime = new Date();
            this.updateStageProgressBar(parseInt(stage), 100, 'completed');
        });
        
        // Hide current stage detail
        const currentStageDetail = document.getElementById('current-stage-detail');
        if (currentStageDetail) {
            currentStageDetail.classList.add('hidden');
        }
        
        this.currentExecution = null;
        this.currentSession = null;
    }
    
    /**
     * Handle pipeline interruption
     */
    handlePipelineInterruption(data) {
        console.log('Pipeline interrupted:', data);
        
        this.updateExecutionState('interrupted');
        this.showNotification('Pipeline was interrupted', 'warning');
        
        this.currentExecution = null;
        this.currentSession = null;
    }
    
    /**
     * Handle log stream
     */
    handleLogStream(data) {
        // Delegate to log handler if available
        if (window.YouTubePipelineUI && window.YouTubePipelineUI.logHandler) {
            window.YouTubePipelineUI.logHandler.addLogEntry(data);
        }
    }
    
    /**
     * Update stage progress bar
     */
    updateStageProgressBar(stage, progress, status) {
        const progressBar = document.getElementById(`stage-${stage}-progress`);
        const percentElement = document.getElementById(`stage-${stage}-percent`);
        const statusElement = document.getElementById(`stage-${stage}-status`);
        const subStageElement = document.getElementById(`stage-${stage}-substage`);
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            
            // Update color based on status
            progressBar.className = progressBar.className.replace(/(bg-\w+-\d+)/g, '');
            switch (status) {
                case 'completed':
                    progressBar.classList.add('bg-green-600');
                    break;
                case 'failed':
                    progressBar.classList.add('bg-red-600');
                    break;
                case 'running':
                    progressBar.classList.add('bg-blue-600');
                    break;
                default:
                    progressBar.classList.add('bg-gray-400');
            }
        }
        
        if (percentElement) {
            percentElement.textContent = `${Math.round(progress)}%`;
        }
        
        if (statusElement) {
            statusElement.textContent = this.formatStatus(status);
            statusElement.className = statusElement.className.replace(/(bg-\w+-\d+)|(text-\w+-\d+)/g, '');
            
            switch (status) {
                case 'completed':
                    statusElement.classList.add('bg-green-100', 'text-green-800');
                    break;
                case 'failed':
                    statusElement.classList.add('bg-red-100', 'text-red-800');
                    break;
                case 'running':
                    statusElement.classList.add('bg-blue-100', 'text-blue-800');
                    break;
                default:
                    statusElement.classList.add('bg-gray-100', 'text-gray-600');
            }
        }
        
        if (subStageElement && this.stageProgress[stage] && this.stageProgress[stage].subStage) {
            subStageElement.textContent = this.stageProgress[stage].subStage;
            subStageElement.classList.remove('hidden');
        }
    }
    
    /**
     * Update current stage detail
     */
    updateCurrentStageDetail(stage, subStage, progress) {
        const stageInfo = this.stageDefinitions[stage];
        if (!stageInfo) return;
        
        const currentStageDetail = document.getElementById('current-stage-detail');
        const stageIcon = document.getElementById('current-stage-icon');
        const stageName = document.getElementById('current-stage-name');
        const stageDescription = document.getElementById('current-stage-description');
        const currentSubStage = document.getElementById('current-sub-stage');
        const progressPercent = document.getElementById('current-progress-percent');
        const progressBar = document.getElementById('current-progress-bar');
        
        if (currentStageDetail) {
            currentStageDetail.classList.remove('hidden');
        }
        
        if (stageIcon) {
            stageIcon.textContent = stageInfo.icon;
        }
        
        if (stageName) {
            stageName.textContent = `Stage ${stage}: ${stageInfo.name}`;
        }
        
        if (stageDescription) {
            stageDescription.textContent = stageInfo.description;
        }
        
        if (currentSubStage) {
            currentSubStage.textContent = subStage || 'Processing...';
        }
        
        if (progressPercent) {
            progressPercent.textContent = `${Math.round(progress)}%`;
        }
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        // Update timing information
        this.updateStageTiming(stage);
    }
    
    /**
     * Update stage timing information
     */
    updateStageTiming(stage) {
        const stageData = this.stageProgress[stage];
        if (!stageData || !stageData.startTime) return;
        
        const elapsedElement = document.getElementById('stage-elapsed');
        const estimatedElement = document.getElementById('stage-estimated');
        
        if (elapsedElement) {
            const elapsed = Math.floor((new Date() - stageData.startTime) / 1000);
            elapsedElement.textContent = `Elapsed: ${this.formatTime(elapsed)}`;
        }
        
        if (estimatedElement && stageData.progress > 0) {
            const elapsed = Math.floor((new Date() - stageData.startTime) / 1000);
            const estimated = Math.floor((elapsed / stageData.progress) * 100);
            const remaining = Math.max(0, estimated - elapsed);
            estimatedElement.textContent = `Remaining: ${this.formatTime(remaining)}`;
        }
    }
    
    /**
     * Mark previous stages as complete
     */
    markPreviousStagesComplete(currentStage) {
        for (let i = 1; i < currentStage; i++) {
            if (this.stageProgress[i] && this.stageProgress[i].status !== 'completed') {
                this.stageProgress[i].status = 'completed';
                this.stageProgress[i].progress = 100;
                this.stageProgress[i].endTime = new Date();
                this.updateStageProgressBar(i, 100, 'completed');
            }
        }
    }
    
    /**
     * Reset progress tracking
     */
    resetProgressTracking() {
        Object.keys(this.stageProgress).forEach(stage => {
            this.stageProgress[stage] = {
                progress: 0,
                status: 'pending',
                subStage: null,
                startTime: null,
                endTime: null
            };
            this.updateStageProgressBar(parseInt(stage), 0, 'pending');
        });
        
        // Hide current stage detail
        const currentStageDetail = document.getElementById('current-stage-detail');
        if (currentStageDetail) {
            currentStageDetail.classList.add('hidden');
        }
    }
    
    /**
     * Update execution state
     */
    updateExecutionState(state) {
        this.executionState = state;
        this.updateButtonStates();
        this.updatePipelineStatus();
    }
    
    /**
     * Update button states
     */
    updateButtonStates() {
        const isRunning = this.executionState === 'running' || this.executionState === 'initializing';
        
        if (this.startButton) {
            this.startButton.disabled = isRunning || !this.isConnected;
            this.startButton.textContent = isRunning ? 'Pipeline Running...' : 'Start Pipeline';
        }
        
        if (this.stopButton) {
            this.stopButton.disabled = !isRunning;
        }
        
        if (this.pauseButton) {
            this.pauseButton.disabled = !isRunning;
        }
    }
    
    /**
     * Update pipeline status indicator
     */
    updatePipelineStatus() {
        const statusElement = document.getElementById('pipeline-status');
        if (!statusElement) return;
        
        statusElement.textContent = this.formatStatus(this.executionState);
        statusElement.className = statusElement.className.replace(/(bg-\w+-\d+)|(text-\w+-\d+)/g, '');
        
        switch (this.executionState) {
            case 'running':
                statusElement.classList.add('bg-blue-100', 'text-blue-800');
                break;
            case 'completed':
                statusElement.classList.add('bg-green-100', 'text-green-800');
                break;
            case 'failed':
                statusElement.classList.add('bg-red-100', 'text-red-800');
                break;
            case 'interrupted':
                statusElement.classList.add('bg-yellow-100', 'text-yellow-800');
                break;
            case 'initializing':
                statusElement.classList.add('bg-indigo-100', 'text-indigo-800');
                break;
            default:
                statusElement.classList.add('bg-gray-100', 'text-gray-800');
        }
    }
    
    /**
     * Update connection status
     */
    updateConnectionStatus(connected) {
        // Update any connection indicators
        const indicators = document.querySelectorAll('.connection-indicator');
        indicators.forEach(indicator => {
            if (connected) {
                indicator.classList.remove('text-red-500');
                indicator.classList.add('text-green-500');
                indicator.textContent = 'Connected';
            } else {
                indicator.classList.remove('text-green-500');
                indicator.classList.add('text-red-500');
                indicator.textContent = 'Disconnected';
            }
        });
        
        this.updateButtonStates();
    }
    
    /**
     * Check for running pipeline on page load
     */
    async checkForRunningPipeline() {
        try {
            const response = await fetch('/pipeline/status');
            const result = await response.json();
            
            if (result.session_id && result.status === 'running') {
                this.currentExecution = result.session_id;
                this.currentSession = result.session_id;
                this.updateExecutionState('running');
                this.progressContainer.classList.remove('hidden');
                this.showNotification('Reconnected to running pipeline', 'info');
            }
        } catch (error) {
            console.log('No running pipeline found');
        }
    }
    
    /**
     * Validate form before submission
     */
    validateForm() {
        const youtubeUrl = document.getElementById('youtube-url');
        if (!youtubeUrl || !youtubeUrl.value.trim()) {
            this.showNotification('Please enter a YouTube URL', 'error');
            return false;
        }
        
        // Validate YouTube URL format
        const urlPattern = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
        if (!urlPattern.test(youtubeUrl.value.trim())) {
            this.showNotification('Please enter a valid YouTube URL', 'error');
            return false;
        }
        
        return this.validateStageSelection();
    }
    
    /**
     * Validate stage selection
     */
    validateStageSelection() {
        const selectedStages = document.querySelectorAll('input[name="selected_stages"]:checked');
        if (selectedStages.length === 0) {
            this.showNotification('Please select at least one pipeline stage', 'error');
            return false;
        }
        
        // Validate sequential execution
        const stageNumbers = Array.from(selectedStages).map(cb => parseInt(cb.value)).sort((a, b) => a - b);
        for (let i = 1; i < stageNumbers.length; i++) {
            if (stageNumbers[i] !== stageNumbers[i-1] + 1) {
                // Check if there are any gaps
                const hasGaps = stageNumbers[i] - stageNumbers[i-1] > 1;
                if (hasGaps) {
                    const missingStages = [];
                    for (let j = stageNumbers[i-1] + 1; j < stageNumbers[i]; j++) {
                        missingStages.push(j);
                    }
                    this.showNotification(`Warning: Skipping stages ${missingStages.join(', ')} may cause issues`, 'warning');
                }
            }
        }
        
        return true;
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Use existing notification system or create simple alert
        if (window.YouTubePipelineUI && window.YouTubePipelineUI.showNotification) {
            window.YouTubePipelineUI.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
            
            // Create temporary notification
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-sm ${this.getNotificationClasses(type)}`;
            notification.innerHTML = `
                <div class="flex items-center">
                    <span class="mr-2">${this.getNotificationIcon(type)}</span>
                    <span>${message}</span>
                    <button class="ml-auto text-lg font-bold opacity-70 hover:opacity-100" onclick="this.parentElement.parentElement.remove()">&times;</button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
    }
    
    /**
     * Get notification classes based on type
     */
    getNotificationClasses(type) {
        switch (type) {
            case 'success': return 'bg-green-100 text-green-800 border border-green-300';
            case 'error': return 'bg-red-100 text-red-800 border border-red-300';
            case 'warning': return 'bg-yellow-100 text-yellow-800 border border-yellow-300';
            default: return 'bg-blue-100 text-blue-800 border border-blue-300';
        }
    }
    
    /**
     * Get notification icon based on type
     */
    getNotificationIcon(type) {
        switch (type) {
            case 'success': return '✅';
            case 'error': return '❌';
            case 'warning': return '⚠️';
            default: return 'ℹ️';
        }
    }
    
    /**
     * Format status text
     */
    formatStatus(status) {
        return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ');
    }
    
    /**
     * Format time in MM:SS format
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
}

// Initialize pipeline controller when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('pipeline-form')) {
        window.YouTubePipelineUI = window.YouTubePipelineUI || {};
        window.YouTubePipelineUI.pipelineController = new PipelineController();
        console.log('🎯 Pipeline Controller ready');
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PipelineController;
}
