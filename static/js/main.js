/**
 * Main JavaScript file for Document Research Chatbot
 * Handles global functionality, utilities, and UI enhancements
 */

// Global configuration
const CONFIG = {
    API_ENDPOINTS: {
        SYSTEM_STATS: '/api/system-stats',
        DOCUMENT_STATUS: '/api/document-status'
    },
    REFRESH_INTERVALS: {
        SYSTEM_STATS: 10000, // 10 seconds
        DOCUMENT_STATUS: 5000 // 5 seconds
    },
    UPLOAD: {
        MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
        ALLOWED_EXTENSIONS: ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'txt', 'docx']
    }
};

// Global state management
const AppState = {
    processingDocuments: new Set(),
    systemStats: {},
    isOnline: navigator.onLine
};

/**
 * Utility Functions
 */
const Utils = {
    /**
     * Format file size to human readable format
     */
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Get file extension from filename
     */
    getFileExtension: function(filename) {
        return filename.split('.').pop().toLowerCase();
    },

    /**
     * Check if file is allowed
     */
    isFileAllowed: function(filename) {
        const ext = this.getFileExtension(filename);
        return CONFIG.UPLOAD.ALLOWED_EXTENSIONS.includes(ext);
    },

    /**
     * Get appropriate icon for file type
     */
    getFileIcon: function(filename) {
        const ext = this.getFileExtension(filename);
        switch (ext) {
            case 'pdf': return 'fa-file-pdf';
            case 'png':
            case 'jpg':
            case 'jpeg':
            case 'tiff':
            case 'bmp': return 'fa-file-image';
            case 'txt':
            case 'docx': return 'fa-file-alt';
            default: return 'fa-file';
        }
    },

    /**
     * Get color class for file type
     */
    getFileColor: function(filename) {
        const ext = this.getFileExtension(filename);
        switch (ext) {
            case 'pdf': return 'text-danger';
            case 'png':
            case 'jpg':
            case 'jpeg':
            case 'tiff':
            case 'bmp': return 'text-info';
            case 'txt':
            case 'docx': return 'text-secondary';
            default: return 'text-muted';
        }
    },

    /**
     * Debounce function for performance optimization
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info', duration = 5000) {
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to page
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1100';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);

        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    /**
     * Copy text to clipboard
     */
    copyToClipboard: async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard!', 'success');
            return true;
        } catch (err) {
            console.error('Failed to copy text: ', err);
            this.showToast('Failed to copy to clipboard', 'error');
            return false;
        }
    },

    /**
     * Format date for display
     */
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    },

    /**
     * Validate file before upload
     */
    validateFile: function(file) {
        const errors = [];
        
        if (!this.isFileAllowed(file.name)) {
            errors.push(`File type not supported: ${this.getFileExtension(file.name)}`);
        }
        
        if (file.size > CONFIG.UPLOAD.MAX_FILE_SIZE) {
            errors.push(`File too large: ${this.formatFileSize(file.size)} (max: ${this.formatFileSize(CONFIG.UPLOAD.MAX_FILE_SIZE)})`);
        }
        
        return errors;
    }
};

/**
 * API Service for backend communication
 */
