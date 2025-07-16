/**
 * Preset Management System - JavaScript Client
 * 
 * Handles preset creation, loading, deletion, and pipeline integration
 * with real-time updates and comprehensive validation.
 * 
 * Created: June 20, 2025
 * Agent: Agent_Preset_Audio
 * Task Reference: Phase 5, Task 5.1 - Workflow Preset System
 */

class PresetManager {
    constructor() {
        this.presets = [];
        this.currentPreset = null;
        this.filteredPresets = [];
        this.statistics = {};
        
        // UI elements
        this.container = document.getElementById('presets-container');
        this.emptyState = document.getElementById('empty-state');
        this.modal = document.getElementById('preset-modal');
        this.deleteModal = document.getElementById('delete-modal');
        this.form = document.getElementById('preset-form');
        
        // Search and filter elements
        this.searchInput = document.getElementById('search-presets');
        this.categoryFilter = document.getElementById('category-filter');
        this.sortSelect = document.getElementById('sort-presets');
        
        // Statistics elements
        this.totalPresetsEl = document.getElementById('total-presets');
        this.totalUsageEl = document.getElementById('total-usage');
        this.mostUsedEl = document.getElementById('most-used-preset');
        this.categoryCountEl = document.getElementById('category-count');
        
        // Initialize
        this.initialize();
    }
    
    async initialize() {
        try {
            this.setupEventListeners();
            await this.loadPresets();
            await this.loadStatistics();
            this.renderPresets();
            
            console.log('🎯 Preset Manager initialized');
        } catch (error) {
            console.error('Failed to initialize preset manager:', error);
            this.showNotification('Failed to load preset manager', 'error');
        }
    }
    
