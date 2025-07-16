/**
 * Main Dashboard Coordination JavaScript
 * 
 * Central coordination for all UI components with real-time status updates,
 * episode management, preset functionality, and overall application state management.
 * 
 * Created: June 20, 2025
 * Agent: Implementation Agent
 * Task Reference: Phase 4, Task 4.2 - JavaScript Client Implementation
 */

class MainDashboard {
    constructor() {
        this.socket = null;
        this.currentEpisode = null;
        this.episodes = [];
        this.presets = [];
        this.systemStatus = 'unknown';
        this.connectionStatus = 'disconnected';
        
        // Component references
        this.pipelineController = null;
        this.segmentManager = null;
        this.logHandler = null;
        
        // UI elements
        this.episodeSelect = null;
        this.presetSelect = null;
        this.statusIndicator = null;
        this.refreshButton = null;
        this.notificationContainer = null;
        this.dashboardStats = null;
        
        // State management
        this.appState = {
            currentPage: 'dashboard',
            selectedEpisode: null,
            selectedPreset: null,
            pipelineState: 'idle',
            lastUpdate: null
        };
        
        // Configuration
        this.config = {
            refreshInterval: 30000, // 30 seconds
            maxNotifications: 5,
            autoSaveInterval: 60000 // 1 minute
        };
        
        this.initialize();
    }
    
    /**
     * Initialize main dashboard
     */
    initialize() {
        this.initializeUI();
        this.initializeSocketIO();
        this.setupEventListeners();
        this.loadInitialData();
        this.startPeriodicUpdates();
        
        console.log('🏠 Main Dashboard initialized');
    }
    
    /**
     * Initialize UI elements
     */
    initializeUI() {
        // Find main UI elements
        this.episodeSelect = document.getElementById('episode-select');
        this.presetSelect = document.getElementById('preset-select');
        this.statusIndicator = document.getElementById('system-status');
        this.refreshButton = document.getElementById('refresh-data');
        this.dashboardStats = document.getElementById('dashboard-stats');
        
        // Create notification container
        this.notificationContainer = document.getElementById('notifications') || 
                                   this.createNotificationContainer();
        
        // Initialize dashboard stats if not present
        if (!this.dashboardStats) {
            this.dashboardStats = this.createDashboardStats();
        }
        
        // Update initial UI state
        this.updateSystemStatus();
        this.updateConnectionStatus();
        
        console.log('🖥️ Dashboard UI elements initialized');
    }
    
    /**
     * Create notification container
     */
    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notifications';
        container.className = 'fixed top-4 right-4 z-50 space-y-3 max-w-sm';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-label', 'Notifications');
        
