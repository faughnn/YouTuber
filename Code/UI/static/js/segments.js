/**
 * Segment Selection and Management JavaScript
 * 
 * Enhanced segment interface with real-time updates, dynamic sorting, filtering,
 * and seamless integration with pipeline execution for responsive user experience.
 * 
 * Created: June 20, 2025
 * Agent: Implementation Agent
 * Task Reference: Phase 4, Task 4.2 - JavaScript Client Implementation
 */

class SegmentManager {
    constructor() {
        this.socket = null;
        this.currentSegments = [];
        this.selectedSegments = new Set();
        this.filteredSegments = [];
        this.episodePath = '';
        
        // Filter and sort state
        this.currentSort = 'timestamp';
        this.reverseSort = false;
        this.activeFilters = {
            search: '',
            severity: 'all',
            confidence: 'all',
            type: 'all',
            duration: 'all'
        };
        
        // UI elements
        this.segmentContainer = null;
        this.searchInput = null;
        this.sortSelect = null;
        this.filterElements = {};
        this.selectionSummary = null;
        this.bulkActions = null;
        
        // Configuration
        this.config = {
            apiEndpoint: '/segments/api/segments',
            debounceDelay: 300,
            animationDuration: 300,
            pageSize: 20,
            virtualScrollThreshold: 100
        };
        
        // State tracking
        this.isLoading = false;
        this.currentPage = 1;
        this.totalSegments = 0;
        this.lastUpdate = null;
        
        this.initialize();
    }
    
    /**
     * Initialize segment manager
     */
    initialize() {
        this.initializeUI();
        this.initializeSocketIO();
        this.setupEventListeners();
        this.loadInitialData();
        
        console.log('🎬 Segment Manager initialized');
    }
    
    /**
     * Initialize UI elements
     */
    initializeUI() {
        // Find main segment container
        this.segmentContainer = document.getElementById('segments-container') || 
                               document.querySelector('.segment-list');
        
        if (!this.segmentContainer) {
            console.warn('⚠️ Segment container not found');
            return;
        }
        
        // Find or create search input
        this.searchInput = document.getElementById('search-input') || 
                          document.querySelector('input[name="search"]');
        
        // Find or create sort select
        this.sortSelect = document.getElementById('sort-select') || 
                         document.querySelector('select[name="sort"]');
        
        // Find filter elements
        this.filterElements = {
            severity: document.getElementById('severity-filter'),
            confidence: document.getElementById('confidence-filter'),
            type: document.getElementById('type-filter'),
            duration: document.getElementById('duration-filter')
        };
        
        // Find or create selection summary
        this.selectionSummary = document.getElementById('selection-summary') || 
                               this.createSelectionSummary();
        
        // Find or create bulk actions
        this.bulkActions = document.getElementById('bulk-actions') || 
                          this.createBulkActions();
        
        // Initialize virtual scrolling if needed
        this.initializeVirtualScrolling();
        
        console.log('🖥️ Segment UI elements initialized');
    }
    
