/**
 * Pipeline Integration - Enhanced Form Handling
 * 
 * This file integrates the existing pipeline form with the new real-time monitoring system,
 * providing seamless user experience for pipeline execution control.
 * 
 * Created: June 20, 2025
 * Agent: Agent_Realtime_System
 * Task Reference: Phase 4, Task 4.1 - SocketIO Integration
 */

class PipelineIntegration {
    constructor() {
        this.pipelineForm = null;
        this.startButton = null;
        this.stopButton = null;
        this.monitor = null;
        this.currentExecution = null;
        
        this.initializeIntegration();
    }
    
    /**
     * Initialize pipeline form integration
     */
    initializeIntegration() {
        // Wait for pipeline monitor to be available
        if (typeof window.YouTubePipelineUI !== 'undefined' && 
            window.YouTubePipelineUI.pipelineMonitor) {
            this.monitor = window.YouTubePipelineUI.pipelineMonitor;
            this.setupFormHandlers();
        } else {
            // Retry after a short delay
            setTimeout(() => this.initializeIntegration(), 500);
        }
    }
    
    /**
     * Setup form event handlers
     */
    setupFormHandlers() {
        // Find pipeline form
        this.pipelineForm = document.getElementById('pipeline-form') || 
                           document.querySelector('form[action*="pipeline"]');
        
        if (this.pipelineForm) {
            this.setupFormSubmission();
            this.setupControlButtons();
            this.enhanceStageSelection();
            console.log('✅ Pipeline form integration ready');
        } else {
            console.warn('⚠️ Pipeline form not found');
        }
    }
    
