class WebinarDirectory {
    constructor() {
        this.webinars = [];
        this.filteredWebinars = [];
        this.currentSort = { field: 'date_added', direction: 'desc' };
        this.filters = {
            search: '',
            provider: '',
            topic: '',
            format: '',
            duration: '',
            certificate: '',
            date: '',
            liked: ''
        };
        this.dataModified = false;
        
        this.init();
    }

    // Security functions
    sanitizeInput(input) {
        if (typeof input !== 'string') return '';
        return input.replace(/[<>]/g, '').trim();
    }

    validateWebinarData(webinar) {
        const required = ['id', 'title', 'provider', 'url'];
        for (const field of required) {
            if (!webinar[field]) {
                console.error(`Missing required field: ${field}`);
                return false;
            }
        }
        
        // Validate URL format
        try {
            new URL(webinar.url);
        } catch {
            console.error('Invalid URL format');
            return false;
        }
        
        return true;
    }

    logSecurityEvent(event, details) {
        console.warn(`Security Event: ${event}`, details);
        // In production, send to monitoring service
    }

    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.populateFilters();
        this.renderTable();
        this.updateResultsInfo();
        this.updateFooterInfo();
        this.handleUrlParameters();
    }

    async loadData() {
        try {
            // Smart caching: use last_updated timestamp for cache busting
            // This way we only bypass cache when data actually changes
            const response = await fetch('webinars.json');
            const data = await response.json();
            
            // Check if we need to bypass cache (if last_updated changed)
            const lastUpdated = data.last_updated;
            const cachedLastUpdated = localStorage.getItem('webinar_last_updated');
            
            if (cachedLastUpdated !== lastUpdated) {
                // Data has changed, reload with cache busting
                const timestamp = new Date().getTime();
                const freshResponse = await fetch(`webinars.json?t=${timestamp}`, {
                    cache: 'no-cache'
                });
                const freshData = await freshResponse.json();
                // Validate webinar data
                const validWebinars = (freshData.webinars || []).filter(webinar => {
                    if (!this.validateWebinarData(webinar)) {
                        this.logSecurityEvent('Invalid webinar data', { id: webinar.id, title: webinar.title });
                        return false;
                    }
                    return true;
                });
                this.webinars = validWebinars;
                localStorage.setItem('webinar_last_updated', lastUpdated);
            } else {
                // Use cached data
                const validWebinars = (data.webinars || []).filter(webinar => {
                    if (!this.validateWebinarData(webinar)) {
                        this.logSecurityEvent('Invalid cached webinar data', { id: webinar.id, title: webinar.title });
                        return false;
                    }
                    return true;
                });
                this.webinars = validWebinars;
            }
            
            // Integrate pending webinars from localStorage
            this.integratePendingWebinars();
            
            // Migrate existing likes from localStorage to webinar data
            this.migrateLikesFromLocalStorage();
            
            this.filteredWebinars = [...this.webinars];
            
            // Update footer info with current data
            this.updateFooterInfo();
        } catch (error) {
            console.error('Error loading webinar data:', error);
            // Fallback to sample data for development
            this.webinars = [
                {
                    "id": "labroots-2025-cgt",
                    "title": "Cell & Gene Therapy 2025 Virtual Event",
                    "provider": "Labroots",
                    "topics": ["cell-therapy", "regulatory", "gene-therapy"],
                    "format": "on-demand",
                    "duration_min": 60,
                    "certificate_available": true,
                    "certificate_process": "Auto-issued after quiz completion",
                    "date_added": "2025-01-15",
                    "url": "https://www.labroots.com/virtual-event/cell-gene-therapy-2025",
                    "description": "Comprehensive overview of latest developments in cell and gene therapy, including regulatory considerations and clinical applications."
                }
            ];
            this.filteredWebinars = [...this.webinars];
            this.updateFooterInfo();
        }
    }

    integratePendingWebinars() {
        const pendingWebinars = JSON.parse(localStorage.getItem('pendingWebinars') || '[]');
        if (pendingWebinars.length > 0) {
            // Add pending webinars to the main array
            this.webinars = [...this.webinars, ...pendingWebinars];
            
            // Mark data as modified
            this.dataModified = true;
            
            // Clear pending webinars from localStorage
            localStorage.removeItem('pendingWebinars');
            
            // Update footer with new data
            this.updateFooterInfo();
            
            // Show notification
            this.showToast(`${pendingWebinars.length} new webinar(s) added!`, 'success');
        }
    }

    migrateLikesFromLocalStorage() {
        const oldLikes = JSON.parse(localStorage.getItem('webinar_likes') || '{}');
        let migratedCount = 0;
        
        // Migrate old likes to webinar data
        Object.keys(oldLikes).forEach(webinarId => {
            const webinar = this.webinars.find(w => w.id === webinarId);
            if (webinar && oldLikes[webinarId] > 0) {
                webinar.likes = (webinar.likes || 0) + oldLikes[webinarId];
                migratedCount += oldLikes[webinarId];
            }
        });
        
        if (migratedCount > 0) {
            // Mark data as modified
            this.dataModified = true;
            
            // Clear old likes from localStorage
            localStorage.removeItem('webinar_likes');
            
            console.log(`Migrated ${migratedCount} likes from localStorage to webinar data`);
        }
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const clearSearch = document.getElementById('clearSearch');
        
        searchInput.addEventListener('input', (e) => {
            this.filters.search = this.sanitizeInput(e.target.value);
            this.applyFilters();
        });
        
        clearSearch.addEventListener('click', () => {
            searchInput.value = '';
            this.filters.search = '';
            this.applyFilters();
        });

        // Filter dropdowns
        const filterSelects = ['providerFilter', 'topicFilter', 'formatFilter', 'durationFilter', 'certificateFilter', 'dateFilter', 'likedFilter'];
        filterSelects.forEach(id => {
            document.getElementById(id).addEventListener('change', (e) => {
                this.filters[id.replace('Filter', '')] = e.target.value;
                this.applyFilters();
            });
        });

        // Reset filters
        document.getElementById('resetFilters').addEventListener('click', () => {
            this.resetFilters();
        });

        // Table sorting
        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                this.sortTable(th.dataset.sort);
            });
        });

        // Certificate modal
        this.setupModal();
    }

    populateFilters() {
        // Get unique values for filter dropdowns
        const providers = [...new Set(this.webinars.map(w => w.provider))].sort();
        const topics = [...new Set(this.webinars.flatMap(w => w.topics))].sort();
        
        // Populate provider filter
        const providerFilter = document.getElementById('providerFilter');
        providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider;
            option.textContent = provider;
            providerFilter.appendChild(option);
        });

        // Populate topic filter
        const topicFilter = document.getElementById('topicFilter');
        topics.forEach(topic => {
            const option = document.createElement('option');
            option.value = topic;
            option.textContent = topic.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
            topicFilter.appendChild(option);
        });
    }

    applyFilters() {
        this.filteredWebinars = this.webinars.filter(webinar => {
            // Search filter
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                const searchableText = `${webinar.title} ${webinar.description} ${webinar.topics.join(' ')}`.toLowerCase();
                if (!searchableText.includes(searchTerm)) return false;
            }

            // Provider filter
            if (this.filters.provider && webinar.provider !== this.filters.provider) return false;

            // Topic filter
            if (this.filters.topic && !webinar.topics.includes(this.filters.topic)) return false;

            // Format filter
            if (this.filters.format && webinar.format !== this.filters.format) return false;

            // Duration filter
            if (this.filters.duration) {
                const duration = webinar.duration_min;
                switch (this.filters.duration) {
                    case '0-30': if (duration > 30) return false; break;
                    case '31-60': if (duration < 31 || duration > 60) return false; break;
                    case '61-90': if (duration < 61 || duration > 90) return false; break;
                    case '91+': if (duration < 91) return false; break;
                }
            }

            // Certificate filter
            if (this.filters.certificate && webinar.certificate_available.toString() !== this.filters.certificate) return false;

            // Date filter
            if (this.filters.date) {
                if (this.filters.date === 'live') {
                    if (webinar.format !== 'live') return false;
                } else if (this.filters.date === 'on-demand') {
                    if (webinar.format !== 'on-demand') return false;
                } else if (this.filters.date === 'upcoming') {
                    if (webinar.format !== 'live') return false;
                    if (!webinar.live_date || webinar.live_date === 'on-demand' || webinar.live_date === 'Unknown') return false;
                    const now = new Date();
                    const date = new Date(webinar.live_date);
                    const diffDays = (date - now) / (1000 * 60 * 60 * 24);
                    if (isNaN(date.getTime()) || diffDays < 0 || diffDays > 30) return false;
                }
            }

            // Liked filter
            if (this.filters.liked === 'liked') {
                if (!this.isWebinarLiked(webinar.id)) return false;
            }

            return true;
        });

        this.renderTable();
        this.updateResultsInfo();
    }

    resetFilters() {
        // Reset all filter values
        this.filters = {
            search: '',
            provider: '',
            topic: '',
            format: '',
            duration: '',
            certificate: '',
            date: '',
            liked: ''
        };

        // Reset UI
        document.getElementById('searchInput').value = '';
        document.getElementById('providerFilter').value = '';
        document.getElementById('topicFilter').value = '';
        document.getElementById('formatFilter').value = '';
        document.getElementById('durationFilter').value = '';
        document.getElementById('certificateFilter').value = '';
        document.getElementById('dateFilter').value = '';
        document.getElementById('likedFilter').value = '';

        // Reset data
        this.filteredWebinars = [...this.webinars];
        this.renderTable();
        this.updateResultsInfo();
    }

    sortTable(field) {
        const direction = this.currentSort.field === field && this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        this.currentSort = { field, direction };

        this.filteredWebinars.sort((a, b) => {
            let aVal = a[field];
            let bVal = b[field];

            // Handle special cases
            if (field === 'topics') {
                aVal = aVal.join(', ');
                bVal = bVal.join(', ');
            } else if (field === 'likes') {
                // Handle likes sorting
                aVal = this.getLikeCount(a.id);
                bVal = this.getLikeCount(b.id);
            }

            // Handle live_date sorting
            if (field === 'live_date') {
                // Convert dates to comparable values
                const getDateValue = (val) => {
                    if (!val || val === 'on-demand' || val === 'Unknown') return 0;
                    try {
                        return new Date(val).getTime();
                    } catch (e) {
                        return 0;
                    }
                };
                aVal = getDateValue(aVal);
                bVal = getDateValue(bVal);
            } else if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }

            if (aVal < bVal) return direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return direction === 'asc' ? 1 : -1;
            return 0;
        });

        this.renderTable();
        this.updateSortIndicators();
    }

    updateSortIndicators() {
        document.querySelectorAll('th[data-sort] i').forEach(icon => {
            icon.className = 'fas fa-sort';
        });

        const currentHeader = document.querySelector(`th[data-sort="${this.currentSort.field}"] i`);
        if (currentHeader) {
            currentHeader.className = `fas fa-sort-${this.currentSort.direction === 'asc' ? 'up' : 'down'}`;
        }
    }

    renderTable() {
        const tbody = document.getElementById('webinarsTableBody');
        const noResults = document.getElementById('noResults');

        if (this.filteredWebinars.length === 0) {
            tbody.innerHTML = '';
            noResults.style.display = 'block';
            return;
        }

        noResults.style.display = 'none';
        tbody.innerHTML = this.filteredWebinars.map(webinar => this.createTableRow(webinar)).join('');
    }

    createTableRow(webinar) {
        const topics = webinar.topics.map(topic => 
            `<span class="topic-tag">${topic.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>`
        ).join('');

        const certificateBadge = webinar.certificate_available 
            ? `<span class="certificate-badge available" onclick="webinarDirectory.showCertificateInfo('${webinar.id}')">
                 <i class="fas fa-certificate"></i> Available
               </span>`
            : `<span class="certificate-badge not-available">
                 <i class="fas fa-times-circle"></i> Not Available
               </span>`;

        // Format the date for display - fix timezone issues by parsing date manually
        let dateDisplay = 'On-Demand';
        if (webinar.live_date && webinar.live_date !== 'on-demand' && webinar.live_date !== 'Unknown') {
            try {
                // Parse date manually to avoid timezone issues
                const dateParts = webinar.live_date.split('-');
                if (dateParts.length === 3) {
                    const year = parseInt(dateParts[0]);
                    const month = parseInt(dateParts[1]) - 1; // Month is 0-indexed
                    const day = parseInt(dateParts[2]);
                    
                    // Create date in local timezone to avoid conversion issues
                    const date = new Date(year, month, day);
                    if (!isNaN(date.getTime())) {
                        dateDisplay = date.toLocaleDateString('en-US', { 
                            year: 'numeric', 
                            month: 'short', 
                            day: 'numeric' 
                        });
                    }
                } else {
                    dateDisplay = webinar.live_date;
                }
            } catch (e) {
                dateDisplay = webinar.live_date;
            }
        }

        // Get like count for this webinar
        const likeCount = this.getLikeCount(webinar.id);
        const isLiked = this.isWebinarLiked(webinar.id);

        return `
            <tr data-id="${webinar.id}">
                <td>
                    <div class="webinar-title">
                        <strong>${webinar.title}</strong>
                        <div class="webinar-description">${webinar.description}</div>
                    </div>
                </td>
                <td>${webinar.provider}</td>
                <td><div class="topic-tags">${topics}</div></td>
                <td>${webinar.format.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                <td>${dateDisplay}</td>
                <td>${webinar.duration_min} min</td>
                <td>${certificateBadge}</td>
                <td>
                    <div class="likes-column">
                        <span class="like-count-display">${likeCount}</span>
                        <button class="btn btn-like ${isLiked ? 'liked' : ''}" onclick="webinarDirectory.toggleLike('${webinar.id}')" title="${isLiked ? 'Unlike' : 'Like'} this webinar">
                            <i class="fas fa-heart"></i>
                        </button>
                    </div>
                </td>
                <td>
                    <div class="action-buttons">
                        <a href="${webinar.url}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt"></i> View
                        </a>
                        <button class="btn btn-secondary" onclick="webinarDirectory.copyLink('${webinar.id}', event)">
                            <i class="fas fa-link"></i> Copy Link
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    updateResultsInfo() {
        const count = this.filteredWebinars.length;
        const total = this.webinars.length;
        document.getElementById('resultsCount').textContent = 
            `Showing ${count} of ${total} webinars`;
    }

    setupModal() {
        const modal = document.getElementById('certificateModal');
        const closeBtn = document.querySelector('.close');

        closeBtn.onclick = () => modal.style.display = 'none';
        window.onclick = (event) => {
            if (event.target === modal) modal.style.display = 'none';
        };
    }

    showCertificateInfo(webinarId) {
        const webinar = this.webinars.find(w => w.id === webinarId);
        if (!webinar) return;

        const modal = document.getElementById('certificateModal');
        const details = document.getElementById('certificateDetails');

        details.innerHTML = `
            <h4>${webinar.title}</h4>
            <p><strong>Provider:</strong> ${webinar.provider}</p>
            <p><strong>Certificate Process:</strong> ${webinar.certificate_process}</p>
            <p><strong>Duration:</strong> ${webinar.duration_min} minutes</p>
            <p><strong>Format:</strong> ${webinar.format}</p>
        `;

        modal.style.display = 'block';
    }

    copyLink(webinarId, event) {
        const webinar = this.webinars.find(w => w.id === webinarId);
        if (!webinar) return;

        const url = webinar.url;
        
        // Get the button that was clicked
        const button = event.target.closest('.btn');
        
        // Try modern clipboard API first
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(url).then(() => {
                this.showCopySuccess(button);
            }).catch(err => {
                console.error('Failed to copy link:', err);
                this.fallbackCopy(url, button);
            });
        } else {
            // Fallback for non-secure contexts (like localhost)
            this.fallbackCopy(url, button);
        }
    }

    fallbackCopy(text, button) {
        // Create a temporary textarea element
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-999999px';
        textarea.style.top = '-999999px';
        document.body.appendChild(textarea);
        
        // Select and copy the text
        textarea.focus();
        textarea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                this.showCopySuccess(button);
            } else {
                this.showCopyError(text, button);
            }
        } catch (err) {
            console.error('Fallback copy failed:', err);
            this.showCopyError(text, button);
        }
        
        // Clean up
        document.body.removeChild(textarea);
    }

    showCopySuccess(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Copied!';
        button.style.background = '#28a745';
        
        // Show a small toast notification
        this.showToast('Link copied to clipboard!', 'success');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '';
        }, 2000);
    }

    showToast(message, type = 'info') {
        // Remove any existing toast
        const existingToast = document.querySelector('.toast-notification');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add styles
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : '#17a2b8'};
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            animation: slideIn 0.3s ease-out;
        `;
        
        // Add animation styles if not already present
        if (!document.querySelector('#toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(toast);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }, 3000);
    }

    showCopyError(text, button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Failed';
        button.style.background = '#dc3545';
        
        // Show the URL in an alert for manual copying
        alert('Failed to copy link. Please copy manually: ' + text);
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '';
        }, 2000);
    }

    editWebinar(webinarId) {
        const webinar = this.webinars.find(w => w.id === webinarId);
        if (!webinar) {
            this.showToast('Webinar not found', 'error');
            return;
        }

        // Store the webinar being edited
        this.editingWebinar = webinar;
        
        // Show edit modal
        this.showEditModal(webinar);
    }

    showEditModal(webinar) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('editModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'editModal';
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 800px; max-height: 90vh; overflow-y: auto;">
                    <span class="close">&times;</span>
                    <h3><i class="fas fa-edit"></i> Edit Webinar</h3>
                    <form id="editForm">
                        <div class="form-group">
                            <label for="editTitle">Title *</label>
                            <input type="text" id="editTitle" name="title" required>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="editProvider">Provider *</label>
                                <select id="editProvider" name="provider" required>
                                    <option value="">Select Provider</option>
                                    <option value="Labroots">Labroots</option>
                                    <option value="FDA CDER">FDA CDER</option>
                                    <option value="ASGCT">ASGCT</option>
                                    <option value="PELOBIOTECH">PELOBIOTECH</option>
                                    <option value="ISPE">ISPE</option>
                                    <option value="BioProcess International">BioProcess International</option>
                                    <option value="AABB">AABB</option>
                                    <option value="USP">USP</option>
                                    <option value="PDA">PDA</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="editFormat">Format *</label>
                                <select id="editFormat" name="format" required>
                                    <option value="">Select Format</option>
                                    <option value="on-demand">On-Demand</option>
                                    <option value="live">Live</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="editDuration">Duration (minutes) *</label>
                                <input type="number" id="editDuration" name="duration" min="1" max="480" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="editCertificate">Certificate Available *</label>
                                <select id="editCertificate" name="certificate" required>
                                    <option value="">Select</option>
                                    <option value="true">Yes</option>
                                    <option value="false">No</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="editCertificateProcess">Certificate Process</label>
                            <textarea id="editCertificateProcess" name="certificateProcess" rows="3"></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="editUrl">URL *</label>
                            <input type="url" id="editUrl" name="url" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="editTopics">Topics</label>
                            <div class="topics-input" id="editTopicsContainer">
                                <input type="text" id="editTopicInput" placeholder="Type a topic and press Enter">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="editDescription">Description</label>
                            <textarea id="editDescription" name="description" rows="4"></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="editLiveDate">Live Date</label>
                            <input type="date" id="editLiveDate" name="liveDate">
                        </div>
                        
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Save Changes
                            </button>
                            <button type="button" class="btn btn-secondary" onclick="webinarDirectory.closeEditModal()">
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Setup modal close functionality
            const closeBtn = modal.querySelector('.close');
            closeBtn.onclick = () => this.closeEditModal();
            window.onclick = (event) => {
                if (event.target === modal) this.closeEditModal();
            };
            
            // Setup form submission
            const form = modal.querySelector('#editForm');
            form.onsubmit = (e) => {
                e.preventDefault();
                this.saveWebinarChanges();
            };
            
            // Setup topics input
            this.setupTopicsInput('editTopicInput', 'editTopicsContainer');
        }
        
        // Populate form with current data
        document.getElementById('editTitle').value = webinar.title;
        document.getElementById('editProvider').value = webinar.provider;
        document.getElementById('editFormat').value = webinar.format;
        document.getElementById('editDuration').value = webinar.duration_min;
        document.getElementById('editCertificate').value = webinar.certificate_available.toString();
        document.getElementById('editCertificateProcess').value = webinar.certificate_process || '';
        document.getElementById('editUrl').value = webinar.url;
        document.getElementById('editDescription').value = webinar.description || '';
        
        // Handle live date
        if (webinar.live_date && webinar.live_date !== 'on-demand' && webinar.live_date !== 'Unknown') {
            document.getElementById('editLiveDate').value = webinar.live_date;
        } else {
            document.getElementById('editLiveDate').value = '';
        }
        
        // Populate topics
        const topicsContainer = document.getElementById('editTopicsContainer');
        topicsContainer.innerHTML = '<input type="text" id="editTopicInput" placeholder="Type a topic and press Enter">';
        webinar.topics.forEach(topic => {
            const tag = document.createElement('span');
            tag.className = 'topic-tag';
            tag.innerHTML = `${topic} <span class="remove" onclick="this.parentElement.remove()">&times;</span>`;
            topicsContainer.appendChild(tag);
        });
        
        modal.style.display = 'block';
    }

    setupTopicsInput(inputId, containerId) {
        const input = document.getElementById(inputId);
        const container = document.getElementById(containerId);
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const topic = input.value.trim();
                if (topic) {
                    const tag = document.createElement('span');
                    tag.className = 'topic-tag';
                    tag.innerHTML = `${topic} <span class="remove" onclick="this.parentElement.remove()">&times;</span>`;
                    container.appendChild(tag);
                    input.value = '';
                }
            }
        });
    }

    saveWebinarChanges() {
        const form = document.getElementById('editForm');
        const formData = new FormData(form);
        
        // Get topics from tags
        const topicTags = document.querySelectorAll('#editTopicsContainer .topic-tag');
        const topics = Array.from(topicTags).map(tag => tag.textContent.replace('×', '').trim());
        
        // Update the webinar object
        const updatedWebinar = {
            ...this.editingWebinar,
            title: formData.get('title'),
            provider: formData.get('provider'),
            format: formData.get('format'),
            duration_min: parseInt(formData.get('duration')),
            certificate_available: formData.get('certificate') === 'true',
            certificate_process: formData.get('certificateProcess'),
            url: formData.get('url'),
            description: formData.get('description'),
            topics: topics,
            live_date: formData.get('liveDate') || 'on-demand'
        };
        
        // Update the webinar in the array
        const index = this.webinars.findIndex(w => w.id === this.editingWebinar.id);
        if (index !== -1) {
            this.webinars[index] = updatedWebinar;
            this.filteredWebinars = [...this.webinars];
            this.renderTable();
            this.populateFilters();
            this.updateResultsInfo();
            this.updateFooterInfo();
            
            this.showToast('Webinar updated successfully!', 'success');
            this.closeEditModal();
            
            // Mark data as modified
            this.dataModified = true;
        }
    }

    closeEditModal() {
        const modal = document.getElementById('editModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.editingWebinar = null;
    }

    deleteWebinar(webinarId) {
        const webinar = this.webinars.find(w => w.id === webinarId);
        if (!webinar) {
            this.showToast('Webinar not found', 'error');
            return;
        }

        if (confirm(`Are you sure you want to delete "${webinar.title}"? This action cannot be undone.`)) {
            // Remove from arrays
            this.webinars = this.webinars.filter(w => w.id !== webinarId);
            this.filteredWebinars = this.filteredWebinars.filter(w => w.id !== webinarId);
            
            // Re-render
            this.renderTable();
            this.populateFilters();
            this.updateResultsInfo();
            this.updateFooterInfo();
            
            this.showToast('Webinar deleted successfully!', 'success');
            
            // Mark data as modified
            this.dataModified = true;
        }
    }

    exportUpdatedData() {
        if (!this.dataModified) {
            this.showToast('No changes to export', 'info');
            return;
        }

        const exportData = {
            webinars: this.webinars,
            last_updated: new Date().toISOString().split('T')[0],
            total_count: this.webinars.length
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = 'webinars_updated.json';
        link.click();
        
        this.showToast('Updated data exported! Replace webinars.json with this file. Likes will be preserved.', 'success');
    }

    updateFooterInfo() {
        // Find the latest date_added from all webinars
        const latestDate = this.webinars.reduce((latest, webinar) => {
            const webinarDate = webinar.date_added;
            if (!webinarDate) return latest;
            
            if (!latest || webinarDate > latest) {
                return webinarDate;
            }
            return latest;
        }, null);
        
        // Use the latest webinar date, or current date if no webinars
        const displayDate = latestDate || new Date().toISOString().split('T')[0];
        
        document.getElementById('lastUpdated').textContent = 
            new Date(displayDate).toLocaleDateString();
        
        // Update total count with current webinar count
        document.getElementById('totalCount').textContent = this.webinars.length;
    }

    // Like functionality methods
    getLikeCount(webinarId) {
        const webinar = this.webinars.find(w => w.id === webinarId);
        return webinar ? (webinar.likes || 0) : 0;
    }

    isWebinarLiked(webinarId) {
        const userLikes = JSON.parse(localStorage.getItem('user_webinar_likes') || '{}');
        return userLikes[webinarId] || false;
    }

    toggleLike(webinarId) {
        const webinar = this.webinars.find(w => w.id === webinarId);
        const userLikes = JSON.parse(localStorage.getItem('user_webinar_likes') || '{}');
        
        if (!webinar) {
            this.showToast('Webinar not found', 'error');
            return;
        }
        
        // Initialize likes if not present
        if (!webinar.likes) {
            webinar.likes = 0;
        }
        
        if (userLikes[webinarId]) {
            // Unlike: decrement global count and remove from user likes
            webinar.likes = Math.max(0, webinar.likes - 1);
            delete userLikes[webinarId];
            this.showToast('Removed from liked webinars', 'info');
        } else {
            // Like: increment global count and add to user likes
            webinar.likes = (webinar.likes || 0) + 1;
            userLikes[webinarId] = true;
            this.showToast('Added to liked webinars', 'success');
        }
        
        // Save user likes to localStorage
        localStorage.setItem('user_webinar_likes', JSON.stringify(userLikes));
        
        // Mark data as modified so it can be exported
        this.dataModified = true;
        
        // Save likes to the server (webinars.json)
        this.saveLikesToServer();
        
        // Re-render the table to update like counts
        this.renderTable();
    }

    async saveLikesToServer() {
        try {
            // Create a backup of current data
            const backupData = {
                webinars: this.webinars,
                last_updated: new Date().toISOString(),
                total_count: this.webinars.length
            };
            
            // Save to webinars.json
            const response = await fetch('save_likes.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(backupData)
            });
            
            if (!response.ok) {
                console.warn('Failed to save likes to server, but continuing with local changes');
            }
        } catch (error) {
            console.warn('Error saving likes to server:', error);
            // Don't show error to user as this is a background operation
        }
    }

    handleUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const webinarId = urlParams.get('id');
        
        if (webinarId) {
            // Find the webinar in the data
            const webinar = this.webinars.find(w => w.id === webinarId);
            if (webinar) {
                // Clear any existing filters to show the webinar
                this.resetFilters();
                
                // Scroll to the specific webinar after a short delay to ensure rendering is complete
                setTimeout(() => {
                    const row = document.querySelector(`tr[data-id="${webinarId}"]`);
                    if (row) {
                        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        row.style.backgroundColor = '#fff3cd';
                        setTimeout(() => {
                            row.style.backgroundColor = '';
                        }, 3000);
                        
                        // Show a toast notification
                        this.showToast(`Scrolled to: ${webinar.title}`, 'info');
                    }
                }, 500);
            } else {
                this.showToast('Webinar not found', 'error');
            }
        }
    }
}

// Initialize the application
let webinarDirectory;
document.addEventListener('DOMContentLoaded', () => {
    webinarDirectory = new WebinarDirectory();
}); 