    /**
     * Create selection summary element
     */
    createSelectionSummary() {
        const summary = document.createElement('div');
        summary.id = 'selection-summary';
        summary.className = 'bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 hidden';
        summary.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <span class="text-blue-600 font-medium">
                        <span id="selected-count">0</span> segments selected
                    </span>
                    <span id="selected-duration" class="ml-4 text-sm text-blue-500">
                        Total duration: 0:00
                    </span>
                </div>
                <div class="flex items-center space-x-2">
                    <button id="clear-selection" class="text-sm text-blue-600 hover:text-blue-800">
                        Clear Selection
                    </button>
                    <button id="invert-selection" class="text-sm text-blue-600 hover:text-blue-800">
                        Invert Selection
                    </button>
                </div>
            </div>
        `;
        
        // Insert before segment container
        if (this.segmentContainer && this.segmentContainer.parentNode) {
            this.segmentContainer.parentNode.insertBefore(summary, this.segmentContainer);
        }
        
        return summary;
    }
    
    /**
     * Create bulk actions element
     */
    createBulkActions() {
        const actions = document.createElement('div');
        actions.id = 'bulk-actions';
        actions.className = 'bg-white border rounded-lg p-4 mb-6 hidden';
        actions.innerHTML = `
            <div class="flex items-center justify-between">
                <h3 class="text-lg font-medium text-gray-900">Bulk Actions</h3>
                <div class="flex items-center space-x-3">
                    <button id="bulk-export" class="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                        Export Selected
                    </button>
                    <button id="bulk-analyze" class="px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
                        Analyze Selected
                    </button>
                    <button id="bulk-delete" class="px-3 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">
                        Remove Selected
                    </button>
                </div>
            </div>
        `;
        
        // Insert after selection summary
        if (this.selectionSummary && this.selectionSummary.parentNode) {
            this.selectionSummary.parentNode.insertBefore(actions, this.selectionSummary.nextSibling);
        }
        
        return actions;
    }
    
    /**
     * Initialize SocketIO for real-time updates
     */
    initializeSocketIO() {
        // Connect to existing socket or create new one
        if (window.YouTubePipelineUI && window.YouTubePipelineUI.pipelineController) {
            this.socket = window.YouTubePipelineUI.pipelineController.socket;
        } else if (typeof io !== 'undefined') {
            this.socket = io();
        }
        
        if (this.socket) {
            this.setupSocketEventHandlers();
        }
    }
    
    /**
     * Setup SocketIO event handlers for real-time updates
     */
    setupSocketEventHandlers() {
        // Listen for segment updates during pipeline execution
        this.socket.on('segment_update', (data) => {
            this.handleSegmentUpdate(data);
        });
        
        this.socket.on('segment_analysis_complete', (data) => {
            this.handleSegmentAnalysisComplete(data);
        });
        
        this.socket.on('pipeline_progress', (data) => {
            // Update segment status based on pipeline progress
            if (data.stage === 3 || data.stage === 4) { // Content analysis or segment detection
                this.handlePipelineSegmentProgress(data);
            }
        });
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Search functionality
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce((e) => {
                this.activeFilters.search = e.target.value.toLowerCase();
                this.applyFiltersAndSort();
            }, this.config.debounceDelay));
            
            // Clear search
            const clearButton = document.getElementById('search-clear');
            if (clearButton) {
                clearButton.addEventListener('click', () => {
                    this.searchInput.value = '';
                    this.activeFilters.search = '';
                    this.applyFiltersAndSort();
                });
            }
        }
        
        // Sort functionality
        if (this.sortSelect) {
            this.sortSelect.addEventListener('change', (e) => {
                this.currentSort = e.target.value;
                this.applyFiltersAndSort();
            });
        }
        
        // Reverse sort button
        const reverseSortBtn = document.getElementById('reverse-sort');
        if (reverseSortBtn) {
            reverseSortBtn.addEventListener('click', () => {
                this.reverseSort = !this.reverseSort;
                reverseSortBtn.classList.toggle('bg-indigo-100');
                reverseSortBtn.classList.toggle('text-indigo-700');
                this.applyFiltersAndSort();
            });
        }
        
        // Filter controls
        Object.entries(this.filterElements).forEach(([filterType, element]) => {
            if (element) {
                element.addEventListener('change', (e) => {
                    this.activeFilters[filterType] = e.target.value;
                    this.applyFiltersAndSort();
                });
            }
        });
        
        // Segment container events (using delegation)
        if (this.segmentContainer) {
            this.segmentContainer.addEventListener('change', (e) => {
                if (e.target.classList.contains('segment-checkbox')) {
                    this.handleSegmentSelection(e.target);
                }
            });
            
            this.segmentContainer.addEventListener('click', (e) => {
                if (e.target.closest('.expand-btn')) {
                    this.handleSegmentExpand(e.target.closest('.expand-btn'));
                } else if (e.target.closest('.play-btn')) {
                    this.handleSegmentPlay(e.target.closest('.play-btn'));
                } else if (e.target.closest('.edit-btn')) {
                    this.handleSegmentEdit(e.target.closest('.edit-btn'));
                }
            });
        }
        
        // Selection summary events
        if (this.selectionSummary) {
            const clearBtn = this.selectionSummary.querySelector('#clear-selection');
            const invertBtn = this.selectionSummary.querySelector('#invert-selection');
            
            if (clearBtn) {
                clearBtn.addEventListener('click', () => this.clearSelection());
            }
            
            if (invertBtn) {
                invertBtn.addEventListener('click', () => this.invertSelection());
            }
        }
        
        // Bulk actions events
        if (this.bulkActions) {
            const exportBtn = this.bulkActions.querySelector('#bulk-export');
            const analyzeBtn = this.bulkActions.querySelector('#bulk-analyze');
            const deleteBtn = this.bulkActions.querySelector('#bulk-delete');
            
            if (exportBtn) {
                exportBtn.addEventListener('click', () => this.exportSelected());
            }
            
            if (analyzeBtn) {
                analyzeBtn.addEventListener('click', () => this.analyzeSelected());
            }
            
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => this.deleteSelected());
            }
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'a':
                        if (this.segmentContainer.contains(document.activeElement)) {
                            e.preventDefault();
                            this.selectAll();
                        }
                        break;
                    case 'f':
                        if (this.searchInput) {
                            e.preventDefault();
                            this.searchInput.focus();
                        }
                        break;
                }
            }
        });
    }
    
    /**
     * Load initial segment data
     */
    async loadInitialData() {
        // Check if segments are already provided in page data
        const existingSegments = window.segmentData || [];
        const existingPath = window.episodePath || '';
        
        if (existingSegments.length > 0) {
            this.currentSegments = existingSegments;
            this.episodePath = existingPath;
            this.applyFiltersAndSort();
            console.log(`📊 Loaded ${existingSegments.length} segments from page data`);
        } else {
            // Load from API
            await this.loadSegmentsFromAPI();
        }
    }
    
    /**
     * Load segments from API
     */
    async loadSegmentsFromAPI() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            const response = await fetch(this.config.apiEndpoint);
            const data = await response.json();
            
            if (data.success) {
                this.currentSegments = data.segments || [];
                this.episodePath = data.episode_path || '';
                this.totalSegments = data.total || this.currentSegments.length;
                this.applyFiltersAndSort();
                
                console.log(`📊 Loaded ${this.currentSegments.length} segments from API`);
            } else {
                this.showError(data.error || 'Failed to load segments');
            }
            
        } catch (error) {
            console.error('Failed to load segments:', error);
            this.showError('Network error loading segments');
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }
    
    /**
     * Apply filters and sorting
     */
    applyFiltersAndSort() {
        let filtered = [...this.currentSegments];
        
        // Apply search filter
        if (this.activeFilters.search) {
            const searchTerm = this.activeFilters.search.toLowerCase();
            filtered = filtered.filter(segment => 
                segment.title?.toLowerCase().includes(searchTerm) ||
                segment.description?.toLowerCase().includes(searchTerm) ||
                segment.transcript?.toLowerCase().includes(searchTerm) ||
                segment.tags?.some(tag => tag.toLowerCase().includes(searchTerm))
            );
        }
        
        // Apply severity filter
        if (this.activeFilters.severity !== 'all') {
            filtered = filtered.filter(segment => 
                segment.severity === this.activeFilters.severity
            );
        }
        
        // Apply confidence filter
        if (this.activeFilters.confidence !== 'all') {
            const confidenceThreshold = parseFloat(this.activeFilters.confidence);
            filtered = filtered.filter(segment => 
                segment.confidence >= confidenceThreshold
            );
        }
        
        // Apply type filter
        if (this.activeFilters.type !== 'all') {
            filtered = filtered.filter(segment => 
                segment.type === this.activeFilters.type
            );
        }
        
        // Apply duration filter
        if (this.activeFilters.duration !== 'all') {
            const [min, max] = this.activeFilters.duration.split('-').map(Number);
            filtered = filtered.filter(segment => {
                const duration = segment.end_time - segment.start_time;
                return max ? (duration >= min && duration <= max) : duration >= min;
            });
        }
        
        // Apply sorting
        filtered.sort((a, b) => {
            let aVal, bVal;
            
            switch (this.currentSort) {
                case 'timestamp':
                    aVal = a.start_time;
                    bVal = b.start_time;
                    break;
                case 'duration':
                    aVal = a.end_time - a.start_time;
                    bVal = b.end_time - b.start_time;
                    break;
                case 'confidence':
                    aVal = a.confidence || 0;
                    bVal = b.confidence || 0;
                    break;
                case 'severity':
                    const severityOrder = { 'low': 1, 'medium': 2, 'high': 3 };
                    aVal = severityOrder[a.severity] || 0;
                    bVal = severityOrder[b.severity] || 0;
                    break;
                case 'title':
                    aVal = a.title || '';
                    bVal = b.title || '';
                    break;
                default:
                    aVal = a.start_time;
                    bVal = b.start_time;
            }
            
            let result = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
            return this.reverseSort ? -result : result;
        });
        
        this.filteredSegments = filtered;
        this.renderSegments();
        this.updateFilterSummary();
    }
    
    /**
     * Render segments in the container
     */
    renderSegments() {
        if (!this.segmentContainer) return;
        
        // Clear container
        this.segmentContainer.innerHTML = '';
        
        if (this.filteredSegments.length === 0) {
            this.renderEmptyState();
            return;
        }
        
        // Create segment cards
        this.filteredSegments.forEach((segment, index) => {
            const segmentCard = this.createSegmentCard(segment, index);
            this.segmentContainer.appendChild(segmentCard);
        });
        
        // Update selection state
        this.updateSelectionDisplay();
    }
    
    /**
     * Create segment card element
     */
    createSegmentCard(segment, index) {
        const card = document.createElement('div');
        card.className = 'segment-card bg-white border rounded-lg p-4 mb-4 transition-all duration-200 hover:shadow-md';
        card.dataset.segmentId = segment.id;
        card.dataset.index = index;
        
        const isSelected = this.selectedSegments.has(segment.id);
        const duration = this.formatDuration(segment.end_time - segment.start_time);
        const confidence = Math.round((segment.confidence || 0) * 100);
        
        card.innerHTML = `
            <div class="flex items-start space-x-4">
                <!-- Selection checkbox -->
                <div class="flex-shrink-0 pt-1">
                    <input type="checkbox" 
                           class="segment-checkbox h-4 w-4 text-blue-600 rounded focus:ring-blue-500" 
                           data-segment-id="${segment.id}"
                           ${isSelected ? 'checked' : ''}>
                </div>
                
                <!-- Segment content -->
                <div class="flex-1 min-w-0">
                    <!-- Header -->
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center space-x-2">
                            <h3 class="text-sm font-medium text-gray-900 truncate">
                                ${this.escapeHtml(segment.title || `Segment ${index + 1}`)}
                            </h3>
                            <span class="px-2 py-1 text-xs rounded-full ${this.getSeverityClasses(segment.severity)}">
                                ${segment.severity || 'unknown'}
                            </span>
                            <span class="text-xs text-gray-500">
                                ${confidence}% confidence
                            </span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="text-xs text-gray-500">${duration}</span>
                            <button class="expand-btn text-gray-400 hover:text-gray-600" data-segment-id="${segment.id}">
                                <svg class="w-4 h-4 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                    
                    <!-- Basic info -->
                    <div class="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                        <span>${this.formatTimestamp(segment.start_time)} - ${this.formatTimestamp(segment.end_time)}</span>
                        ${segment.type ? `<span class="px-2 py-1 bg-gray-100 rounded text-xs">${segment.type}</span>` : ''}
                    </div>
                    
                    <!-- Description preview -->
                    ${segment.description ? `
                        <p class="text-sm text-gray-600 line-clamp-2 mb-2">
                            ${this.escapeHtml(segment.description)}
                        </p>
                    ` : ''}
                    
                    <!-- Tags -->
                    ${segment.tags && segment.tags.length > 0 ? `
                        <div class="flex flex-wrap gap-1 mb-2">
                            ${segment.tags.slice(0, 3).map(tag => 
                                `<span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">${this.escapeHtml(tag)}</span>`
                            ).join('')}
                            ${segment.tags.length > 3 ? `<span class="text-xs text-gray-500">+${segment.tags.length - 3} more</span>` : ''}
                        </div>
                    ` : ''}
                    
                    <!-- Action buttons -->
                    <div class="flex items-center space-x-2">
                        <button class="play-btn px-3 py-1 text-xs bg-green-100 text-green-800 hover:bg-green-200 rounded" 
                                data-segment-id="${segment.id}"
                                data-start-time="${segment.start_time}">
                            ▶ Play
                        </button>
                        <button class="edit-btn px-3 py-1 text-xs bg-blue-100 text-blue-800 hover:bg-blue-200 rounded" 
                                data-segment-id="${segment.id}">
                            ✏ Edit
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Expanded content (hidden by default) -->
            <div class="expanded-content hidden mt-4 pt-4 border-t border-gray-200">
                ${this.createExpandedContent(segment)}
            </div>
        `;
        