    setupEventListeners() {
        // Create preset button
        document.getElementById('create-preset-btn').addEventListener('click', () => {
            this.openCreateModal();
        });
        
        // Import preset button
        document.getElementById('import-preset-btn').addEventListener('click', () => {
            this.openImportDialog();
        });
        
        // Modal controls
        document.getElementById('cancel-preset').addEventListener('click', () => {
            this.closeModal();
        });
        
        // Delete modal controls
        document.getElementById('cancel-delete').addEventListener('click', () => {
            this.closeDeleteModal();
        });
        
        document.getElementById('confirm-delete').addEventListener('click', () => {
            this.executeDelete();
        });
        
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });
        
        // Search and filter
        this.searchInput.addEventListener('input', () => {
            this.filterPresets();
        });
        
        this.categoryFilter.addEventListener('change', () => {
            this.filterPresets();
        });
        
        this.sortSelect.addEventListener('change', () => {
            this.sortPresets();
        });
        
        // Close modal on backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
        
        this.deleteModal.addEventListener('click', (e) => {
            if (e.target === this.deleteModal) {
                this.closeDeleteModal();
            }
        });
    }
    
    async loadPresets() {
        try {
            const response = await fetch('/presets/api/presets');
            const data = await response.json();
            
            if (data.success) {
                this.presets = data.presets;
                this.filteredPresets = [...this.presets];
                console.log(`📋 Loaded ${this.presets.length} presets`);
            } else {
                throw new Error(data.error || 'Failed to load presets');
            }
        } catch (error) {
            console.error('Failed to load presets:', error);
            this.showNotification('Failed to load presets', 'error');
            this.presets = [];
            this.filteredPresets = [];
        }
    }
    
    async loadStatistics() {
        try {
            const response = await fetch('/presets/api/statistics');
            const data = await response.json();
            
            if (data.success) {
                this.statistics = data.statistics;
                this.updateStatisticsDisplay();
            }
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }
    
    updateStatisticsDisplay() {
        const stats = this.statistics;
        
        this.totalPresetsEl.textContent = stats.total_presets || 0;
        this.totalUsageEl.textContent = stats.usage_stats?.total_usage || 0;
        this.mostUsedEl.textContent = stats.usage_stats?.most_used?.name || 'None';
        this.categoryCountEl.textContent = Object.keys(stats.categories || {}).length;
    }
    
    renderPresets() {
        if (this.filteredPresets.length === 0) {
            this.showEmptyState();
            return;
        }
        
        this.hideEmptyState();
        
        this.container.innerHTML = '';
        
        this.filteredPresets.forEach(preset => {
            const presetCard = this.createPresetCard(preset);
            this.container.appendChild(presetCard);
        });
    }
    
    createPresetCard(preset) {
        const card = document.createElement('div');
        card.className = 'preset-card bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow duration-200';
        
        // Category badge color
        const categoryColors = {
            'system': 'bg-blue-100 text-blue-800',
            'custom': 'bg-green-100 text-green-800',
            'template': 'bg-purple-100 text-purple-800'
        };
        
        const categoryColor = categoryColors[preset.category] || 'bg-gray-100 text-gray-800';
        
        // Stage indicators
        const stageColors = [
            'bg-blue-100 text-blue-800',
            'bg-green-100 text-green-800',
            'bg-yellow-100 text-yellow-800',
            'bg-purple-100 text-purple-800',
            'bg-indigo-100 text-indigo-800',
            'bg-pink-100 text-pink-800',
            'bg-red-100 text-red-800'
        ];
        
        const stageIndicators = (preset.stage_names || []).map((stageName, index) => {
            const stageNum = index + 1;
            const colorClass = stageColors[index] || 'bg-gray-100 text-gray-800';
            return `<span class="stage-indicator ${colorClass}" title="${stageName}">${stageNum}</span>`;
        }).join('');
        
        card.innerHTML = `
            <div class="p-6">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <h3 class="text-lg font-medium text-gray-900">${this.escapeHtml(preset.name)}</h3>
                        <span class="preset-category-badge ${categoryColor}">${preset.category}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button class="text-gray-400 hover:text-primary-600 transition-colors" onclick="presetManager.loadPreset('${preset.preset_id}')" title="Load Preset">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path>
                            </svg>
                        </button>
                        <button class="text-gray-400 hover:text-blue-600 transition-colors" onclick="presetManager.editPreset('${preset.preset_id}')" title="Edit Preset">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                            </svg>
                        </button>
                        <button class="text-gray-400 hover:text-green-600 transition-colors" onclick="presetManager.exportPreset('${preset.preset_id}')" title="Export Preset">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                        </button>
                        <button class="text-gray-400 hover:text-red-600 transition-colors" onclick="presetManager.deletePreset('${preset.preset_id}', '${this.escapeHtml(preset.name)}')" title="Delete Preset">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                
                ${preset.description ? `<p class="mt-2 text-sm text-gray-600">${this.escapeHtml(preset.description)}</p>` : ''}
                
                <div class="mt-4">
                    <div class="flex items-center justify-between text-sm text-gray-500">
                        <span>Pipeline Stages:</span>
                        <span>${(preset.stage_names || []).length} of 7 stages</span>
                    </div>
                    <div class="mt-2 flex flex-wrap gap-1">
                        ${stageIndicators}
                    </div>
                </div>
                
                <div class="mt-4 grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="text-gray-500">Segment Mode:</span>
                        <span class="ml-2 font-medium">${preset.configuration?.segment_mode || 'auto'}</span>
                    </div>
                    <div>
                        <span class="text-gray-500">Audio Method:</span>
                        <span class="ml-2 font-medium">${preset.configuration?.audio_method || 'tts'}</span>
                    </div>
                </div>
                
                <div class="mt-4 flex items-center justify-between">
                    <div class="text-sm text-gray-500">
                        Used ${preset.usage_count || 0} times
                    </div>
                    <button onclick="presetManager.loadPreset('${preset.preset_id}')" class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors">
                        Load Preset
                    </button>
                </div>
            </div>
        `;
        
        return card;
    }
    
    showEmptyState() {
        this.container.style.display = 'none';
        this.emptyState.classList.remove('hidden');
    }
    
    hideEmptyState() {
        this.container.style.display = 'grid';
        this.emptyState.classList.add('hidden');
    }
    
    filterPresets() {
        const searchTerm = this.searchInput.value.toLowerCase();
        const selectedCategory = this.categoryFilter.value;
        
        this.filteredPresets = this.presets.filter(preset => {
            const matchesSearch = !searchTerm || 
                preset.name.toLowerCase().includes(searchTerm) ||
                (preset.description && preset.description.toLowerCase().includes(searchTerm));
            
            const matchesCategory = !selectedCategory || preset.category === selectedCategory;
            
            return matchesSearch && matchesCategory;
        });
        
        this.sortPresets();
    }
    
    sortPresets() {
        const sortBy = this.sortSelect.value;
        
        this.filteredPresets.sort((a, b) => {
            switch (sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'usage':
                    return (b.usage_count || 0) - (a.usage_count || 0);
                case 'created':
                    return new Date(b.created_at) - new Date(a.created_at);
                case 'updated':
                    return new Date(b.updated_at) - new Date(a.updated_at);
                default:
                    return 0;
            }
        });
        
        this.renderPresets();
    }
    
    openCreateModal() {
        this.currentPreset = null;
        this.resetForm();
        document.getElementById('modal-title').textContent = 'Create New Preset';
        this.form.querySelector('button[type="submit"]').textContent = 'Create Preset';
        this.showModal();
    }
    
    async editPreset(presetId) {
        try {
            const response = await fetch(`/presets/api/presets/${presetId}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentPreset = data.preset;
                this.populateForm(data.preset);
                document.getElementById('modal-title').textContent = 'Edit Preset';
                this.form.querySelector('button[type="submit"]').textContent = 'Update Preset';
                this.showModal();
            } else {
                this.showNotification('Failed to load preset for editing', 'error');
            }
        } catch (error) {
            console.error('Failed to load preset:', error);
            this.showNotification('Failed to load preset for editing', 'error');
        }
    }
    
    resetForm() {
        this.form.reset();
        
        // Reset checkboxes and radio buttons
        this.form.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        this.form.querySelectorAll('input[type="radio"]').forEach(rb => rb.checked = false);
        
        // Set defaults
        document.getElementById('segment-auto').checked = true;
        document.getElementById('audio-method').value = 'tts';
        document.getElementById('output-format').value = 'mp4';
        document.getElementById('output-quality').value = 'high';
        document.getElementById('include-subtitles').checked = true;
    }
    
    populateForm(preset) {
        const config = preset.configuration;
        
        // Basic fields
        document.getElementById('preset-name').value = preset.name;
        document.getElementById('preset-description').value = preset.description || '';
        document.getElementById('preset-category').value = preset.category;
        
        // Stage selection
        if (config.stage_selection) {
            config.stage_selection.forEach(stage => {
                const checkbox = document.getElementById(`stage-${stage}`);
                if (checkbox) checkbox.checked = true;
            });
        }
        
        // Segment mode
        if (config.segment_mode) {
            const radio = document.getElementById(`segment-${config.segment_mode}`);
            if (radio) radio.checked = true;
        }
        
        // Audio method
        if (config.audio_method) {
            document.getElementById('audio-method').value = config.audio_method;
        }
        
        // Output settings
        if (config.output_settings) {
            const settings = config.output_settings;
            if (settings.format) {
                document.getElementById('output-format').value = settings.format;
            }
            if (settings.quality) {
                document.getElementById('output-quality').value = settings.quality;
            }
            if (settings.include_subtitles !== undefined) {
                document.getElementById('include-subtitles').checked = settings.include_subtitles;
            }
        }
    }
    
    async handleFormSubmit() {
        try {
            const formData = this.getFormData();
            
            // Validate form data
            const validation = this.validateFormData(formData);
            if (!validation.isValid) {
                this.showNotification(validation.errors.join(', '), 'error');
                return;
            }
            
            const url = this.currentPreset 
                ? `/presets/api/presets/${this.currentPreset.preset_id}`
                : '/presets/api/presets';
            
            const method = this.currentPreset ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(
                    this.currentPreset ? 'Preset updated successfully' : 'Preset created successfully',
                    'success'
                );
                this.closeModal();
                await this.loadPresets();
                await this.loadStatistics();
                this.renderPresets();
            } else {
                this.showNotification(data.error || 'Failed to save preset', 'error');
            }
        } catch (error) {
            console.error('Failed to save preset:', error);
            this.showNotification('Failed to save preset', 'error');
        }
    }
    
    getFormData() {
        const formData = new FormData(this.form);
        
        // Get selected stages
        const stages = Array.from(this.form.querySelectorAll('input[name="stages"]:checked'))
            .map(cb => parseInt(cb.value));
        
        // Get prompt references (simplified for this implementation)
        const promptReferences = {
            content_analysis: 'default_content_analysis.txt',
            segment_selection: formData.get('segment_mode') === 'auto' 
                ? 'auto_segment_selection.txt' 
                : 'manual_segment_selection.txt'
        };
        
        return {
            name: formData.get('name'),
            description: formData.get('description'),
            category: formData.get('category'),
            configuration: {
                stage_selection: stages,
                segment_mode: formData.get('segment_mode'),
                prompt_references: promptReferences,
                audio_method: formData.get('audio_method'),
                output_settings: {
                    format: formData.get('output_format'),
                    quality: formData.get('output_quality'),
                    include_subtitles: formData.has('include_subtitles')
                }
            }
        };
    }
    
    validateFormData(data) {
        const errors = [];
        
        if (!data.name || data.name.trim().length === 0) {
            errors.push('Preset name is required');
        }
        
        if (!data.configuration.stage_selection || data.configuration.stage_selection.length === 0) {
            errors.push('At least one pipeline stage must be selected');
        }
        
        if (!data.configuration.segment_mode) {
            errors.push('Segment mode must be selected');
        }
        
        if (!data.configuration.audio_method) {
            errors.push('Audio method must be selected');
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
    
    async loadPreset(presetId) {
        try {
            const response = await fetch(`/presets/api/presets/${presetId}/load`);
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Preset "${data.preset_name}" loaded successfully`, 'success');
                
                // Integrate with pipeline controller if available
                if (window.YouTubePipelineUI && window.YouTubePipelineUI.pipelineController) {
                    window.YouTubePipelineUI.pipelineController.applyPresetConfiguration(data.configuration);
                }
                
                // Broadcast preset load event
                if (window.YouTubePipelineUI && window.YouTubePipelineUI.socketClient) {
                    window.YouTubePipelineUI.socketClient.emit('preset_loaded', {
                        preset_id: presetId,
                        preset_name: data.preset_name,
                        configuration: data.configuration
                    });
                }
                
                // Update statistics
                await this.loadStatistics();
                
            } else {
                this.showNotification('Failed to load preset', 'error');
            }
        } catch (error) {
            console.error('Failed to load preset:', error);
            this.showNotification('Failed to load preset', 'error');
        }
    }
    
    deletePreset(presetId, presetName) {
        this.presetToDelete = { id: presetId, name: presetName };
        document.getElementById('delete-preset-name').textContent = presetName;
        this.showDeleteModal();
    }
    
    async executeDelete() {
        if (!this.presetToDelete) return;
        
        try {
            const response = await fetch(`/presets/api/presets/${this.presetToDelete.id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Preset "${this.presetToDelete.name}" deleted successfully`, 'success');
                this.closeDeleteModal();
                await this.loadPresets();
                await this.loadStatistics();
                this.renderPresets();
            } else {
                this.showNotification('Failed to delete preset', 'error');
            }
        } catch (error) {
            console.error('Failed to delete preset:', error);
            this.showNotification('Failed to delete preset', 'error');
        }
        
        this.presetToDelete = null;
    }
    
    async exportPreset(presetId) {
        try {
            const response = await fetch(`/presets/api/presets/${presetId}/export`);
            const data = await response.json();
            
            if (data.success) {
                // Create download link
                const blob = new Blob([JSON.stringify(data.preset_data, null, 2)], 
                    { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${data.preset_data.name.replace(/[^a-z0-9]/gi, '_')}_preset.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.showNotification('Preset exported successfully', 'success');
            } else {
                this.showNotification('Failed to export preset', 'error');
            }
        } catch (error) {
            console.error('Failed to export preset:', error);
            this.showNotification('Failed to export preset', 'error');
        }
    }
    
    openImportDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.style.display = 'none';
        
        input.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.importPreset(file);
            }
        });
        
        document.body.appendChild(input);
        input.click();
        document.body.removeChild(input);
    }
    
    async importPreset(file) {
        try {
            const text = await file.text();
            const presetData = JSON.parse(text);
            
            const response = await fetch('/presets/api/presets/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ preset_data: presetData })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Preset imported successfully', 'success');
                await this.loadPresets();
                await this.loadStatistics();
                this.renderPresets();
            } else {
                this.showNotification(data.error || 'Failed to import preset', 'error');
            }
        } catch (error) {
            console.error('Failed to import preset:', error);
            this.showNotification('Failed to import preset - invalid file format', 'error');
        }
    }
    
    showModal() {
        this.modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
    
    closeModal() {
        this.modal.classList.add('hidden');
        document.body.style.overflow = '';
        this.currentPreset = null;
    }
    
    showDeleteModal() {
        this.deleteModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
    
    closeDeleteModal() {
        this.deleteModal.classList.add('hidden');
        document.body.style.overflow = '';
        this.presetToDelete = null;
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notification-container');
        
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const notification = document.createElement('div');
        notification.className = `${colors[type]} text-white p-4 rounded-lg shadow-lg mb-4 flex items-center space-x-3 transform transition-all duration-300 translate-x-full`;
        
        notification.innerHTML = `
            <span class="text-lg">${icons[type]}</span>
            <span class="flex-1">${this.escapeHtml(message)}</span>
            <button class="text-white hover:text-gray-200" onclick="this.parentElement.remove()">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        
        container.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, duration);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize preset manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.presetManager = new PresetManager();
    
    // Register with global UI system if available
    if (window.YouTubePipelineUI) {
        window.YouTubePipelineUI.presetManager = window.presetManager;
    }
    
    console.log('🎯 Preset Management System ready');
});
