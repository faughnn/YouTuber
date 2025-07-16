/**
 * Core JavaScript for YouTube Pipeline UI
 * 
 * This file contains the core JavaScript functionality for the YouTube Pipeline UI,
 * including mobile menu handling, real-time updates, and common utilities.
 * 
 * Created: June 20, 2025
 * Agent: Implementation Agent
 * Task Reference: Phase 1, Task 1.1 - Core Flask Application Setup
 */

// Global application state
window.YouTubePipelineUI = {
    socket: null,
    currentExecution: null,
    systemStatus: 'unknown'
};

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Main application initialization
 */
function initializeApp() {
    console.log('🚀 YouTube Pipeline UI - Initializing...');
    
    // Initialize mobile menu
    initializeMobileMenu();
    
    // Initialize SocketIO connection
    initializeSocketIO();
    
    // Initialize system status monitoring
    initializeSystemStatus();
    
    // Initialize common UI interactions
    initializeUIInteractions();
    
    console.log('✅ YouTube Pipeline UI - Initialization complete');
}

/**
 * Initialize mobile menu functionality
 */
function initializeMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            const isHidden = mobileMenu.classList.contains('hidden');
            
            if (isHidden) {
                mobileMenu.classList.remove('hidden');
                mobileMenuBtn.setAttribute('aria-expanded', 'true');
            } else {
                mobileMenu.classList.add('hidden');
                mobileMenuBtn.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!mobileMenuBtn.contains(event.target) && !mobileMenu.contains(event.target)) {
                mobileMenu.classList.add('hidden');
                mobileMenuBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }
}

/**
 * Initialize SocketIO connection for real-time updates
 */
function initializeSocketIO() {
    if (typeof io !== 'undefined') {
        try {
            window.YouTubePipelineUI.socket = io();
            
            window.YouTubePipelineUI.socket.on('connect', function() {
                console.log('🔌 SocketIO connected');
                updateConnectionStatus(true);
            });
            
            window.YouTubePipelineUI.socket.on('disconnect', function() {
                console.log('🔌 SocketIO disconnected');
                updateConnectionStatus(false);
            });
            
            window.YouTubePipelineUI.socket.on('pipeline_update', function(data) {
                console.log('📊 Pipeline update received:', data);
                handlePipelineUpdate(data);
            });
            
            window.YouTubePipelineUI.socket.on('system_status', function(data) {
                console.log('🖥️ System status update:', data);
                handleSystemStatusUpdate(data);
            });
            
        } catch (error) {
            console.warn('⚠️ SocketIO initialization failed:', error);
        }
    } else {
        console.warn('⚠️ SocketIO not available');
    }
}

/**
 * Initialize system status monitoring
 */
function initializeSystemStatus() {
    const statusBtn = document.getElementById('system-status-btn');
    
    if (statusBtn) {
        statusBtn.addEventListener('click', function() {
            checkSystemStatus();
        });
    }
    
    // Check system status periodically
    setInterval(checkSystemStatus, 30000); // Every 30 seconds
}

/**
 * Initialize common UI interactions
 */
function initializeUIInteractions() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize modals
    initializeModals();
}

/**
 * Check system status via API
 */
function checkSystemStatus() {
    fetch('/api/system-status')
        .then(response => response.json())
        .then(data => {
            window.YouTubePipelineUI.systemStatus = data.status;
            updateSystemStatusUI(data);
        })
        .catch(error => {
            console.error('❌ System status check failed:', error);
            window.YouTubePipelineUI.systemStatus = 'error';
            updateSystemStatusUI({ status: 'error', error: error.message });
        });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusIndicator = document.querySelector('#system-status-btn .rounded-full');
    
    if (statusIndicator) {
        if (connected) {
            statusIndicator.className = 'h-3 w-3 bg-green-400 rounded-full';
        } else {
            statusIndicator.className = 'h-3 w-3 bg-red-400 rounded-full';
        }
    }
}

/**
 * Update system status UI
 */
function updateSystemStatusUI(data) {
    const statusIndicator = document.querySelector('#system-status-btn .rounded-full');
    
    if (statusIndicator) {
        switch (data.status) {
            case 'healthy':
                statusIndicator.className = 'h-3 w-3 bg-green-400 rounded-full';
                break;
            case 'warning':
                statusIndicator.className = 'h-3 w-3 bg-yellow-400 rounded-full';
                break;
            case 'error':
                statusIndicator.className = 'h-3 w-3 bg-red-400 rounded-full';
                break;
            default:
                statusIndicator.className = 'h-3 w-3 bg-gray-400 rounded-full';
        }
    }
}

/**
 * Handle pipeline update events
 */
