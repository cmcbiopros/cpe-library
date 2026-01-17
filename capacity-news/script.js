class CapacityNewsDirectory {
    constructor() {
        this.articles = [];
        this.filteredArticles = [];
        this.filters = {
            search: '',
            outlet: '',
            year: '',
            status: '',
            bioreactor: '',
            footprint: '',
            fillfinish: '',
            capex: ''
        };

        this.init();
    }

    sanitizeInput(input) {
        if (typeof input !== 'string') return '';
        return input.replace(/[<>]/g, '').trim();
    }

    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.populateFilters();
        this.applyFilters();
        this.updateFooterInfo();
    }

    async loadData() {
        try {
            const timestamp = new Date().getTime();
            const response = await fetch(`./capacity_news.json?t=${timestamp}`, { cache: 'no-cache' });
            const data = await response.json();

            const articles = Array.isArray(data) ? data : (data.articles || []);
            this.articles = articles.map((article) => this.normalizeArticle(article));
        } catch (error) {
            console.error('Error loading capacity news data:', error);
            this.articles = [];
        }

        this.articles.sort((a, b) => this.getDateValue(b.published_date) - this.getDateValue(a.published_date));
    }

    normalizeArticle(article) {
        const normalized = {
            id: article.id || article.url || `${article.outlet || 'news'}-${article.title || ''}`,
            title: article.title || 'Untitled',
            outlet: article.outlet || article.source || 'Unknown',
            url: article.url || '',
            published_date: article.published_at || article.published_date || article.date || '',
            status: article.status || 'NOT_PERTINENT',
            key_facts_text: article.key_facts_text || '',
            flags: Array.isArray(article.flags) ? article.flags : [],
            event_types: Array.isArray(article.event_types) ? article.event_types : [],
            has_bioreactor_L: Boolean(article.has_bioreactor_L),
            has_footprint: Boolean(article.has_footprint),
            has_fillfinish_output: Boolean(article.has_fillfinish_output),
            has_capex: Boolean(article.has_capex),
            summary: article.summary || '',
            facts: Array.isArray(article.facts) ? article.facts : []
        };

        normalized.facts = normalized.facts.map((fact) => ({
            fact: fact.fact || fact.statement || fact.fact_type || '',
            evidence: fact.evidence || fact.snippet || fact.evidence_snippet || '',
            source_url: fact.source_url || fact.url || normalized.url || ''
        }));

        return normalized;
    }

    setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        const clearSearch = document.getElementById('clearSearch');
        const outletFilter = document.getElementById('outletFilter');
        const yearFilter = document.getElementById('yearFilter');
        const statusFilter = document.getElementById('statusFilter');
        const bioreactorFilter = document.getElementById('bioreactorFilter');
        const footprintFilter = document.getElementById('footprintFilter');
        const fillfinishFilter = document.getElementById('fillfinishFilter');
        const capexFilter = document.getElementById('capexFilter');
        const resetFilters = document.getElementById('resetFilters');
        const downloadCsv = document.getElementById('downloadCsv');
        const tableBody = document.getElementById('newsTableBody');

        searchInput.addEventListener('input', (event) => {
            this.filters.search = this.sanitizeInput(event.target.value);
            this.applyFilters();
        });

        clearSearch.addEventListener('click', () => {
            searchInput.value = '';
            this.filters.search = '';
            this.applyFilters();
        });

        outletFilter.addEventListener('change', (event) => {
            this.filters.outlet = event.target.value;
            this.applyFilters();
        });

        yearFilter.addEventListener('change', (event) => {
            this.filters.year = event.target.value;
            this.applyFilters();
        });

        statusFilter.addEventListener('change', (event) => {
            this.filters.status = event.target.value;
            this.applyFilters();
        });

        bioreactorFilter.addEventListener('change', (event) => {
            this.filters.bioreactor = event.target.value;
            this.applyFilters();
        });

        footprintFilter.addEventListener('change', (event) => {
            this.filters.footprint = event.target.value;
            this.applyFilters();
        });

        fillfinishFilter.addEventListener('change', (event) => {
            this.filters.fillfinish = event.target.value;
            this.applyFilters();
        });

        capexFilter.addEventListener('change', (event) => {
            this.filters.capex = event.target.value;
            this.applyFilters();
        });

        resetFilters.addEventListener('click', () => this.resetFilters());
        downloadCsv.addEventListener('click', () => this.downloadCsv());

        tableBody.addEventListener('click', (event) => {
            const row = event.target.closest('tr');
            if (!row) return;
            const articleId = row.dataset.id;
            const article = this.filteredArticles.find((item) => item.id === articleId);
            if (article) {
                this.renderDetail(article);
            }
        });
    }

    populateFilters() {
        const outlets = [...new Set(this.articles.map((article) => article.outlet).filter(Boolean))].sort();
        const years = [...new Set(this.articles
            .map((article) => this.getYear(article.published_date))
            .filter(Boolean))].sort((a, b) => b - a);

        const outletFilter = document.getElementById('outletFilter');
        outlets.forEach((outlet) => {
            const option = document.createElement('option');
            option.value = outlet;
            option.textContent = outlet;
            outletFilter.appendChild(option);
        });

        const yearFilter = document.getElementById('yearFilter');
        years.forEach((year) => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearFilter.appendChild(option);
        });
    }

    applyFilters() {
        this.filteredArticles = this.articles.filter((article) => {
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                const factsText = article.facts.map((fact) => `${fact.fact} ${fact.evidence}`).join(' ');
                const searchableText = `${article.title} ${article.outlet} ${article.summary} ${article.key_facts_text} ${article.status} ${article.flags.join(' ')} ${factsText}`.toLowerCase();
                if (!searchableText.includes(searchTerm)) return false;
            }

            if (this.filters.outlet && article.outlet !== this.filters.outlet) return false;

            if (this.filters.year) {
                const articleYear = this.getYear(article.published_date);
                if (articleYear?.toString() !== this.filters.year) return false;
            }

            if (this.filters.status && article.status !== this.filters.status) return false;

            if (this.filters.bioreactor === 'true' && !article.has_bioreactor_L) return false;
            if (this.filters.footprint === 'true' && !article.has_footprint) return false;
            if (this.filters.fillfinish === 'true' && !article.has_fillfinish_output) return false;
            if (this.filters.capex === 'true' && !article.has_capex) return false;

            return true;
        });

        this.renderTable();
        this.updateResultsInfo();
    }

    resetFilters() {
        this.filters = {
            search: '',
            outlet: '',
            year: '',
            status: '',
            bioreactor: '',
            footprint: '',
            fillfinish: '',
            capex: ''
        };
        document.getElementById('searchInput').value = '';
        document.getElementById('outletFilter').value = '';
        document.getElementById('yearFilter').value = '';
        document.getElementById('statusFilter').value = '';
        document.getElementById('bioreactorFilter').value = '';
        document.getElementById('footprintFilter').value = '';
        document.getElementById('fillfinishFilter').value = '';
        document.getElementById('capexFilter').value = '';
        this.applyFilters();
    }

    renderTable() {
        const tbody = document.getElementById('newsTableBody');
        const noResults = document.getElementById('noResults');

        if (this.filteredArticles.length === 0) {
            tbody.innerHTML = '';
            noResults.style.display = 'block';
            return;
        }

        noResults.style.display = 'none';
        tbody.innerHTML = this.filteredArticles.map((article) => this.createTableRow(article)).join('');
    }

    createTableRow(article) {
        const dateDisplay = this.formatDate(article.published_date);

        return `
            <tr data-id="${this.escapeHtml(article.id)}">
                <td>
                    <div class="headline">
                        <strong>${this.escapeHtml(article.title)}</strong>
                        <a class="headline-link" href="${this.escapeHtml(article.url)}" target="_blank" rel="noopener">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </td>
                <td>${this.escapeHtml(article.outlet)}</td>
                <td>${this.escapeHtml(dateDisplay)}</td>
                <td><span class="status-pill status-${this.escapeHtml(article.status.toLowerCase())}">${this.escapeHtml(article.status)}</span></td>
                <td>${this.escapeHtml(article.key_facts_text || '—')}</td>
            </tr>
        `;
    }

    renderDetail(article) {
        const detailPanel = document.getElementById('detailPanel');
        const dateDisplay = this.formatDate(article.published_date);
        const flags = article.flags.length ? article.flags.join(', ') : 'None';
        const eventTypes = article.event_types.length ? article.event_types.join(', ') : 'None';

        const factsMarkup = article.facts.length
            ? article.facts.map((fact) => `
                <li>
                    <p class="fact-statement">${this.escapeHtml(fact.fact)}</p>
                    ${fact.evidence ? `<p class="fact-evidence">"${this.escapeHtml(fact.evidence)}"</p>` : ''}
                    ${fact.source_url ? `<a href="${this.escapeHtml(fact.source_url)}" target="_blank" rel="noopener">Source</a>` : ''}
                </li>
            `).join('')
            : '<li>No extracted facts yet.</li>';

        detailPanel.innerHTML = `
            <div class="detail-header">
                <h3>${this.escapeHtml(article.title)}</h3>
                <p class="detail-meta">${this.escapeHtml(article.outlet)} · ${this.escapeHtml(dateDisplay)}</p>
                <p class="detail-meta"><strong>Status:</strong> ${this.escapeHtml(article.status)}</p>
                <p class="detail-meta"><strong>Flags:</strong> ${this.escapeHtml(flags)}</p>
                <p class="detail-meta"><strong>Event types:</strong> ${this.escapeHtml(eventTypes)}</p>
                ${article.key_facts_text ? `<p class="detail-summary"><strong>Key facts:</strong> ${this.escapeHtml(article.key_facts_text)}</p>` : ''}
                ${article.url ? `<a class="detail-link" href="${this.escapeHtml(article.url)}" target="_blank" rel="noopener">
                    <i class="fas fa-external-link-alt"></i> Read full article
                </a>` : ''}
            </div>
            ${article.summary ? `<p class="detail-summary">${this.escapeHtml(article.summary)}</p>` : ''}
            <div class="detail-facts">
                <h4>Facts & Evidence</h4>
                <ul>${factsMarkup}</ul>
            </div>
        `;
    }

    updateResultsInfo() {
        const count = this.filteredArticles.length;
        const total = this.articles.length;
        document.getElementById('resultsCount').textContent =
            `Showing ${count} of ${total} articles`;
    }

    updateFooterInfo() {
        const latestDate = this.articles.reduce((latest, article) => {
            const dateValue = this.getDateValue(article.published_date);
            if (!dateValue) return latest;
            return Math.max(latest, dateValue);
        }, 0);

        const lastUpdated = latestDate ? new Date(latestDate) : new Date();
        document.getElementById('lastUpdated').textContent = lastUpdated.toLocaleDateString();
        document.getElementById('totalCount').textContent = this.articles.length;
    }

    downloadCsv() {
        const headers = [
            'Title', 'Outlet', 'Published Date', 'Status', 'Key Facts', 'Flags',
            'Event Types', 'Has Bioreactor L', 'Has Footprint', 'Has Fill/Finish',
            'Has Capex', 'URL', 'Facts'
        ];
        const rows = this.filteredArticles.map((article) => {
            const factsText = article.facts
                .map((fact) => `${fact.fact}${fact.evidence ? ` (${fact.evidence})` : ''}`)
                .join(' | ');
            return [
                article.title,
                article.outlet,
                article.published_date,
                article.status,
                article.key_facts_text,
                article.flags.join('; '),
                article.event_types.join('; '),
                article.has_bioreactor_L,
                article.has_footprint,
                article.has_fillfinish_output,
                article.has_capex,
                article.url,
                factsText
            ];
        });

        const csvLines = [headers, ...rows].map((row) => row.map(this.escapeCsvValue).join(','));
        const csvContent = csvLines.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'capacity_news_filtered.csv';
        link.click();
    }

    escapeCsvValue(value) {
        if (value === null || value === undefined) return '""';
        const stringValue = String(value).replace(/"/g, '""');
        return `"${stringValue}"`;
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        const dateValue = this.getDateValue(dateString);
        if (!dateValue) return dateString;
        return new Date(dateValue).toLocaleDateString();
    }

    getDateValue(dateString) {
        if (!dateString) return 0;
        const parsed = new Date(dateString);
        if (!isNaN(parsed.getTime())) return parsed.getTime();
        return 0;
    }

    getYear(dateString) {
        const dateValue = this.getDateValue(dateString);
        if (!dateValue) return null;
        return new Date(dateValue).getFullYear();
    }
}

let capacityNewsDirectory;
document.addEventListener('DOMContentLoaded', () => {
    capacityNewsDirectory = new CapacityNewsDirectory();
});