    /**
     * Setup enhanced form submission
     */
    setupFormSubmission() {
        this.pipelineForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (this.currentExecution) {
                this.showAlert('Pipeline is already running. Stop current execution first.', 'warning');
                return;
            }
            
            await this.startPipelineExecution();
        });
    }
    
    /**
     * Setup start/stop control buttons
     */
    setupControlButtons() {
        // Find or create start button
        this.startButton = document.getElementById('start-pipeline-btn') || 
                          this.pipelineForm.querySelector('button[type="submit"]');
        
        if (this.startButton) {
            this.startButton.addEventListener('click', (e) => {
                if (this.currentExecution) {
                    e.preventDefault();
                    this.showAlert('Pipeline is already running', 'warning');
                }
            });
        }
        
        // Create stop button if it doesn't exist
        this.stopButton = document.getElementById('stop-pipeline-btn');
        if (!this.stopButton && this.startButton) {
            this.stopButton = this.createStopButton();
        }
        
        if (this.stopButton) {
            this.stopButton.addEventListener('click', () => this.stopPipelineExecution());
        }
        
        this.updateButtonStates();
    }
    
    /**
     * Create stop button
     */
    createStopButton() {
        const stopBtn = document.createElement('button');
        stopBtn.id = 'stop-pipeline-btn';
        stopBtn.type = 'button';
        stopBtn.className = 'ml-3 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
        stopBtn.innerHTML = `
            <svg class="inline w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10h6v4H9z"></path>
            </svg>
            Stop Pipeline
        `;
        stopBtn.disabled = true;
        
        // Insert after start button
        if (this.startButton && this.startButton.parentNode) {
            this.startButton.parentNode.insertBefore(stopBtn, this.startButton.nextSibling);
        }
        
        return stopBtn;
    }
    
    /**
     * Enhance stage selection with dependencies
     */
    enhanceStageSelection() {
        const stageCheckboxes = this.pipelineForm.querySelectorAll('input[name="selected_stages"]');
        
        stageCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.validateStageSelection();
                this.updateProgressPreview();
            });
        });
        
        // Initial validation
        this.validateStageSelection();
    }
    
    /**
     * Validate stage selection dependencies
     */
    validateStageSelection() {
        const stageCheckboxes = this.pipelineForm.querySelectorAll('input[name="selected_stages"]:checked');
        const selectedStages = Array.from(stageCheckboxes).map(cb => parseInt(cb.value)).sort();
        
        // Update form validation state
        const isValid = selectedStages.length > 0;
        this.updateFormValidation(isValid, selectedStages);
        
        return isValid;
    }
    
    /**
     * Update form validation state
     */
    updateFormValidation(isValid, selectedStages) {
        if (this.startButton) {
            this.startButton.disabled = !isValid || !!this.currentExecution;
        }
        
        // Show stage count
        this.updateStageCount(selectedStages.length);
    }
    
    /**
     * Update stage count display
     */
    updateStageCount(count) {
        let countDisplay = document.getElementById('stage-count-display');
        
        if (!countDisplay && count > 0) {
            countDisplay = document.createElement('div');
            countDisplay.id = 'stage-count-display';
            countDisplay.className = 'mt-2 text-sm text-gray-600';
            
            const stageContainer = this.pipelineForm.querySelector('.stage-selection') || 
                                 this.pipelineForm.querySelector('fieldset') ||
                                 this.pipelineForm;
            stageContainer.appendChild(countDisplay);
        }
        
        if (countDisplay) {
            if (count > 0) {
                countDisplay.textContent = `${count} stage${count !== 1 ? 's' : ''} selected`;
                countDisplay.style.display = 'block';
            } else {
                countDisplay.style.display = 'none';
            }
        }
    }
    
    /**
     * Update progress preview
     */
    updateProgressPreview() {
        const selectedStages = this.getSelectedStages();
        
        if (selectedStages.length > 0 && this.monitor) {
            // Show estimated time or stage info
            this.showStagePreview(selectedStages);
        }
    }
    
    /**
     * Show stage selection preview
     */
    showStagePreview(stages) {
        const stageNames = {
            1: 'Media Extraction',
            2: 'Transcript Generation', 
            3: 'Content Analysis',
            4: 'Narrative Generation',
            5: 'Audio Generation',
            6: 'Video Clipping',
            7: 'Video Compilation'
        };
        
        let previewDiv = document.getElementById('stage-preview');
        
        if (!previewDiv) {
            previewDiv = document.createElement('div');
            previewDiv.id = 'stage-preview';
            previewDiv.className = 'mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md';
            
            const stageContainer = this.pipelineForm.querySelector('.stage-selection') || 
                                 this.pipelineForm.querySelector('fieldset') ||
                                 this.pipelineForm;
            stageContainer.appendChild(previewDiv);
        }
        
        if (stages.length > 0) {
            const stageList = stages.map(stage => stageNames[stage] || `Stage ${stage}`).join(' → ');
            previewDiv.innerHTML = `
                <div class="flex items-center">
                    <svg class="w-4 h-4 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div>
                        <div class="text-sm font-medium text-blue-800">Pipeline Execution Order:</div>
                        <div class="text-sm text-blue-600">${stageList}</div>
                    </div>
                </div>
            `;
            previewDiv.style.display = 'block';
        } else {
            previewDiv.style.display = 'none';
        }
    }
    
    /**
     * Start pipeline execution
     */
    async startPipelineExecution() {
        try {
            if (!this.validateStageSelection()) {
                this.showAlert('Please select at least one stage to execute', 'error');
                return;
            }
            
            const formData = this.getFormData();
            
            // Update UI state
            this.updateButtonStates(true);
            this.showAlert('Starting pipeline execution...', 'info');
            
            // Submit form data
            const response = await fetch('/pipeline/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (response.ok && result.status === 'started') {
                this.currentExecution = {
                    session_id: result.session_id,
                    selected_stages: formData.selected_stages,
                    started_at: new Date().toISOString()
                };
                
                // Start monitoring
                if (this.monitor) {
                    this.monitor.startMonitoring(result.session_id, formData.selected_stages);
                }
                
                this.showAlert('Pipeline started successfully', 'success');
                
                // Store execution state
                localStorage.setItem('current_pipeline_execution', JSON.stringify(this.currentExecution));
                
            } else {
                throw new Error(result.error || 'Failed to start pipeline');
            }
            
        } catch (error) {
            console.error('Pipeline start error:', error);
            this.showAlert(`Failed to start pipeline: ${error.message}`, 'error');
            this.updateButtonStates(false);
        }
    }
    
    /**
     * Stop pipeline execution
     */
    async stopPipelineExecution() {
        if (!this.currentExecution) {
            this.showAlert('No pipeline is currently running', 'warning');
            return;
        }
        
        try {
            const confirmed = confirm('Are you sure you want to stop the pipeline execution? This cannot be undone.');
            
            if (!confirmed) return;
            
            this.showAlert('Stopping pipeline...', 'info');
            
            const response = await fetch(`/pipeline/interrupt/${this.currentExecution.session_id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.currentExecution = null;
                this.updateButtonStates(false);
                
                // Stop monitoring
                if (this.monitor) {
                    this.monitor.stopMonitoring();
                }
                
                this.showAlert('Pipeline stopped successfully', 'success');
                
                // Clear stored state
                localStorage.removeItem('current_pipeline_execution');
                
            } else {
                throw new Error(result.error || 'Failed to stop pipeline');
            }
            
        } catch (error) {
            console.error('Pipeline stop error:', error);
            this.showAlert(`Failed to stop pipeline: ${error.message}`, 'error');
        }
    }
    
    /**
     * Get form data for submission
     */
    getFormData() {
        const formData = new FormData(this.pipelineForm);
        const data = {
            youtube_url: formData.get('youtube_url') || '',
            selected_stages: this.getSelectedStages(),
            execution_mode: formData.get('execution_mode') || 'custom'
        };
        
        // Add episode directory if available
        const episodeDir = formData.get('episode_directory');
        if (episodeDir) {
            data.episode_directory = episodeDir;
        }
        
        return data;
    }
    
    /**
     * Get selected stages from form
     */
    getSelectedStages() {
        const checkboxes = this.pipelineForm.querySelectorAll('input[name="selected_stages"]:checked');
        return Array.from(checkboxes).map(cb => parseInt(cb.value)).sort();
    }
    
    /**
     * Update button states
     */
    updateButtonStates(isRunning = false) {
        if (this.startButton) {
            this.startButton.disabled = isRunning || !this.validateStageSelection();
            this.startButton.innerHTML = isRunning ? 
                `<svg class="inline w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>Starting...` :
                `<svg class="inline w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m-10 5a9 9 0 1118 0 9 9 0 01-18 0z"></path>
                </svg>Start Pipeline`;
        }
        
        if (this.stopButton) {
            this.stopButton.disabled = !isRunning;
        }
    }
    
    /**
     * Show alert message
     */
    showAlert(message, type = 'info') {
        if (this.monitor && this.monitor.showNotification) {
            this.monitor.showNotification(message, type, type === 'error' ? 8000 : 4000);
        } else {
            // Fallback alert
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    /**
     * Check for resumed execution on page load
     */
    checkForResumedExecution() {
        const storedExecution = localStorage.getItem('current_pipeline_execution');
        if (storedExecution) {
            try {
                this.currentExecution = JSON.parse(storedExecution);
                this.updateButtonStates(true);
                console.log('Resumed pipeline execution state');
            } catch (error) {
                console.error('Failed to parse stored execution state:', error);
                localStorage.removeItem('current_pipeline_execution');
            }
        }
    }
    
    /**
     * Listen for pipeline completion events
     */
    setupPipelineEventListeners() {
        if (this.monitor && this.monitor.socket) {
            this.monitor.socket.on('pipeline_completion', (data) => {
                if (this.currentExecution && data.session_id === this.currentExecution.session_id) {
                    this.currentExecution = null;
                    this.updateButtonStates(false);
                    localStorage.removeItem('current_pipeline_execution');
                }
            });
            
            this.monitor.socket.on('pipeline_error', (data) => {
                if (data.severity === 'critical') {
                    this.currentExecution = null;
                    this.updateButtonStates(false);
                    localStorage.removeItem('current_pipeline_execution');
                }
            });
        }
    }
}

// Initialize pipeline integration when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.YouTubePipelineUI === 'undefined') {
        window.YouTubePipelineUI = {};
    }
    
    // Initialize after pipeline monitor is ready
    setTimeout(() => {
        window.YouTubePipelineUI.pipelineIntegration = new PipelineIntegration();
        
        // Check for resumed execution
        window.YouTubePipelineUI.pipelineIntegration.checkForResumedExecution();
        window.YouTubePipelineUI.pipelineIntegration.setupPipelineEventListeners();
        
        console.log('🔗 Pipeline Integration initialized');
    }, 1000);
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PipelineIntegration;
}