function handlePipelineUpdate(data) {
    // Update pipeline status in UI
    if (data.execution_id) {
        updatePipelineProgress(data.execution_id, data);
    }
    
    // Show notification if significant update
    if (data.stage_completed || data.error) {
        showNotification(data);
    }
}

/**
 * Handle system status update events
 */
function handleSystemStatusUpdate(data) {
    updateSystemStatusUI(data);
    
    // Show notification for critical status changes
    if (data.status === 'error' || data.status === 'warning') {
        showNotification({
            type: data.status,
            message: data.message || 'System status changed'
        });
    }
}

/**
 * Update pipeline progress UI
 */
function updatePipelineProgress(executionId, data) {
    const progressElements = document.querySelectorAll(`[data-execution-id="${executionId}"]`);
    
    progressElements.forEach(element => {
        if (element.classList.contains('progress-bar-fill')) {
            element.style.width = `${data.progress_percentage || 0}%`;
        }
        
        if (element.classList.contains('stage-status')) {
            updateStageStatus(element, data.current_stage, data.stage_status);
        }
    });
}

/**
 * Update stage status indicators
 */
function updateStageStatus(element, currentStage, stageStatus) {
    const stageNumber = parseInt(element.dataset.stage);
    
    // Remove all status classes
    element.classList.remove('stage-completed', 'stage-processing', 'stage-pending', 'stage-error');
    
    if (stageStatus && stageStatus[stageNumber]) {
        const status = stageStatus[stageNumber];
        element.classList.add(`stage-${status}`);
    } else if (currentStage === stageNumber) {
        element.classList.add('stage-processing');
    } else if (currentStage > stageNumber) {
        element.classList.add('stage-completed');
    } else {
        element.classList.add('stage-pending');
    }
}

/**
 * Show notification to user
 */
function showNotification(data) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 max-w-sm bg-white shadow-lg rounded-lg p-4 border-l-4 ${
        data.type === 'error' ? 'border-red-500' : 
        data.type === 'warning' ? 'border-yellow-500' : 
        'border-green-500'
    } fade-in`;
    
    notification.innerHTML = `
        <div class="flex">
            <div class="flex-shrink-0">
                <svg class="h-5 w-5 ${
                    data.type === 'error' ? 'text-red-400' : 
                    data.type === 'warning' ? 'text-yellow-400' : 
                    'text-green-400'
                }" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium text-gray-900">${data.message || 'Update received'}</p>
                ${data.details ? `<p class="text-sm text-gray-500">${data.details}</p>` : ''}
            </div>
            <div class="ml-auto pl-3">
                <button class="inline-flex rounded-md p-1.5 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500" onclick="this.parentElement.parentElement.parentElement.remove()">
                    <span class="sr-only">Dismiss</span>
                    <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    // Simple tooltip implementation
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

/**
 * Show tooltip
 */
function showTooltip(event) {
    const element = event.target;
    const tooltipText = element.getAttribute('data-tooltip');
    
    if (!tooltipText) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'absolute z-50 px-2 py-1 text-sm bg-gray-900 text-white rounded shadow-lg';
    tooltip.textContent = tooltipText;
    tooltip.id = 'tooltip';
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
    tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(form)) {
                event.preventDefault();
            }
        });
    });
}

/**
 * Validate form
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorElement = document.createElement('p');
    errorElement.className = 'mt-1 text-sm text-red-600';
    errorElement.textContent = message;
    errorElement.setAttribute('data-field-error', field.name || 'field');
    
    field.parentNode.appendChild(errorElement);
    field.classList.add('border-red-300', 'focus:border-red-500', 'focus:ring-red-500');
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    const errorElement = field.parentNode.querySelector(`[data-field-error="${field.name || 'field'}"]`);
    if (errorElement) {
        errorElement.remove();
    }
    
    field.classList.remove('border-red-300', 'focus:border-red-500', 'focus:ring-red-500');
}

/**
 * Initialize modals
 */
function initializeModals() {
    // Simple modal implementation
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal-target');
            const modal = document.getElementById(modalId);
            
            if (modal) {
                showModal(modal);
            }
        });
    });
    
    // Close modal when clicking outside or on close button
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal-backdrop') || 
            event.target.classList.contains('modal-close')) {
            const modal = event.target.closest('.modal');
            if (modal) {
                hideModal(modal);
            }
        }
    });
}

/**
 * Show modal
 */
function showModal(modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.classList.add('overflow-hidden');
}

/**
 * Hide modal
 */
function hideModal(modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    document.body.classList.remove('overflow-hidden');
}

/**
 * Utility function to format file sizes
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Utility function to format duration
 */
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

// Export utilities for use in other scripts
window.YouTubePipelineUI.utils = {
    formatFileSize,
    formatDuration,
    showNotification,
    checkSystemStatus
};