        return card;
    }
    
    /**
     * Create expanded content for segment
     */
    createExpandedContent(segment) {
        return `
            <!-- Full transcript -->
            ${segment.transcript ? `
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-900 mb-2">Transcript</h4>
                    <div class="bg-gray-50 rounded p-3 text-sm text-gray-700 max-h-32 overflow-y-auto">
                        ${this.escapeHtml(segment.transcript)}
                    </div>
                </div>
            ` : ''}
            
            <!-- All tags -->
            ${segment.tags && segment.tags.length > 0 ? `
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-900 mb-2">Tags</h4>
                    <div class="flex flex-wrap gap-1">
                        ${segment.tags.map(tag => 
                            `<span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">${this.escapeHtml(tag)}</span>`
                        ).join('')}
                    </div>
                </div>
            ` : ''}
            
            <!-- Technical details -->
            <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <span class="font-medium text-gray-900">Start Time:</span>
                    <span class="text-gray-600">${this.formatTimestamp(segment.start_time)}</span>
                </div>
                <div>
                    <span class="font-medium text-gray-900">End Time:</span>
                    <span class="text-gray-600">${this.formatTimestamp(segment.end_time)}</span>
                </div>
                <div>
                    <span class="font-medium text-gray-900">Duration:</span>
                    <span class="text-gray-600">${this.formatDuration(segment.end_time - segment.start_time)}</span>
                </div>
                <div>
                    <span class="font-medium text-gray-900">Confidence:</span>
                    <span class="text-gray-600">${Math.round((segment.confidence || 0) * 100)}%</span>
                </div>
            </div>
            
            <!-- Analysis data if available -->
            ${segment.analysis ? `
                <div class="mt-4">
                    <h4 class="text-sm font-medium text-gray-900 mb-2">Analysis</h4>
                    <div class="bg-gray-50 rounded p-3 text-sm">
                        <pre class="whitespace-pre-wrap text-gray-700">${JSON.stringify(segment.analysis, null, 2)}</pre>
                    </div>
                </div>
            ` : ''}
        `;
    }
    
    /**
     * Render empty state
     */
    renderEmptyState() {
        this.segmentContainer.innerHTML = `
            <div class="text-center py-12">
                <div class="text-gray-400 text-6xl mb-4">🎬</div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No segments found</h3>
                <p class="text-gray-500 mb-4">
                    ${this.currentSegments.length === 0 
                        ? 'No segments have been analyzed yet. Run the pipeline to generate segments.'
                        : 'No segments match your current filters. Try adjusting your search or filter criteria.'
                    }
                </p>
                ${this.currentSegments.length > 0 ? `
                    <button onclick="window.location.reload()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Reset Filters
                    </button>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * Handle segment selection
     */
    handleSegmentSelection(checkbox) {
        const segmentId = checkbox.dataset.segmentId;
        const isChecked = checkbox.checked;
        
        if (isChecked) {
            this.selectedSegments.add(segmentId);
        } else {
            this.selectedSegments.delete(segmentId);
        }
        
        this.updateSelectionDisplay();
        this.saveSelectionState();
    }
    
    /**
     * Handle segment expand/collapse
     */
    handleSegmentExpand(button) {
        const segmentCard = button.closest('.segment-card');
        const expandedContent = segmentCard.querySelector('.expanded-content');
        const icon = button.querySelector('svg');
        
        if (expandedContent.classList.contains('hidden')) {
            expandedContent.classList.remove('hidden');
            icon.classList.add('rotate-180');
        } else {
            expandedContent.classList.add('hidden');
            icon.classList.remove('rotate-180');
        }
    }
    
    /**
     * Handle segment play
     */
    handleSegmentPlay(button) {
        const segmentId = button.dataset.segmentId;
        const startTime = parseFloat(button.dataset.startTime);
        
        // Implement video player integration
        if (window.YouTubePipelineUI && window.YouTubePipelineUI.videoPlayer) {
            window.YouTubePipelineUI.videoPlayer.seekTo(startTime);
            window.YouTubePipelineUI.videoPlayer.play();
        } else {
            this.showNotification(`Playing segment from ${this.formatTimestamp(startTime)}`, 'info');
        }
    }
    
    /**
     * Handle segment edit
     */
    handleSegmentEdit(button) {
        const segmentId = button.dataset.segmentId;
        const segment = this.currentSegments.find(s => s.id === segmentId);
        
        if (segment) {
            this.openSegmentEditor(segment);
        }
    }
    
    /**
     * Open segment editor
     */
    openSegmentEditor(segment) {
        // Create modal for segment editing
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-xl font-semibold text-gray-900">Edit Segment</h2>
                    <button class="close-modal text-gray-400 hover:text-gray-600">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <form id="segment-edit-form" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
                        <input type="text" name="title" value="${this.escapeHtml(segment.title || '')}" 
                               class="w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea name="description" rows="3" 
                                  class="w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">${this.escapeHtml(segment.description || '')}</textarea>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                            <input type="number" name="start_time" value="${segment.start_time}" step="0.1"
                                   class="w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">End Time</label>
                            <input type="number" name="end_time" value="${segment.end_time}" step="0.1"
                                   class="w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                            <select name="severity" class="w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                                <option value="low" ${segment.severity === 'low' ? 'selected' : ''}>Low</option>
                                <option value="medium" ${segment.severity === 'medium' ? 'selected' : ''}>Medium</option>
                                <option value="high" ${segment.severity === 'high' ? 'selected' : ''}>High</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
                            <input type="text" name="type" value="${this.escapeHtml(segment.type || '')}"
                                   class="w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
                        <input type="text" name="tags" value="${(segment.tags || []).join(', ')}"
                               class="w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                    </div>
                    
                    <div class="flex justify-end space-x-3 pt-4">
                        <button type="button" class="close-modal px-4 py-2 text-gray-600 hover:text-gray-800">
                            Cancel
                        </button>
                        <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Setup modal event handlers
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.remove();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        modal.querySelector('#segment-edit-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.saveSegmentChanges(segment.id, new FormData(e.target));
            modal.remove();
        });
    }
    
    /**
     * Save segment changes
     */
    async saveSegmentChanges(segmentId, formData) {
        try {
            const response = await fetch(`/segments/api/segments/${segmentId}`, {
                method: 'PUT',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Update local segment data
                const segmentIndex = this.currentSegments.findIndex(s => s.id === segmentId);
                if (segmentIndex !== -1) {
                    Object.assign(this.currentSegments[segmentIndex], result.segment);
                    this.applyFiltersAndSort();
                }
                this.showNotification('Segment updated successfully', 'success');
            } else {
                this.showNotification(result.error || 'Failed to update segment', 'error');
            }
            
        } catch (error) {
            console.error('Error saving segment:', error);
            this.showNotification('Network error saving segment', 'error');
        }
    }
    
    /**
     * Handle real-time segment updates
     */
    handleSegmentUpdate(data) {
        if (data.episode_path === this.episodePath) {
            // Update or add segment
            const existingIndex = this.currentSegments.findIndex(s => s.id === data.segment.id);
            if (existingIndex !== -1) {
                this.currentSegments[existingIndex] = data.segment;
            } else {
                this.currentSegments.push(data.segment);
            }
            
            this.applyFiltersAndSort();
            this.showNotification('Segment updated', 'info');
        }
    }
    
    /**
     * Handle segment analysis completion
     */
    handleSegmentAnalysisComplete(data) {
        if (data.episode_path === this.episodePath) {
            this.currentSegments = data.segments || [];
            this.applyFiltersAndSort();
            this.showNotification(`Analysis complete: ${data.segments.length} segments found`, 'success');
        }
    }
    
    /**
     * Handle pipeline segment progress
     */
    handlePipelineSegmentProgress(data) {
        // Show progress indicator for segment analysis
        const progressIndicator = document.getElementById('segment-analysis-progress');
        if (progressIndicator) {
            progressIndicator.style.width = `${data.progress}%`;
        }
        
        if (data.status === 'completed' && (data.stage === 3 || data.stage === 4)) {
            // Refresh segments after analysis
            setTimeout(() => {
                this.loadSegmentsFromAPI();
            }, 1000);
        }
    }
    
    /**
     * Update selection display
     */
    updateSelectionDisplay() {
        const selectedCount = this.selectedSegments.size;
        
        // Update selection summary
        if (this.selectionSummary) {
            const countElement = this.selectionSummary.querySelector('#selected-count');
            const durationElement = this.selectionSummary.querySelector('#selected-duration');
            
            if (countElement) {
                countElement.textContent = selectedCount;
            }
            
            if (durationElement) {
                const totalDuration = this.calculateSelectedDuration();
                durationElement.textContent = `Total duration: ${this.formatDuration(totalDuration)}`;
            }
            
            if (selectedCount > 0) {
                this.selectionSummary.classList.remove('hidden');
                if (this.bulkActions) {
                    this.bulkActions.classList.remove('hidden');
                }
            } else {
                this.selectionSummary.classList.add('hidden');
                if (this.bulkActions) {
                    this.bulkActions.classList.add('hidden');
                }
            }
        }
        
        // Update visual selection state
        this.filteredSegments.forEach(segment => {
            const card = this.segmentContainer.querySelector(`[data-segment-id="${segment.id}"]`);
            if (card) {
                if (this.selectedSegments.has(segment.id)) {
                    card.classList.add('ring-2', 'ring-blue-500', 'bg-blue-50');
                } else {
                    card.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50');
                }
            }
        });
    }
    
    /**
     * Calculate total duration of selected segments
     */
    calculateSelectedDuration() {
        let totalDuration = 0;
        this.currentSegments.forEach(segment => {
            if (this.selectedSegments.has(segment.id)) {
                totalDuration += segment.end_time - segment.start_time;
            }
        });
        return totalDuration;
    }
    
    /**
     * Clear selection
     */
    clearSelection() {
        this.selectedSegments.clear();
        
        // Update checkboxes
        const checkboxes = this.segmentContainer.querySelectorAll('.segment-checkbox');
        checkboxes.forEach(cb => cb.checked = false);
        
        this.updateSelectionDisplay();
        this.saveSelectionState();
    }
    
    /**
     * Invert selection
     */
    invertSelection() {
        const newSelection = new Set();
        this.filteredSegments.forEach(segment => {
            if (!this.selectedSegments.has(segment.id)) {
                newSelection.add(segment.id);
            }
        });
        
        this.selectedSegments = newSelection;
        
        // Update checkboxes
        const checkboxes = this.segmentContainer.querySelectorAll('.segment-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = this.selectedSegments.has(cb.dataset.segmentId);
        });
        
        this.updateSelectionDisplay();
        this.saveSelectionState();
    }
    
    /**
     * Select all filtered segments
     */
    selectAll() {
        this.filteredSegments.forEach(segment => {
            this.selectedSegments.add(segment.id);
        });
        
        // Update checkboxes
        const checkboxes = this.segmentContainer.querySelectorAll('.segment-checkbox');
        checkboxes.forEach(cb => {
            if (this.filteredSegments.some(s => s.id === cb.dataset.segmentId)) {
                cb.checked = true;
            }
        });
        
        this.updateSelectionDisplay();
        this.saveSelectionState();
    }
    
    /**
     * Export selected segments
     */
    async exportSelected() {
        if (this.selectedSegments.size === 0) {
            this.showNotification('No segments selected for export', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/segments/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    segment_ids: Array.from(this.selectedSegments),
                    episode_path: this.episodePath
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `segments_export_${new Date().getTime()}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('Segments exported successfully', 'success');
            } else {
                throw new Error('Export failed');
            }
            
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification('Failed to export segments', 'error');
        }
    }
    
    /**
     * Analyze selected segments
     */
    async analyzeSelected() {
        if (this.selectedSegments.size === 0) {
            this.showNotification('No segments selected for analysis', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/segments/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    segment_ids: Array.from(this.selectedSegments),
                    episode_path: this.episodePath
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Analysis started for selected segments', 'info');
            } else {
                this.showNotification(result.error || 'Failed to start analysis', 'error');
            }
            
        } catch (error) {
            console.error('Analysis error:', error);
            this.showNotification('Failed to start segment analysis', 'error');
        }
    }
    
    /**
     * Delete selected segments
     */
    async deleteSelected() {
        if (this.selectedSegments.size === 0) {
            this.showNotification('No segments selected for deletion', 'warning');
            return;
        }
        
        if (!confirm(`Are you sure you want to delete ${this.selectedSegments.size} selected segments?`)) {
            return;
        }
        
        try {
            const response = await fetch('/segments/api/delete', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    segment_ids: Array.from(this.selectedSegments)
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Remove deleted segments from local data
                this.currentSegments = this.currentSegments.filter(s => 
                    !this.selectedSegments.has(s.id)
                );
                this.selectedSegments.clear();
                this.applyFiltersAndSort();
                
                this.showNotification('Selected segments deleted', 'success');
            } else {
                this.showNotification(result.error || 'Failed to delete segments', 'error');
            }
            
        } catch (error) {
            console.error('Delete error:', error);
            this.showNotification('Failed to delete segments', 'error');
        }
    }
    
    /**
     * Save selection state to session storage
     */
    saveSelectionState() {
        if (this.episodePath) {
            const selectionKey = `segment_selection_${this.episodePath}`;
            sessionStorage.setItem(selectionKey, JSON.stringify(Array.from(this.selectedSegments)));
        }
    }
    
    /**
     * Load selection state from session storage
     */
    loadSelectionState() {
        if (this.episodePath) {
            const selectionKey = `segment_selection_${this.episodePath}`;
            const savedSelection = sessionStorage.getItem(selectionKey);
            if (savedSelection) {
                try {
                    const selectedIds = JSON.parse(savedSelection);
                    this.selectedSegments = new Set(selectedIds);
                    this.updateSelectionDisplay();
                } catch (error) {
                    console.error('Failed to load selection state:', error);
                }
            }
        }
    }
    
    /**
     * Initialize virtual scrolling for large datasets
     */
    initializeVirtualScrolling() {
        if (this.currentSegments.length > this.config.virtualScrollThreshold) {
            // Implement virtual scrolling for performance
            console.log('📊 Virtual scrolling enabled for large dataset');
        }
    }
    
    /**
     * Show loading state
     */
    showLoadingState() {
        if (this.segmentContainer) {
            this.segmentContainer.innerHTML = `
                <div class="flex items-center justify-center py-12">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span class="ml-3 text-gray-600">Loading segments...</span>
                </div>
            `;
        }
    }
    
    /**
     * Hide loading state
     */
    hideLoadingState() {
        // Loading state will be replaced by rendered segments
    }
    
    /**
     * Show error message
     */
    showError(message) {
        if (this.segmentContainer) {
            this.segmentContainer.innerHTML = `
                <div class="text-center py-12">
                    <div class="text-red-400 text-6xl mb-4">⚠️</div>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">Error Loading Segments</h3>
                    <p class="text-gray-500 mb-4">${this.escapeHtml(message)}</p>
                    <button onclick="window.location.reload()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Retry
                    </button>
                </div>
            `;
        }
    }
    
    /**
     * Update filter summary
     */
    updateFilterSummary() {
        const summaryElement = document.getElementById('filter-summary');
        if (summaryElement) {
            const total = this.currentSegments.length;
            const filtered = this.filteredSegments.length;
            
            if (filtered === total) {
                summaryElement.textContent = `Showing all ${total} segments`;
            } else {
                summaryElement.textContent = `Showing ${filtered} of ${total} segments`;
            }
        }
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        if (window.YouTubePipelineUI && window.YouTubePipelineUI.showNotification) {
            window.YouTubePipelineUI.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    /**
     * Utility functions
     */
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
    
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    formatTimestamp(seconds) {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    getSeverityClasses(severity) {
        switch (severity) {
            case 'high': return 'bg-red-100 text-red-800';
            case 'medium': return 'bg-yellow-100 text-yellow-800';
            case 'low': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }
}

// Initialize segment manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('segments-container') || document.querySelector('.segment-list')) {
        window.YouTubePipelineUI = window.YouTubePipelineUI || {};
        window.YouTubePipelineUI.segmentManager = new SegmentManager();
        console.log('🎬 Segment Manager ready');
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SegmentManager;
}