const API = {
    /**
     * Generic fetch wrapper with error handling
     */
    async fetch(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    /**
     * Get system statistics
     */
    async getSystemStats() {
        try {
            const stats = await this.fetch(CONFIG.API_ENDPOINTS.SYSTEM_STATS);
            AppState.systemStats = stats;
            return stats;
        } catch (error) {
            console.error('Failed to fetch system stats:', error);
            Utils.showToast('Failed to update system statistics', 'error');
            return null;
        }
    },

    /**
     * Get document processing status
     */
    async getDocumentStatus(documentId) {
        try {
            return await this.fetch(`${CONFIG.API_ENDPOINTS.DOCUMENT_STATUS}/${documentId}`);
        } catch (error) {
            console.error('Failed to fetch document status:', error);
            return null;
        }
    }
};

/**
 * File Upload Handler
 */
const FileUpload = {
    /**
     * Initialize drag and drop functionality
     */
    initDragDrop: function(dropZone, fileInput) {
        if (!dropZone || !fileInput) return;

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => this.highlight(dropZone), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => this.unhighlight(dropZone), false);
        });

        // Handle dropped files
        dropZone.addEventListener('drop', (e) => this.handleDrop(e, fileInput), false);
        
        // Handle click to open file dialog
        dropZone.addEventListener('click', () => fileInput.click());
    },

    preventDefaults: function(e) {
        e.preventDefault();
        e.stopPropagation();
    },

    highlight: function(dropZone) {
        dropZone.classList.add('border-primary', 'bg-primary', 'bg-opacity-10');
    },

    unhighlight: function(dropZone) {
        dropZone.classList.remove('border-primary', 'bg-primary', 'bg-opacity-10');
    },

    handleDrop: function(e, fileInput) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        // Set files to input element
        fileInput.files = files;
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
    },

    /**
     * Validate files before upload
     */
    validateFiles: function(files) {
        const validFiles = [];
        const errors = [];

        Array.from(files).forEach(file => {
            const fileErrors = Utils.validateFile(file);
            if (fileErrors.length === 0) {
                validFiles.push(file);
            } else {
                errors.push(`${file.name}: ${fileErrors.join(', ')}`);
            }
        });

        return { validFiles, errors };
    },

    /**
     * Create file preview element
     */
    createFilePreview: function(file) {
        const previewItem = document.createElement('div');
        previewItem.className = 'list-group-item d-flex justify-content-between align-items-center';
        
        previewItem.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${Utils.getFileIcon(file.name)} fa-lg ${Utils.getFileColor(file.name)} me-3"></i>
                <div>
                    <div class="fw-semibold">${file.name}</div>
                    <small class="text-muted">${Utils.formatFileSize(file.size)}</small>
                </div>
            </div>
            <span class="badge bg-info">Ready</span>
        `;
        
        return previewItem;
    }
};

/**
 * UI Enhancement Functions
 */
const UI = {
    /**
     * Initialize tooltips
     */
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    /**
     * Initialize popovers
     */
    initPopovers: function() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },

    /**
     * Auto-resize textareas
     */
    initAutoResize: function() {
        const textareas = document.querySelectorAll('textarea[data-auto-resize]');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        });
    },

    /**
     * Initialize search functionality
     */
    initSearch: function(searchInput, searchTargets) {
        if (!searchInput) return;

        const debouncedSearch = Utils.debounce((searchTerm) => {
            this.performSearch(searchTerm, searchTargets);
        }, 300);

        searchInput.addEventListener('input', (e) => {
            debouncedSearch(e.target.value.toLowerCase());
        });
    },

    performSearch: function(searchTerm, targets) {
        targets.forEach(target => {
            const text = target.textContent.toLowerCase();
            const visible = text.includes(searchTerm);
            target.style.display = visible ? '' : 'none';
        });
    },

    /**
     * Update processing indicators
     */
    updateProcessingIndicators: function() {
        const processingElements = document.querySelectorAll('[data-processing]');
        processingElements.forEach(element => {
            const docId = element.getAttribute('data-doc-id');
            if (AppState.processingDocuments.has(docId)) {
                element.classList.add('processing-indicator');
            } else {
                element.classList.remove('processing-indicator');
            }
        });
    },

    /**
     * Animate numbers (counting effect)
     */
    animateNumber: function(element, endValue, duration = 1000) {
        const startValue = parseInt(element.textContent) || 0;
        const range = endValue - startValue;
        const increment = endValue > startValue ? 1 : -1;
        const stepTime = Math.abs(Math.floor(duration / range));
        
        let current = startValue;
        const timer = setInterval(() => {
            current += increment;
            element.textContent = current;
            
            if (current === endValue) {
                clearInterval(timer);
            }
        }, stepTime);
    }
};

/**
 * Application Initialization
 */
const App = {
    /**
     * Initialize the application
     */
    init: function() {
        console.log('Initializing Document Research Chatbot...');
        
        // Initialize UI components
        this.initUIComponents();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        // Check online status
        this.setupConnectivityMonitoring();
        
        console.log('Application initialized successfully');
    },

    initUIComponents: function() {
        UI.initTooltips();
        UI.initPopovers();
        UI.initAutoResize();
        
        // Initialize file upload if on upload page
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('files');
        if (dropZone && fileInput) {
            FileUpload.initDragDrop(dropZone, fileInput);
        }
        
        // Initialize search if search input exists
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            const searchTargets = document.querySelectorAll('.document-row, .query-item');
            UI.initSearch(searchInput, searchTargets);
        }
    },

    setupEventListeners: function() {
        // Global error handling
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            Utils.showToast('An unexpected error occurred', 'error');
        });

        // Handle form submissions with loading states
        document.addEventListener('submit', (event) => {
            const form = event.target;
            if (form.tagName === 'FORM') {
                this.handleFormSubmission(form);
            }
        });

        // Handle copy buttons
        document.addEventListener('click', (event) => {
            if (event.target.matches('[data-copy]')) {
                const text = event.target.getAttribute('data-copy');
                Utils.copyToClipboard(text);
            }
        });
    },

    handleFormSubmission: function(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Processing...';
            
            // Re-enable after 5 seconds as fallback
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Submit';
            }, 5000);
        }
    },

    startPeriodicUpdates: function() {
        // Update system stats periodically
        setInterval(async () => {
            if (AppState.isOnline) {
                await API.getSystemStats();
                this.updateSystemStatsDisplay();
            }
        }, CONFIG.REFRESH_INTERVALS.SYSTEM_STATS);

        // Update document status for processing documents
        setInterval(async () => {
            if (AppState.isOnline && AppState.processingDocuments.size > 0) {
                await this.checkProcessingDocuments();
            }
        }, CONFIG.REFRESH_INTERVALS.DOCUMENT_STATUS);
    },

    async checkProcessingDocuments() {
        const promises = Array.from(AppState.processingDocuments).map(async (docId) => {
            const status = await API.getDocumentStatus(docId);
            if (status && status.status !== 'processing') {
                AppState.processingDocuments.delete(docId);
                this.updateDocumentStatusDisplay(docId, status);
            }
        });
        
        await Promise.all(promises);
        UI.updateProcessingIndicators();
    },

    updateSystemStatsDisplay: function() {
        const stats = AppState.systemStats;
        if (!stats) return;

        // Update stat displays
        const statElements = {
            'totalDocs': stats.total_documents,
            'processedDocs': stats.processed_documents,
            'processingDocs': stats.processing_documents,
            'failedDocs': stats.failed_documents,
            'processing-count': stats.processing_documents
        };

        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                const currentValue = parseInt(element.textContent) || 0;
                if (currentValue !== value) {
                    UI.animateNumber(element, value);
                }
            }
        });
    },

    updateDocumentStatusDisplay: function(docId, status) {
        const row = document.querySelector(`[data-doc-id="${docId}"]`);
        if (!row) return;

        const statusBadge = row.querySelector('.badge');
        if (statusBadge) {
            statusBadge.className = `badge bg-${status.status === 'completed' ? 'success' : 'danger'}`;
            statusBadge.textContent = status.status === 'completed' ? 'Completed' : 'Failed';
        }

        if (status.status === 'completed') {
            Utils.showToast(`Document "${status.filename}" processed successfully`, 'success');
        } else if (status.status === 'failed') {
            Utils.showToast(`Document "${status.filename}" failed to process`, 'error');
        }
    },

    setupConnectivityMonitoring: function() {
        window.addEventListener('online', () => {
            AppState.isOnline = true;
            Utils.showToast('Connection restored', 'success');
        });

        window.addEventListener('offline', () => {
            AppState.isOnline = false;
            Utils.showToast('Connection lost - some features may be unavailable', 'warning');
        });
    }
};

/**
 * Initialize application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

/**
 * Export utilities for use in other scripts
 */
window.ChatbotUtils = Utils;
window.ChatbotAPI = API;
window.ChatbotUI = UI;
