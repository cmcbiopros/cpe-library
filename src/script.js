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
            date: ''
        };
        
        this.init();
    }

    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.populateFilters();
        this.renderTable();
        this.updateResultsInfo();
    }

    async loadData() {
        try {
            const response = await fetch('webinars.json');
            const data = await response.json();
            this.webinars = data.webinars || [];
            this.filteredWebinars = [...this.webinars];
            
            // Update footer info
            document.getElementById('lastUpdated').textContent = 
                new Date(data.last_updated).toLocaleDateString();
            document.getElementById('totalCount').textContent = data.total_count || this.webinars.length;
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
        }
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const clearSearch = document.getElementById('clearSearch');
        
        searchInput.addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.applyFilters();
        });
        
        clearSearch.addEventListener('click', () => {
            searchInput.value = '';
            this.filters.search = '';
            this.applyFilters();
        });

        // Filter dropdowns
        const filterSelects = ['providerFilter', 'topicFilter', 'formatFilter', 'durationFilter', 'certificateFilter', 'dateFilter'];
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
            date: ''
        };

        // Reset UI
        document.getElementById('searchInput').value = '';
        document.getElementById('providerFilter').value = '';
        document.getElementById('topicFilter').value = '';
        document.getElementById('formatFilter').value = '';
        document.getElementById('durationFilter').value = '';
        document.getElementById('certificateFilter').value = '';
        document.getElementById('dateFilter').value = '';

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

        // Format the date for display
        let dateDisplay = 'On-Demand';
        if (webinar.live_date && webinar.live_date !== 'on-demand' && webinar.live_date !== 'Unknown') {
            try {
                const date = new Date(webinar.live_date);
                if (!isNaN(date.getTime())) {
                    dateDisplay = date.toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric' 
                    });
                }
            } catch (e) {
                dateDisplay = webinar.live_date;
            }
        }

        return `
            <tr>
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
                    <div class="action-buttons">
                        <a href="${webinar.url}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt"></i> View
                        </a>
                        <button class="btn btn-secondary" onclick="webinarDirectory.copyLink('${webinar.id}')">
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

    copyLink(webinarId) {
        const webinar = this.webinars.find(w => w.id === webinarId);
        if (!webinar) return;

        const url = `${window.location.origin}${window.location.pathname}?id=${webinarId}`;
        
        navigator.clipboard.writeText(url).then(() => {
            // Show temporary success message
            const button = event.target.closest('.btn');
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.style.background = '#28a745';
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.style.background = '';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy link:', err);
            alert('Failed to copy link. Please copy manually: ' + url);
        });
    }
}

// Initialize the application
let webinarDirectory;
document.addEventListener('DOMContentLoaded', () => {
    webinarDirectory = new WebinarDirectory();
});

// Handle direct links with webinar ID
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const webinarId = urlParams.get('id');
    
    if (webinarId && webinarDirectory) {
        // Scroll to the specific webinar
        setTimeout(() => {
            const row = document.querySelector(`tr[data-id="${webinarId}"]`);
            if (row) {
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                row.style.backgroundColor = '#fff3cd';
                setTimeout(() => {
                    row.style.backgroundColor = '';
                }, 3000);
            }
        }, 1000);
    }
}); 