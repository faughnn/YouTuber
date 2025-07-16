/**
 * UI Enhancements and Polish JavaScript
 * 
 * Enhanced user interface interactions, accessibility features, help system,
 * and performance optimizations for the YouTube Pipeline UI.
 * 
 * Created: June 20, 2025
 * Agent: Agent_Polish_Testing
 * Task Reference: Phase 6, Task 6.1 - UI Polish & Responsive Design
 */

class UIEnhancements {
    constructor() {
        this.preferences = this.loadUserPreferences();
        this.helpSystem = null;
        this.toastContainer = null;
        this.keyboardShortcuts = new Map();
        
        this.init();
    }
      init() {
        this.setupEventListeners();
        this.initializeHelpSystem();
        this.initializeToastSystem();
        this.setupKeyboardShortcuts();
        this.initializeAccessibilityFeatures();
        this.setupThemeToggle();
        this.setupMobileMenuEnhancements();
        this.initializeLoadingStates();
        this.setupFormEnhancements();
        this.initializeProgressBars();
        
        console.log('🎨 UI Enhancements initialized');
    }
    
    /* ========================================
       EVENT LISTENERS SETUP
       ======================================== */
    
    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.enhanceFlashMessages();
            this.setupSystemStatusIndicator();
            this.initializeTooltips();
        });
        
        // Handle resize events for responsive adjustments
        window.addEventListener('resize', this.debounce(() => {
            this.handleResize();
        }, 250));
        
        // Handle visibility change for performance optimization
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
    }
    
    /* ========================================
       HELP SYSTEM
       ======================================== */
    
    initializeHelpSystem() {
        const helpBtn = document.getElementById('help-btn');
        const mobileHelpBtn = document.getElementById('mobile-help-btn');
        const helpModal = document.getElementById('help-modal');
        const helpModalClose = document.getElementById('help-modal-close');
        const helpModalOk = document.getElementById('help-modal-ok');
        
        if (helpBtn) {
            helpBtn.addEventListener('click', () => this.showHelp());
        }
        
        if (mobileHelpBtn) {
            mobileHelpBtn.addEventListener('click', () => this.showHelp());
        }
        
        if (helpModalClose) {
            helpModalClose.addEventListener('click', () => this.hideHelp());
        }
        
        if (helpModalOk) {
            helpModalOk.addEventListener('click', () => this.hideHelp());
        }
        
        // Close modal when clicking outside
        if (helpModal) {
            helpModal.addEventListener('click', (e) => {
                if (e.target === helpModal) {
                    this.hideHelp();
                }
            });
        }
    }
    
    showHelp() {
        const helpModal = document.getElementById('help-modal');
        if (helpModal) {
            helpModal.classList.remove('hidden');
            helpModal.setAttribute('aria-hidden', 'false');
            
            // Focus the close button for accessibility
            const closeBtn = document.getElementById('help-modal-close');
            if (closeBtn) {
                setTimeout(() => closeBtn.focus(), 100);
            }
            
            // Prevent body scrolling
            document.body.style.overflow = 'hidden';
        }
    }
    
    hideHelp() {
        const helpModal = document.getElementById('help-modal');
        if (helpModal) {
            helpModal.classList.add('hidden');
            helpModal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
            
            // Return focus to help button
            const helpBtn = document.getElementById('help-btn');
            if (helpBtn) {
                helpBtn.focus();
            }
        }
    }
    
    /* ========================================
       TOAST NOTIFICATION SYSTEM
       ======================================== */
    
    initializeToastSystem() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            container.setAttribute('aria-live', 'polite');
            container.setAttribute('aria-atomic', 'true');
            document.body.appendChild(container);
        }
        
        this.toastContainer = document.getElementById('toast-container');
    }
    
    showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} animate-fade-in`;
        toast.setAttribute('role', 'alert');
        
        const icon = this.getToastIcon(type);
        
        toast.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    ${icon}
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium text-gray-900">${message}</p>
                </div>
                <div class="ml-auto pl-3">
                    <button class="toast-close inline-flex rounded-md p-1.5 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500">
                        <span class="sr-only">Dismiss</span>
                        <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        
        // Add close functionality
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));
        
        this.toastContainer.appendChild(toast);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => this.removeToast(toast), duration);
        }
        
        return toast;
    }
    
    removeToast(toast) {
        toast.classList.add('toast-exit');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
    
    getToastIcon(type) {
        const icons = {
            success: `<svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                      </svg>`,
            error: `<svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>`,
            warning: `<svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                      </svg>`,
            info: `<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                     <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                   </svg>`
        };
        
        return icons[type] || icons.info;
    }
    
    /* ========================================
       KEYBOARD SHORTCUTS
       ======================================== */
    
    setupKeyboardShortcuts() {
        // Register keyboard shortcuts
        this.keyboardShortcuts.set('?', () => this.showHelp());
        this.keyboardShortcuts.set('Escape', () => this.hideHelp());
        this.keyboardShortcuts.set('ctrl+shift+t', () => this.toggleTheme());
        this.keyboardShortcuts.set('ctrl+k', (e) => {
            e.preventDefault();
            this.focusSearch();
        });
        
        document.addEventListener('keydown', (e) => {
            const key = this.getKeyboardShortcut(e);
            const handler = this.keyboardShortcuts.get(key);
            
            if (handler) {
                e.preventDefault();
                handler(e);
            }
        });
    }
    
    getKeyboardShortcut(event) {
        const parts = [];
        
        if (event.ctrlKey) parts.push('ctrl');
        if (event.shiftKey) parts.push('shift');
        if (event.altKey) parts.push('alt');
        if (event.metaKey) parts.push('meta');
        
        parts.push(event.key.toLowerCase());
        
        return parts.join('+');
    }
    
    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
        if (searchInput) {
            searchInput.focus();
            this.showToast('Search focused. Press Ctrl+K again to focus.', 'info', 2000);
        }
    }
    
    /* ========================================
       ACCESSIBILITY FEATURES
       ======================================== */
    
    initializeAccessibilityFeatures() {
        // Add aria-labels to buttons without text
        this.enhanceAccessibilityLabels();
        
        // Setup focus management
        this.setupFocusManagement();
        
        // Add screen reader announcements
        this.setupScreenReaderAnnouncements();
        
        // Enhance form accessibility
        this.enhanceFormAccessibility();
    }
    
    enhanceAccessibilityLabels() {
        // Add missing aria-labels
        const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        buttons.forEach(button => {
            const text = button.textContent.trim();
            const icon = button.querySelector('svg');
            
            if (!text && icon) {
                // Button has only icon, needs aria-label
                const title = button.getAttribute('title');
                if (title) {
                    button.setAttribute('aria-label', title);
                }
            }
        });
    }
    
    setupFocusManagement() {
        // Ensure proper focus indicators
        const focusableElements = document.querySelectorAll(
            'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
        );
        
        focusableElements.forEach(element => {
            if (!element.classList.contains('focus-ring')) {
                element.classList.add('focus-ring');
            }
        });
    }
    
    setupScreenReaderAnnouncements() {
        // Create live region for announcements
        if (!document.getElementById('sr-announcements')) {
            const announcements = document.createElement('div');
            announcements.id = 'sr-announcements';
            announcements.setAttribute('aria-live', 'polite');
            announcements.setAttribute('aria-atomic', 'true');
            announcements.className = 'sr-only';
            document.body.appendChild(announcements);
        }
    }
    
    announceToScreenReader(message) {
        const announcements = document.getElementById('sr-announcements');
        if (announcements) {
            announcements.textContent = message;
            
            // Clear after a delay to allow for new announcements
            setTimeout(() => {
                announcements.textContent = '';
            }, 1000);
        }
    }
    
    enhanceFormAccessibility() {
        // Add form validation feedback
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('invalid', (e) => {
                const message = e.target.validationMessage;
                this.announceToScreenReader(`Validation error: ${message}`);
            });
        });
    }
    
    /* ========================================
       THEME TOGGLE
       ======================================== */
    
    setupThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        const mobileThemeToggle = document.getElementById('mobile-theme-toggle');
        
        // Set initial theme
        this.applyTheme(this.preferences.theme || 'light');
        
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        if (mobileThemeToggle) {
            mobileThemeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }
    
    toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        this.applyTheme(newTheme);
        this.saveUserPreference('theme', newTheme);
        
        this.showToast(`Switched to ${newTheme} theme`, 'info', 2000);
        this.announceToScreenReader(`Theme changed to ${newTheme} mode`);
    }
    
    applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        
        // Update theme toggle icons
        const toggles = document.querySelectorAll('#theme-toggle svg, #mobile-theme-toggle svg');
        toggles.forEach(icon => {
            if (theme === 'dark') {
                icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />';
            } else {
                icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />';
            }
        });
    }
    
    /* ========================================
       MOBILE MENU ENHANCEMENTS
       ======================================== */
    
    setupMobileMenuEnhancements() {
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        const mobileMenu = document.getElementById('mobile-menu');
        
        if (mobileMenuBtn && mobileMenu) {
            mobileMenuBtn.addEventListener('click', () => {
                const isOpen = mobileMenu.classList.contains('hidden');
                
                if (isOpen) {
                    this.openMobileMenu();
                } else {
                    this.closeMobileMenu();
                }
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!mobileMenuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
                    this.closeMobileMenu();
                }
            });
        }
    }
    
    openMobileMenu() {
        const mobileMenu = document.getElementById('mobile-menu');
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        
        if (mobileMenu && mobileMenuBtn) {
            mobileMenu.classList.remove('hidden');
            mobileMenu.classList.add('slide-in-left');
            mobileMenuBtn.setAttribute('aria-expanded', 'true');
            
            // Switch button icons
            const icons = mobileMenuBtn.querySelectorAll('svg');
            icons[0].classList.add('hidden');
            icons[1].classList.remove('hidden');
        }
    }
    
    closeMobileMenu() {
        const mobileMenu = document.getElementById('mobile-menu');
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        
        if (mobileMenu && mobileMenuBtn) {
            mobileMenu.classList.add('hidden');
            mobileMenu.classList.remove('slide-in-left');
            mobileMenuBtn.setAttribute('aria-expanded', 'false');
            
            // Switch button icons
            const icons = mobileMenuBtn.querySelectorAll('svg');
            icons[0].classList.remove('hidden');
            icons[1].classList.add('hidden');
        }
    }
    
    /* ========================================
       LOADING STATES
       ======================================== */
    
    initializeLoadingStates() {
        // Enhance form submissions with loading states
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.showFormLoading(form);
            });
        });
    }
    
    showFormLoading(form) {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            submitBtn.classList.add('btn-loading');
            submitBtn.disabled = true;
            
            const originalText = submitBtn.textContent;
            submitBtn.setAttribute('data-original-text', originalText);
            submitBtn.textContent = 'Processing...';
        }
    }
    
    hideFormLoading(form) {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            submitBtn.classList.remove('btn-loading');
            submitBtn.disabled = false;
            
            const originalText = submitBtn.getAttribute('data-original-text');
            if (originalText) {
                submitBtn.textContent = originalText;
            }
        }
    }
    
    showGlobalLoading(message = 'Processing...') {
        const loadingOverlay = document.getElementById('global-loading');
        if (loadingOverlay) {
            const messageElement = loadingOverlay.querySelector('span');
            if (messageElement) {
                messageElement.textContent = message;
            }
            loadingOverlay.classList.remove('hidden');
        }
    }
    
    hideGlobalLoading() {
        const loadingOverlay = document.getElementById('global-loading');
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }
    }
    
    /* ========================================
       FORM ENHANCEMENTS
       ======================================== */
    
    setupFormEnhancements() {
        // Add real-time validation feedback
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateInput(input));
            input.addEventListener('input', () => this.clearValidationError(input));
        });
    }
    
    validateInput(input) {
        if (input.checkValidity()) {
            this.clearValidationError(input);
        } else {
            this.showValidationError(input, input.validationMessage);
        }
    }
    
    showValidationError(input, message) {
        input.classList.add('error');
        
        // Remove existing error message
        const existingError = input.parentNode.querySelector('.validation-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Add new error message
        const errorElement = document.createElement('div');
        errorElement.className = 'validation-error text-sm text-red-600 mt-1';
        errorElement.textContent = message;
        input.parentNode.appendChild(errorElement);
    }
    
    clearValidationError(input) {
        input.classList.remove('error');
        
        const errorElement = input.parentNode.querySelector('.validation-error');
        if (errorElement) {
            errorElement.remove();
        }
    }
    
    /* ========================================
       SYSTEM STATUS INDICATOR
       ======================================== */
    
    setupSystemStatusIndicator() {
        const statusBtn = document.getElementById('system-status-btn');
        const statusTooltip = document.getElementById('status-tooltip');
        const statusIndicator = document.getElementById('status-indicator');
        
        if (statusBtn && statusTooltip) {
            statusBtn.addEventListener('mouseenter', () => {
                statusTooltip.classList.remove('hidden');
            });
            
            statusBtn.addEventListener('mouseleave', () => {
                statusTooltip.classList.add('hidden');
            });
            
            statusBtn.addEventListener('click', () => {
                this.updateSystemStatus();
            });
        }
        
        // Update status periodically
        this.updateSystemStatus();
        setInterval(() => this.updateSystemStatus(), 30000);
    }
    
    updateSystemStatus() {
        // Simulate system status check
        const statuses = ['online', 'processing', 'warning', 'error'];
        const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
        
        this.setSystemStatus(randomStatus);
    }
    
    setSystemStatus(status) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusDetails = document.getElementById('status-details');
        const connectionStatus = document.getElementById('connection-status');
        
        if (statusIndicator) {
            statusIndicator.className = 'h-3 w-3 rounded-full';
            
            switch (status) {
                case 'online':
                    statusIndicator.classList.add('bg-green-400');
                    if (statusDetails) statusDetails.textContent = 'All systems operational';
                    if (connectionStatus) connectionStatus.textContent = 'Connected';
                    break;
                case 'processing':
                    statusIndicator.classList.add('bg-yellow-400', 'animate-pulse');
                    if (statusDetails) statusDetails.textContent = 'Pipeline processing active';
                    if (connectionStatus) connectionStatus.textContent = 'Processing';
                    break;
                case 'warning':
                    statusIndicator.classList.add('bg-orange-400');
                    if (statusDetails) statusDetails.textContent = 'System performance degraded';
                    if (connectionStatus) connectionStatus.textContent = 'Warning';
                    break;
                case 'error':
                    statusIndicator.classList.add('bg-red-400');
                    if (statusDetails) statusDetails.textContent = 'System errors detected';
                    if (connectionStatus) connectionStatus.textContent = 'Error';
                    break;
            }
        }
    }
    
    /* ========================================
       ENHANCED FLASH MESSAGES
       ======================================== */
    
    enhanceFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            const closeBtn = message.querySelector('.flash-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    message.style.animation = 'toastSlideOut 0.3s ease-in forwards';
                    setTimeout(() => {
                        if (message.parentNode) {
                            message.parentNode.removeChild(message);
                        }
                    }, 300);
                });
            }
            
            // Auto-remove after 8 seconds
            setTimeout(() => {
                if (message.parentNode) {
                    message.style.animation = 'toastSlideOut 0.3s ease-in forwards';
                    setTimeout(() => {
                        if (message.parentNode) {
                            message.parentNode.removeChild(message);
                        }
                    }, 300);
                }
            }, 8000);
        });
    }
    
    /* ========================================
       TOOLTIPS
       ======================================== */
    
    initializeTooltips() {
        const elementsWithTooltips = document.querySelectorAll('[title]');
        elementsWithTooltips.forEach(element => {
            this.setupTooltip(element);
        });
    }
    
    setupTooltip(element) {
        const title = element.getAttribute('title');
        if (!title) return;
        
        // Remove default title to prevent browser tooltip
        element.removeAttribute('title');
        element.setAttribute('data-tooltip', title);
        
        let tooltip = null;
        
        element.addEventListener('mouseenter', () => {
            tooltip = this.createTooltip(title);
            document.body.appendChild(tooltip);
            this.positionTooltip(tooltip, element);
        });
        
        element.addEventListener('mouseleave', () => {
            if (tooltip) {
                tooltip.remove();
                tooltip = null;
            }
        });
    }
    
    createTooltip(text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'absolute bg-gray-900 text-white text-xs rounded py-1 px-2 z-50 pointer-events-none';
        tooltip.textContent = text;
        return tooltip;
    }
    
    positionTooltip(tooltip, element) {
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltipRect.width / 2}px`;
        tooltip.style.top = `${rect.top - tooltipRect.height - 5}px`;
    }
    
    /* ========================================
       UTILITY FUNCTIONS
       ======================================== */
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    handleResize() {
        // Responsive adjustments
        const width = window.innerWidth;
        
        if (width < 768) {
            // Mobile optimizations
            this.closeMobileMenu();
        }
        
        // Update any size-dependent calculations
        this.announceToScreenReader(`Screen size changed to ${width} pixels wide`);
    }
    
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is now hidden, reduce activity
            console.log('🔇 Page hidden, reducing activity');
        } else {
            // Page is now visible, resume activity
            console.log('🔊 Page visible, resuming activity');
            this.updateSystemStatus();
        }
    }
    
    /* ========================================
       USER PREFERENCES
       ======================================== */
    
    loadUserPreferences() {
        const defaultPrefs = {
            theme: 'light',
            reducedMotion: false,
            highContrast: false,
            fontSize: 'normal',
            autoSave: true
        };
        
        try {
            const stored = localStorage.getItem('yt-pipeline-preferences');
            return stored ? { ...defaultPrefs, ...JSON.parse(stored) } : defaultPrefs;
        } catch (error) {
            console.warn('Failed to load user preferences:', error);
            return defaultPrefs;
        }
    }
    
    saveUserPreference(key, value) {
        this.preferences[key] = value;
        
        try {
            localStorage.setItem('yt-pipeline-preferences', JSON.stringify(this.preferences));
        } catch (error) {
            console.warn('Failed to save user preference:', error);
        }
    }
    
    saveAllPreferences() {
        try {
            localStorage.setItem('yt-pipeline-preferences', JSON.stringify(this.preferences));
            this.showToast('Preferences saved successfully', 'success', 3000);
        } catch (error) {
            console.error('Failed to save preferences:', error);            this.showToast('Failed to save preferences', 'error', 5000);
        }
    }
    
    /* ========================================
       PROGRESS BAR INITIALIZATION
       ======================================== */
    
    initializeProgressBars() {
        // Initialize episode progress bars
        const progressBars = document.querySelectorAll('[data-progress]');
        
        progressBars.forEach(bar => {
            const progress = parseFloat(bar.getAttribute('data-progress')) || 0;
            
            // Set CSS custom property for dynamic width
            bar.style.setProperty('--progress', progress);
            
            // Animate progress bar on load
            setTimeout(() => {
                bar.style.width = `${progress}%`;
                bar.classList.add('initialized');
            }, 100);
            
            // Add accessibility attributes
            bar.setAttribute('role', 'progressbar');
            bar.setAttribute('aria-valuenow', progress);
            bar.setAttribute('aria-valuemin', '0');
            bar.setAttribute('aria-valuemax', '100');
            
            if (!bar.hasAttribute('aria-label')) {
                bar.setAttribute('aria-label', `Progress: ${progress}% complete`);
            }
        });
        
        // Initialize modal progress bars (for processing modals)
        this.initializeModalProgressBars();
    }
    
    initializeModalProgressBars() {
        // Handle progress bars in modals and dynamic content
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const progressBars = node.querySelectorAll ? 
                            node.querySelectorAll('[data-progress]') : [];
                        
                        progressBars.forEach(bar => {
                            if (!bar.classList.contains('initialized')) {
                                const progress = parseFloat(bar.getAttribute('data-progress')) || 0;
                                bar.style.width = `${progress}%`;
                                bar.classList.add('initialized');
                            }
                        });
                    }                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// Initialize UI Enhancements when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.YouTubePipelineUI = window.YouTubePipelineUI || {};
    window.YouTubePipelineUI.uiEnhancements = new UIEnhancements();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIEnhancements;
}