        document.body.appendChild(container);
        return container;
    }
    
    /**
     * Create dashboard stats section
     */
    createDashboardStats() {
        const stats = document.createElement('div');
        stats.id = 'dashboard-stats';
        stats.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8';
        stats.innerHTML = `
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <span class="text-blue-600 font-semibold">📊</span>
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">Total Episodes</dt>
                            <dd id="stat-total-episodes" class="text-lg font-medium text-gray-900">-</dd>
                        </dl>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                            <span class="text-green-600 font-semibold">✅</span>
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">Processed</dt>
                            <dd id="stat-processed-episodes" class="text-lg font-medium text-gray-900">-</dd>
                        </dl>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                            <span class="text-yellow-600 font-semibold">⏳</span>
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">In Progress</dt>
                            <dd id="stat-processing-episodes" class="text-lg font-medium text-gray-900">-</dd>
                        </dl>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                            <span class="text-purple-600 font-semibold">🎬</span>
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">Total Segments</dt>
                            <dd id="stat-total-segments" class="text-lg font-medium text-gray-900">-</dd>
                        </dl>
                    </div>
                </div>
            </div>
        `;
        
        // Insert stats at the beginning of main content
        const main = document.querySelector('main');
        if (main && main.firstChild) {
            main.insertBefore(stats, main.firstChild);
        }
        
        return stats;
    }
    
    /**
     * Initialize SocketIO connection
     */
    initializeSocketIO() {
        if (typeof io === 'undefined') {
            console.warn('⚠️ SocketIO not available');
            return;
        }
        
        this.socket = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 10000
        });
        
        this.setupSocketEventHandlers();
    }
    
    /**
     * Setup SocketIO event handlers
     */
    setupSocketEventHandlers() {
        this.socket.on('connect', () => {
            this.connectionStatus = 'connected';
            this.updateConnectionStatus();
            this.showNotification('Connected to server', 'success');
            console.log('🔗 Dashboard connected to server');
        });
        
        this.socket.on('disconnect', () => {
            this.connectionStatus = 'disconnected';
            this.updateConnectionStatus();
            this.showNotification('Disconnected from server', 'warning');
            console.log('❌ Dashboard disconnected from server');
        });
        
        this.socket.on('system_status', (data) => {
            this.handleSystemStatusUpdate(data);
        });
        
        this.socket.on('episode_update', (data) => {
            this.handleEpisodeUpdate(data);
        });
        
        this.socket.on('pipeline_progress', (data) => {
            this.handlePipelineProgress(data);
        });
        
        this.socket.on('pipeline_completion', (data) => {
            this.handlePipelineCompletion(data);
        });
        
        this.socket.on('stats_update', (data) => {
            this.handleStatsUpdate(data);
        });
        
        this.socket.on('notification', (data) => {
            this.showNotification(data.message, data.type || 'info');
        });
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Episode selection
        if (this.episodeSelect) {
            this.episodeSelect.addEventListener('change', (e) => {
                this.handleEpisodeSelection(e.target.value);
            });
        }
        
        // Preset selection
        if (this.presetSelect) {
            this.presetSelect.addEventListener('change', (e) => {
                this.handlePresetSelection(e.target.value);
            });
        }
        
        // Refresh button
        if (this.refreshButton) {
            this.refreshButton.addEventListener('click', () => {
                this.refreshAllData();
            });
        }
        
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.handlePageVisible();
            }
        });
        
        // Window beforeunload (save state)
        window.addEventListener('beforeunload', () => {
            this.saveAppState();
        });
        
        // Storage events (for multi-tab coordination)
        window.addEventListener('storage', (e) => {
            this.handleStorageChange(e);
        });
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeyboard(e);
        });
        
        console.log('🎯 Dashboard event listeners setup');
    }
    
    /**
     * Load initial data
     */
    async loadInitialData() {
        try {
            // Load episodes
            await this.loadEpisodes();
            
            // Load presets
            await this.loadPresets();
            
            // Load system status
            await this.loadSystemStatus();
            
            // Load dashboard stats
            await this.loadDashboardStats();
            
            // Restore app state
            this.restoreAppState();
            
            console.log('📊 Initial dashboard data loaded');
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }
    
    /**
     * Load episodes from API
     */
    async loadEpisodes() {
        try {
            const response = await fetch('/api/episodes');
            const data = await response.json();
            
            if (data.success) {
                this.episodes = data.episodes || [];
                this.updateEpisodeSelect();
            } else {
                throw new Error(data.error || 'Failed to load episodes');
            }
            
        } catch (error) {
            console.error('Error loading episodes:', error);
            this.showNotification('Failed to load episodes', 'error');
        }
    }
    
    /**
     * Load presets from API
     */
    async loadPresets() {
        try {
            const response = await fetch('/api/presets');
            const data = await response.json();
            
            if (data.success) {
                this.presets = data.presets || [];
                this.updatePresetSelect();
            } else {
                throw new Error(data.error || 'Failed to load presets');
            }
            
        } catch (error) {
            console.error('Error loading presets:', error);
            this.showNotification('Failed to load presets', 'error');
        }
    }
    
    /**
     * Load system status
     */
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                this.systemStatus = data.status;
                this.updateSystemStatus();
            }
            
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }
    
    /**
     * Load dashboard statistics
     */
    async loadDashboardStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.success) {
                this.updateDashboardStats(data.stats);
            }
            
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
    }
    
    /**
     * Update episode select dropdown
     */
    updateEpisodeSelect() {
        if (!this.episodeSelect) return;
        
        // Clear existing options except the default
        const defaultOption = this.episodeSelect.querySelector('option[value=""]');
        this.episodeSelect.innerHTML = '';
        if (defaultOption) {
            this.episodeSelect.appendChild(defaultOption);
        } else {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Select an episode...';
            this.episodeSelect.appendChild(option);
        }
        
        // Add episode options
        this.episodes.forEach(episode => {
            const option = document.createElement('option');
            option.value = episode.id || episode.path;
            option.textContent = episode.title || episode.filename || 'Untitled Episode';
            
            // Add status indicator
            if (episode.status) {
                option.textContent += ` (${episode.status})`;
            }
            
            this.episodeSelect.appendChild(option);
        });
        
        console.log(`📊 Updated episode select with ${this.episodes.length} episodes`);
    }
    
    /**
     * Update preset select dropdown
     */
    updatePresetSelect() {
        if (!this.presetSelect) return;
        
        // Clear existing options except the default
        const defaultOption = this.presetSelect.querySelector('option[value=""]');
        this.presetSelect.innerHTML = '';
        if (defaultOption) {
            this.presetSelect.appendChild(defaultOption);
        } else {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No preset (custom)';
            this.presetSelect.appendChild(option);
        }
        
        // Add preset options
        this.presets.forEach(preset => {
            const option = document.createElement('option');
            option.value = preset.id || preset.name;
            option.textContent = preset.name || 'Untitled Preset';
            
            if (preset.description) {
                option.title = preset.description;
            }
            
            this.presetSelect.appendChild(option);
        });
        
        console.log(`📊 Updated preset select with ${this.presets.length} presets`);
    }
    
    /**
     * Update system status indicator
     */
    updateSystemStatus() {
        if (!this.statusIndicator) return;
        
        const statusText = this.formatStatus(this.systemStatus);
        const statusClass = this.getStatusClass(this.systemStatus);
        
        this.statusIndicator.textContent = statusText;
        this.statusIndicator.className = this.statusIndicator.className.replace(/(bg-\w+-\d+)|(text-\w+-\d+)/g, '');
        this.statusIndicator.classList.add(...statusClass.split(' '));
    }
    
    /**
     * Update connection status
     */
    updateConnectionStatus() {
        const indicators = document.querySelectorAll('.connection-indicator');
        indicators.forEach(indicator => {
            if (this.connectionStatus === 'connected') {
                indicator.classList.remove('text-red-500', 'bg-red-100');
                indicator.classList.add('text-green-500', 'bg-green-100');
                indicator.textContent = 'Connected';
            } else {
                indicator.classList.remove('text-green-500', 'bg-green-100');
                indicator.classList.add('text-red-500', 'bg-red-100');
                indicator.textContent = 'Disconnected';
            }
        });
    }
    
    /**
     * Update dashboard statistics
     */
    updateDashboardStats(stats) {
        if (!stats) return;
        
        const elements = {
            'stat-total-episodes': stats.total_episodes || 0,
            'stat-processed-episodes': stats.processed_episodes || 0,
            'stat-processing-episodes': stats.processing_episodes || 0,
            'stat-total-segments': stats.total_segments || 0
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value.toLocaleString();
            }
        });
    }
    
    /**
     * Handle episode selection
     */
    async handleEpisodeSelection(episodeId) {
        if (!episodeId) {
            this.currentEpisode = null;
            this.appState.selectedEpisode = null;
            return;
        }
        
        try {
            // Find episode data
            const episode = this.episodes.find(e => (e.id || e.path) === episodeId);
            if (!episode) {
                throw new Error('Episode not found');
            }
            
            this.currentEpisode = episode;
            this.appState.selectedEpisode = episodeId;
            
            // Update URL if on episodes page
            if (window.location.pathname.includes('/episodes')) {
                const url = new URL(window.location);
                url.searchParams.set('episode', episodeId);
                window.history.replaceState({}, '', url);
            }
            
            // Notify other components
            this.notifyEpisodeSelection(episode);
            
            // Save state
            this.saveAppState();
            
            this.showNotification(`Selected: ${episode.title || 'Episode'}`, 'info');
            
        } catch (error) {
            console.error('Error selecting episode:', error);
            this.showNotification('Failed to select episode', 'error');
        }
    }
    
    /**
     * Handle preset selection
     */
    async handlePresetSelection(presetId) {
        if (!presetId) {
            this.appState.selectedPreset = null;
            return;
        }
        
        try {
            // Find preset data
            const preset = this.presets.find(p => (p.id || p.name) === presetId);
            if (!preset) {
                throw new Error('Preset not found');
            }
            
            this.appState.selectedPreset = presetId;
            
            // Apply preset to form if available
            await this.applyPreset(preset);
            
            // Save state
            this.saveAppState();
            
            this.showNotification(`Applied preset: ${preset.name}`, 'success');
            
        } catch (error) {
            console.error('Error applying preset:', error);
            this.showNotification('Failed to apply preset', 'error');
        }
    }
    
    /**
     * Apply preset configuration
     */
    async applyPreset(preset) {
        if (!preset.config) return;
        
        try {
            // Apply to pipeline form if available
            const pipelineForm = document.getElementById('pipeline-form');
            if (pipelineForm && preset.config.stages) {
                // Update stage selections
                preset.config.stages.forEach(stage => {
                    const checkbox = pipelineForm.querySelector(`input[value="${stage}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
            }
            
            // Apply other configuration options
            if (preset.config.settings) {
                Object.entries(preset.config.settings).forEach(([key, value]) => {
                    const input = document.querySelector(`[name="${key}"]`);
                    if (input) {
                        if (input.type === 'checkbox') {
                            input.checked = value;
                        } else {
                            input.value = value;
                        }
                    }
                });
            }
            
        } catch (error) {
            console.error('Error applying preset config:', error);
            throw error;
        }
    }
    
    /**
     * Refresh all data
     */
    async refreshAllData() {
        if (this.refreshButton) {
            this.refreshButton.disabled = true;
            this.refreshButton.textContent = 'Refreshing...';
        }
        
        try {
            await Promise.all([
                this.loadEpisodes(),
                this.loadPresets(),
                this.loadSystemStatus(),
                this.loadDashboardStats()
            ]);
            
            this.showNotification('Dashboard data refreshed', 'success');
            
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showNotification('Failed to refresh data', 'error');
        } finally {
            if (this.refreshButton) {
                this.refreshButton.disabled = false;
                this.refreshButton.textContent = 'Refresh';
            }
        }
    }
    
    /**
     * Handle SocketIO events
     */
    handleSystemStatusUpdate(data) {
        this.systemStatus = data.status;
        this.updateSystemStatus();
    }
    
    handleEpisodeUpdate(data) {
        // Update episode in local array
        const index = this.episodes.findIndex(e => (e.id || e.path) === data.episode.id);
        if (index !== -1) {
            this.episodes[index] = { ...this.episodes[index], ...data.episode };
        } else {
            this.episodes.push(data.episode);
        }
        
        this.updateEpisodeSelect();
        
        // Notify components if this is the current episode
        if (this.currentEpisode && (this.currentEpisode.id || this.currentEpisode.path) === data.episode.id) {
            this.notifyEpisodeUpdate(data.episode);
        }
    }
    
    handlePipelineProgress(data) {
        this.appState.pipelineState = 'running';
        this.appState.lastUpdate = new Date().toISOString();
        
        // Update episode status if it matches current episode
        if (this.currentEpisode && data.episode_path === this.currentEpisode.path) {
            this.currentEpisode.status = 'processing';
            this.currentEpisode.progress = data.progress;
        }
    }
    
    handlePipelineCompletion(data) {
        this.appState.pipelineState = 'completed';
        this.appState.lastUpdate = new Date().toISOString();
        
        // Update episode status
        if (this.currentEpisode && data.episode_path === this.currentEpisode.path) {
            this.currentEpisode.status = 'completed';
            this.currentEpisode.progress = 100;
        }
        
        // Refresh stats
        this.loadDashboardStats();
        
        this.showNotification('Pipeline completed successfully!', 'success');
    }
    
    handleStatsUpdate(data) {
        this.updateDashboardStats(data.stats);
    }
    
    /**
     * Component coordination
     */
    initializeComponents() {
        // Initialize pipeline controller
        if (window.YouTubePipelineUI) {
            this.pipelineController = window.YouTubePipelineUI.pipelineController;
            this.segmentManager = window.YouTubePipelineUI.segmentManager;
            this.logHandler = window.YouTubePipelineUI.logHandler;
        }
        
        // Setup cross-component communication
        this.setupComponentCommunication();
    }
    
    setupComponentCommunication() {
        // Share socket connection with other components
        if (this.socket) {
            window.YouTubePipelineUI = window.YouTubePipelineUI || {};
            window.YouTubePipelineUI.socket = this.socket;
        }
        
        // Setup event delegation for component coordination
        document.addEventListener('pipeline:started', (e) => {
            this.appState.pipelineState = 'running';
        });
        
        document.addEventListener('pipeline:completed', (e) => {
            this.appState.pipelineState = 'completed';
            this.loadDashboardStats();
        });
        
        document.addEventListener('episode:selected', (e) => {
            this.handleEpisodeSelection(e.detail.episodeId);
        });
    }
    
    notifyEpisodeSelection(episode) {
        // Notify other components of episode selection
        const event = new CustomEvent('episode:selected', {
            detail: { episode: episode }
        });
        document.dispatchEvent(event);
        
        // Update segments if segment manager is available
        if (this.segmentManager) {
            this.segmentManager.loadEpisodeSegments(episode.path || episode.id);
        }
    }
    
    notifyEpisodeUpdate(episode) {
        const event = new CustomEvent('episode:updated', {
            detail: { episode: episode }
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Page management
     */
    handlePageVisible() {
        // Refresh data when page becomes visible
        if (document.visibilityState === 'visible') {
            this.loadDashboardStats();
            
            // Reconnect socket if needed
            if (this.socket && !this.socket.connected) {
                this.socket.connect();
            }
        }
    }
    
    handleStorageChange(e) {
        // Handle cross-tab state synchronization
        if (e.key === 'app_state') {
            const newState = JSON.parse(e.newValue || '{}');
            this.syncWithStorageState(newState);
        }
    }
    
    syncWithStorageState(newState) {
        // Sync episode selection
        if (newState.selectedEpisode !== this.appState.selectedEpisode) {
            if (this.episodeSelect) {
                this.episodeSelect.value = newState.selectedEpisode || '';
                this.handleEpisodeSelection(newState.selectedEpisode);
            }
        }
        
        // Sync preset selection
        if (newState.selectedPreset !== this.appState.selectedPreset) {
            if (this.presetSelect) {
                this.presetSelect.value = newState.selectedPreset || '';
            }
        }
    }
    
    /**
     * Global keyboard shortcuts
     */
    handleGlobalKeyboard(e) {
        // Only handle shortcuts when not in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'r':
                    e.preventDefault();
                    this.refreshAllData();
                    break;
                case 'e':
                    e.preventDefault();
                    if (this.episodeSelect) {
                        this.episodeSelect.focus();
                    }
                    break;
                case 'p':
                    e.preventDefault();
                    if (this.presetSelect) {
                        this.presetSelect.focus();
                    }
                    break;
            }
        }
    }
    
    /**
     * State management
     */
    saveAppState() {
        try {
            localStorage.setItem('app_state', JSON.stringify(this.appState));
        } catch (error) {
            console.error('Failed to save app state:', error);
        }
    }
    
    restoreAppState() {
        try {
            const savedState = localStorage.getItem('app_state');
            if (savedState) {
                const state = JSON.parse(savedState);
                
                // Restore episode selection
                if (state.selectedEpisode && this.episodeSelect) {
                    this.episodeSelect.value = state.selectedEpisode;
                    this.handleEpisodeSelection(state.selectedEpisode);
                }
                
                // Restore preset selection
                if (state.selectedPreset && this.presetSelect) {
                    this.presetSelect.value = state.selectedPreset;
                }
                
                this.appState = { ...this.appState, ...state };
            }
        } catch (error) {
            console.error('Failed to restore app state:', error);
        }
    }
    
    /**
     * Start periodic updates
     */
    startPeriodicUpdates() {
        // Refresh stats periodically
        setInterval(() => {
            if (!document.hidden && this.connectionStatus === 'connected') {
                this.loadDashboardStats();
            }
        }, this.config.refreshInterval);
        
        // Auto-save state periodically
        setInterval(() => {
            this.saveAppState();
        }, this.config.autoSaveInterval);
    }
    
    /**
     * Notification system
     */
    showNotification(message, type = 'info', duration = 5000) {
        if (!this.notificationContainer) return;
        
        const notification = this.createNotificationElement(message, type);
        this.notificationContainer.appendChild(notification);
        
        // Limit number of notifications
        const notifications = this.notificationContainer.children;
        if (notifications.length > this.config.maxNotifications) {
            notifications[0].remove();
        }
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                this.removeNotification(notification);
            }
        }, duration);
        
        // Also log to console
        console.log(`${type.toUpperCase()}: ${message}`);
    }
    
    createNotificationElement(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification transform transition-all duration-300 translate-x-full opacity-0 ${this.getNotificationClasses(type)}`;
        notification.setAttribute('role', 'alert');
        
        notification.innerHTML = `
            <div class="flex items-center p-4 rounded-lg shadow-lg">
                <span class="mr-3 text-lg">${this.getNotificationIcon(type)}</span>
                <span class="flex-1 text-sm font-medium">${this.escapeHtml(message)}</span>
                <button class="ml-3 text-lg font-bold opacity-70 hover:opacity-100" onclick="this.closest('.notification').remove()">
                    &times;
                </button>
            </div>
        `;
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full', 'opacity-0');
        }, 10);
        
        return notification;
    }
    
    removeNotification(notification) {
        notification.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }
    
    /**
     * Utility functions
     */
    formatStatus(status) {
        return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ');
    }
    
    getStatusClass(status) {
        switch (status) {
            case 'healthy':
            case 'running':
                return 'bg-green-100 text-green-800';
            case 'warning':
                return 'bg-yellow-100 text-yellow-800';
            case 'error':
            case 'failed':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }
    
    getNotificationClasses(type) {
        switch (type) {
            case 'success': return 'bg-green-100 border border-green-300';
            case 'error': return 'bg-red-100 border border-red-300';
            case 'warning': return 'bg-yellow-100 border border-yellow-300';
            default: return 'bg-blue-100 border border-blue-300';
        }
    }
    
    getNotificationIcon(type) {
        switch (type) {
            case 'success': return '✅';
            case 'error': return '❌';
            case 'warning': return '⚠️';
            default: return 'ℹ️';
        }
    }
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
}

// Global notification function for external use
window.showNotification = function(message, type = 'info') {
    if (window.YouTubePipelineUI && window.YouTubePipelineUI.mainDashboard) {
        window.YouTubePipelineUI.mainDashboard.showNotification(message, type);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
    }
};

// Initialize main dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.YouTubePipelineUI = window.YouTubePipelineUI || {};
    window.YouTubePipelineUI.mainDashboard = new MainDashboard();
    
    // Initialize component coordination after a short delay to ensure all components are loaded
    setTimeout(() => {
        window.YouTubePipelineUI.mainDashboard.initializeComponents();
    }, 500);
    
    console.log('🏠 Main Dashboard ready');
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MainDashboard;
}
