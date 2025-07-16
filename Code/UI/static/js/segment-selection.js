/**
 * Segment Selection JavaScript
 * Handles interactive segment selection, sorting, filtering, and selection persistence
 * 
 * Created: June 20, 2025
 * Agent: Implementation Agent
 * Task Reference: Phase 3, Task 3.2 - Segment Selection UI
 */

// Segment Selection Module
window.SegmentSelection = (function() {
    'use strict';
    
    // Private variables
    let currentSegments = [];
    let selectedSegments = new Set();
    let currentSort = 'timestamp';
    let reverseSort = false;
    let episodePath = '';
    
    // Configuration
    const config = {
        apiEndpoint: '/segments/api/segments',
        debounceDelay: 300,
        animationDuration: 300
    };
    
    // Initialize the module
    function init(segments, path) {
        console.log('🎬 Initializing Segment Selection Module...');
        
        currentSegments = segments || [];
        episodePath = path || '';
        
        setupEventListeners();
        updateSelectionSummary();
        
        console.log(`✅ Segment Selection initialized with ${currentSegments.length} segments`);
    }
    
    // Setup event listeners
    function setupEventListeners() {
        // Individual segment selection
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('segment-checkbox')) {
                handleSegmentSelection(e.target);
            }
        });
        
        // Segment expansion
        document.addEventListener('click', function(e) {
            if (e.target.closest('.expand-btn')) {
                handleSegmentExpand(e.target.closest('.expand-btn'));
            }
        });
        
        // Sort controls
        const sortSelect = document.getElementById('sort-select');
        const reverseSortBtn = document.getElementById('reverse-sort');
        
        if (sortSelect) {
            sortSelect.addEventListener('change', function() {
                currentSort = this.value;
                handleSortChange();
            });
        }
        
        if (reverseSortBtn) {
            reverseSortBtn.addEventListener('click', function() {
                reverseSort = !reverseSort;
                this.classList.toggle('bg-indigo-100');
                this.classList.toggle('text-indigo-700');
                handleSortChange();
            });
        }
        
        // Search functionality
        const searchInput = document.getElementById('search-input');
        const searchClear = document.getElementById('search-clear');
        
        if (searchInput) {
            searchInput.addEventListener('input', debounce(handleSearch, config.debounceDelay));
        }
        
        if (searchClear) {
            searchClear.addEventListener('click', function() {
                if (searchInput) {
                    searchInput.value = '';
                    handleSearch();
                }
            });
        }
        
        // Filter controls
        ['severity-filter', 'confidence-filter'].forEach(filterId => {
            const filterElement = document.getElementById(filterId);
            if (filterElement) {
                filterElement.addEventListener('change', handleFilterChange);
            }
        });
        
        // Action buttons
        const clearBtn = document.getElementById('clear-selection');
        const saveBtn = document.getElementById('save-selection');
        const previewBtn = document.getElementById('preview-selection');
        
        if (clearBtn) {
            clearBtn.addEventListener('click', clearSelection);
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', saveSelection);
        }
        
        if (previewBtn) {
            previewBtn.addEventListener('click', previewSelection);
        }
    }
    
    // Handle individual segment selection
    function handleSegmentSelection(checkbox) {
        const segmentId = checkbox.dataset.segmentId;
        const card = document.querySelector(`.segment-card[data-segment-id="${segmentId}"]`);
        
        if (!card) return;
        
        if (checkbox.checked) {
            selectedSegments.add(segmentId);
            card.classList.add('selected');
        } else {
            selectedSegments.delete(segmentId);
            card.classList.remove('selected');
        }
        
        updateSelectionSummary();
        
        // Add visual feedback
        card.style.transform = 'scale(1.02)';
        setTimeout(() => {
            card.style.transform = '';
        }, 150);
    }
    
    // Handle segment detail expansion
    function handleSegmentExpand(button) {
        const segmentId = button.dataset.segmentId;
        const details = document.querySelector(`.segment-details[data-segment-id="${segmentId}"]`);
        const icon = button.querySelector('svg');
        
        if (!details || !icon) return;
        
        if (details.classList.contains('expanded')) {
            details.classList.remove('expanded');
            icon.classList.remove('rotate-180');
        } else {
            details.classList.add('expanded');
            icon.classList.add('rotate-180');
        }
    }
    
    // Handle sort changes (with API call)
    async function handleSortChange() {
        showLoadingState();
        
        try {
            const response = await fetch(`${config.apiEndpoint}/${encodeURIComponent(episodePath)}?sort_by=${currentSort}&reverse=${reverseSort}`);
            const data = await response.json();
            
            if (data.success) {
                currentSegments = data.segments;
                rerenderSegments();
            } else {
                console.error('Sort error:', data.error);
                showNotification('Error sorting segments', 'error');
            }
        } catch (error) {
            console.error('Sort request failed:', error);
            showNotification('Failed to sort segments', 'error');
        } finally {
            hideLoadingState();
        }
    }
    
    // Handle search
    function handleSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        const searchTerm = searchInput.value.toLowerCase();
        const cards = document.querySelectorAll('.segment-card');
        
        cards.forEach(card => {
            const title = card.querySelector('h3')?.textContent?.toLowerCase() || '';
            const description = card.querySelector('.text-gray-600')?.textContent?.toLowerCase() || '';
            const context = card.querySelector('.segment-details')?.textContent?.toLowerCase() || '';
            
            const isMatch = title.includes(searchTerm) || 
                           description.includes(searchTerm) || 
                           context.includes(searchTerm);
            
            card.style.display = isMatch ? 'block' : 'none';
        });
        
        // Update visible count
        updateVisibleCount();
    }
    
    // Handle filter changes
    function handleFilterChange() {
        const severityFilter = document.getElementById('severity-filter');
        const confidenceFilter = document.getElementById('confidence-filter');
        
        const selectedSeverities = severityFilter ? Array.from(severityFilter.selectedOptions).map(opt => opt.value) : [];
        const selectedConfidences = confidenceFilter ? Array.from(confidenceFilter.selectedOptions).map(opt => opt.value) : [];
        
        const cards = document.querySelectorAll('.segment-card');
        
        cards.forEach(card => {
            const segmentId = card.dataset.segmentId;
            const segment = currentSegments.find(s => s.segment_id === segmentId);
            
            if (!segment) {
                card.style.display = 'none';
                return;
            }
            
            const severityMatch = selectedSeverities.length === 0 || selectedSeverities.includes(segment.severityRating);
            const confidenceMatch = selectedConfidences.length === 0 || selectedConfidences.includes(segment.confidence_in_classification);
            
            card.style.display = (severityMatch && confidenceMatch) ? 'block' : 'none';
        });
        
        updateVisibleCount();
    }
    
    // Update selection summary
    function updateSelectionSummary() {
        const summaryDiv = document.getElementById('selection-summary');
        const countSpan = document.getElementById('selected-count');
        const durationSpan = document.getElementById('selected-duration');
        
        if (!summaryDiv || !countSpan || !durationSpan) return;
        
        if (selectedSegments.size > 0) {
            summaryDiv.style.display = 'block';
            countSpan.textContent = selectedSegments.size;
            
            // Calculate total duration
            let totalDuration = 0;
            selectedSegments.forEach(segmentId => {
                const segment = currentSegments.find(s => s.segment_id === segmentId);
                if (segment) {
                    totalDuration += segment.segmentDurationInSeconds || 0;
                }
            });
            
            durationSpan.textContent = formatDuration(totalDuration);
        } else {
            summaryDiv.style.display = 'none';
        }
    }
    
    // Clear all selections
    function clearSelection() {
        selectedSegments.clear();
        document.querySelectorAll('.segment-checkbox').forEach(cb => cb.checked = false);
        document.querySelectorAll('.segment-card').forEach(card => card.classList.remove('selected'));
        updateSelectionSummary();
        
        showNotification('Selection cleared', 'info');
    }
    
    // Save selection
    async function saveSelection() {
        if (selectedSegments.size === 0) {
            showNotification('Please select at least one segment to save', 'warning');
            return;
        }
        
        const selectedIds = Array.from(selectedSegments);
        
        showLoadingOverlay('Saving segment selection...');
        
        try {
            const response = await fetch(`${config.apiEndpoint}/${encodeURIComponent(episodePath)}/select`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    selected_segments: selectedIds
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification(
                    `Successfully saved ${result.selected_count} segments (${result.total_duration}s total)`,
                    'success'
                );
            } else {
                showNotification(`Error saving selection: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Save selection error:', error);
            showNotification('Error saving selection. Please try again.', 'error');
        } finally {
            hideLoadingOverlay();
        }
    }
    
    // Preview selection
    function previewSelection() {
        if (selectedSegments.size === 0) {
            showNotification('No segments selected for preview', 'warning');
            return;
        }
        
        // Create preview modal
        createPreviewModal();
    }
    
    // Utility functions
    function formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds.toFixed(1)}s`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const remainingSeconds = seconds % 60;
            return `${hours}h ${minutes}m ${remainingSeconds.toFixed(1)}s`;
        }
    }
    
    function debounce(func, wait) {
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
    
    function showLoadingState() {
        const segmentsContainer = document.getElementById('segments-container');
        if (segmentsContainer) {
            segmentsContainer.style.opacity = '0.5';
            segmentsContainer.style.pointerEvents = 'none';
        }
    }
    
    function hideLoadingState() {
        const segmentsContainer = document.getElementById('segments-container');
        if (segmentsContainer) {
            segmentsContainer.style.opacity = '';
            segmentsContainer.style.pointerEvents = '';
        }
    }
    
    function showLoadingOverlay(message) {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');
        
        if (overlay) {
            if (messageEl) messageEl.textContent = message;
            overlay.style.display = 'flex';
        }
    }
    
    function hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    function showNotification(message, type = 'info') {
        // Create or update notification element
        let notification = document.getElementById('notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.className = 'fixed top-4 right-4 z-50 max-w-sm';
            document.body.appendChild(notification);
        }
        
        const bgColor = {
            'success': 'bg-green-100 border-green-400 text-green-700',
            'error': 'bg-red-100 border-red-400 text-red-700',
            'warning': 'bg-yellow-100 border-yellow-400 text-yellow-700',
            'info': 'bg-blue-100 border-blue-400 text-blue-700'
        }[type] || 'bg-gray-100 border-gray-400 text-gray-700';
        
        notification.innerHTML = `
            <div class="border px-4 py-3 rounded ${bgColor} shadow-lg">
                <div class="flex items-center justify-between">
                    <span>${message}</span>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-lg leading-none">&times;</button>
                </div>
            </div>
        `;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (notification) {
                notification.remove();
            }
        }, 5000);
    }
    
    function updateVisibleCount() {
        const visibleCards = document.querySelectorAll('.segment-card[style*="display: block"], .segment-card:not([style*="display: none"])');
        console.log(`${visibleCards.length} segments visible`);
    }
    
    function rerenderSegments() {
        // This would re-render the segments with new data
        // For now, just update the display
        console.log('Segments reordered');
    }
    
    function createPreviewModal() {
        // Create preview modal for selected segments
        const selectedData = Array.from(selectedSegments).map(id => 
            currentSegments.find(s => s.segment_id === id)
        ).filter(Boolean);
        
        console.log('Preview segments:', selectedData);
        showNotification(`Preview: ${selectedData.length} segments selected`, 'info');
    }
    
    // Public API
    return {
        init: init,
        getSelectedSegments: () => Array.from(selectedSegments),
        clearSelection: clearSelection,
        saveSelection: saveSelection
    };
})();
