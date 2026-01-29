// Dashboard Appalti IA ANAC 2023-2025
// app.js - Main application logic

let contractsData = [];

// Colors palette
const colors = [
    '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545',
    '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0',
    '#6c757d', '#adb5bd', '#495057', '#212529', '#f8f9fa', '#343a40'
];

// Format utilities
const formatEuro = (value) => '€' + value.toLocaleString('it-IT');
const formatMilioni = (value) => '€' + (value/1000000).toFixed(1) + 'M';

// Load data and initialize
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('data/contracts.json');
        contractsData = await response.json();
        initCharts();
        initSearch();
        initFilters();
    } catch (error) {
        console.error('Error loading data:', error);
    }
});

// Calculate aggregations from data
function calculateStats() {
    const byPA = {};
    const byCategoria = {};
    const bySettore = {};
    const byYear = {};
    let pnrrValue = 0, nonPnrrValue = 0;

    contractsData.forEach(c => {
        const pa = c.DENOMINAZIONE_AMMINISTRAZIONE || 'N/D';
        const cat = c.categoria_ai || 'Altre applicazioni IA';
        const set = c.settore_pa || 'Altri Enti Pubblici';
        const importo = parseFloat(c.IMPORTO_COMPLESSIVO_GARA) || 0;
        const year = c.ANNO_PUBBLICAZIONE || '2025';

        byPA[pa] = (byPA[pa] || 0) + importo;
        byCategoria[cat] = (byCategoria[cat] || 0) + importo;
        bySettore[set] = (bySettore[set] || 0) + importo;
        byYear[year] = byYear[year] || { count: 0, value: 0 };
        byYear[year].count++;
        byYear[year].value += importo;

        if (c.is_pnrr) pnrrValue += importo;
        else nonPnrrValue += importo;
    });

    return { byPA, byCategoria, bySettore, byYear, pnrrValue, nonPnrrValue };
}

function initCharts() {
    const stats = calculateStats();

    // Top 10 PA
    const top10PA = Object.entries(stats.byPA)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    new Chart(document.getElementById('chartTop10'), {
        type: 'bar',
        data: {
            labels: top10PA.map(([name]) => name.length > 40 ? name.substring(0, 37) + '...' : name),
            datasets: [{
                label: 'Spesa Totale',
                data: top10PA.map(([, val]) => val),
                backgroundColor: 'rgba(13, 110, 253, 0.8)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => formatEuro(ctx.parsed.x) } } },
            scales: { x: { beginAtZero: true, ticks: { callback: (v) => formatMilioni(v) } } }
        }
    });

    // Categorie AI
    const catSorted = Object.entries(stats.byCategoria).sort((a, b) => b[1] - a[1]);
    new Chart(document.getElementById('chartCategorie'), {
        type: 'doughnut',
        data: {
            labels: catSorted.map(([name]) => name),
            datasets: [{ data: catSorted.map(([, val]) => val), backgroundColor: colors.slice(0, catSorted.length), borderWidth: 2 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { boxWidth: 12, font: { size: 10 } } },
                tooltip: { callbacks: { label: (ctx) => { const total = ctx.dataset.data.reduce((a, b) => a + b, 0); return ctx.label + ': ' + formatEuro(ctx.parsed) + ' (' + ((ctx.parsed / total) * 100).toFixed(1) + '%)'; } } }
            }
        }
    });

    // Settori PA
    const setSorted = Object.entries(stats.bySettore).sort((a, b) => b[1] - a[1]);
    new Chart(document.getElementById('chartSettori'), {
        type: 'bar',
        data: {
            labels: setSorted.map(([name]) => name),
            datasets: [{ label: 'Valore', data: setSorted.map(([, val]) => val), backgroundColor: colors.slice(0, setSorted.length), borderWidth: 1 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => formatEuro(ctx.parsed.y) } } },
            scales: { y: { beginAtZero: true, ticks: { callback: (v) => formatMilioni(v) } }, x: { ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } } } }
        }
    });

    // PNRR
    new Chart(document.getElementById('chartPnrr'), {
        type: 'doughnut',
        data: {
            labels: ['PNRR', 'Non-PNRR'],
            datasets: [{ data: [stats.pnrrValue, stats.nonPnrrValue], backgroundColor: ['#198754', '#6c757d'], borderWidth: 2 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: (ctx) => { const total = ctx.dataset.data.reduce((a, b) => a + b, 0); return ctx.label + ': ' + formatEuro(ctx.parsed) + ' (' + ((ctx.parsed / total) * 100).toFixed(1) + '%)'; } } } }
        }
    });

    // Trend
    const years = ['2023', '2024', '2025'];
    new Chart(document.getElementById('chartTrend'), {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                { label: 'N. Contratti', data: years.map(y => stats.byYear[y]?.count || 0), borderColor: 'rgb(75, 192, 192)', backgroundColor: 'rgba(75, 192, 192, 0.2)', tension: 0.1, yAxisID: 'y', fill: true },
                { label: 'Valore (€M)', data: years.map(y => (stats.byYear[y]?.value || 0) / 1000000), borderColor: 'rgb(255, 99, 132)', backgroundColor: 'rgba(255, 99, 132, 0.2)', tension: 0.1, yAxisID: 'y1', fill: true }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { position: 'top' } },
            scales: {
                y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'N. Contratti' } },
                y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Valore (€M)' }, grid: { drawOnChartArea: false } }
            }
        }
    });
}

// Search functionality
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    const autocomplete = document.getElementById('autocomplete');
    const searchResults = document.getElementById('searchResults');
    let selectedIndex = -1;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim().toLowerCase();
        if (query.length < 3) {
            autocomplete.style.display = 'none';
            searchResults.innerHTML = '';
            return;
        }

        const matches = contractsData.filter(c => {
            const searchText = [
                c.CIG, c.DENOMINAZIONE_AMMINISTRAZIONE, c.OGGETTO_LOTTO,
                c.COD_ISTAT_PROVINCIA_SEDE, c.categoria_ai, c.settore_pa
            ].join(' ').toLowerCase();
            return searchText.includes(query);
        }).slice(0, 10);

        if (matches.length > 0) {
            autocomplete.innerHTML = matches.map((c, i) => `
                <div class="autocomplete-item" data-index="${i}">
                    <div class="d-flex justify-content-between">
                        <span class="cig">${c.CIG}</span>
                        <span class="badge bg-success">${formatEuro(parseFloat(c.IMPORTO_COMPLESSIVO_GARA) || 0)}</span>
                    </div>
                    <div class="pa">${c.DENOMINAZIONE_AMMINISTRAZIONE || 'N/D'}</div>
                    <div class="oggetto">${(c.OGGETTO_LOTTO || '').substring(0, 80)}...</div>
                </div>
            `).join('');
            autocomplete.style.display = 'block';
            selectedIndex = -1;

            autocomplete.querySelectorAll('.autocomplete-item').forEach((item, idx) => {
                item.addEventListener('click', () => showFullResults(query));
                item.addEventListener('mouseenter', () => {
                    autocomplete.querySelectorAll('.autocomplete-item').forEach(i => i.classList.remove('active'));
                    item.classList.add('active');
                    selectedIndex = idx;
                });
            });
        } else {
            autocomplete.style.display = 'none';
        }
    });

    searchInput.addEventListener('keydown', (e) => {
        const items = autocomplete.querySelectorAll('.autocomplete-item');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            items.forEach((item, i) => item.classList.toggle('active', i === selectedIndex));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, 0);
            items.forEach((item, i) => item.classList.toggle('active', i === selectedIndex));
        } else if (e.key === 'Enter') {
            e.preventDefault();
            showFullResults(searchInput.value.trim().toLowerCase());
            autocomplete.style.display = 'none';
        } else if (e.key === 'Escape') {
            autocomplete.style.display = 'none';
        }
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-input-wrapper')) autocomplete.style.display = 'none';
    });
}

function showFullResults(query) {
    const searchResults = document.getElementById('searchResults');
    if (query.length < 3) return;

    const matches = contractsData.filter(c => {
        const searchText = [c.CIG, c.DENOMINAZIONE_AMMINISTRAZIONE, c.OGGETTO_LOTTO, c.COD_ISTAT_PROVINCIA_SEDE, c.categoria_ai, c.settore_pa].join(' ').toLowerCase();
        return searchText.includes(query);
    });

    if (matches.length === 0) {
        searchResults.innerHTML = '<div class="no-results"><i class="bi bi-search"></i><p>Nessun risultato per "' + query + '"</p></div>';
        return;
    }

    const highlight = (text) => text ? text.replace(new RegExp('(' + query + ')', 'gi'), '<span class="highlight">$1</span>') : '';

    searchResults.innerHTML = `
        <div class="result-count mb-3">Trovati <strong>${matches.length}</strong> contratti</div>
        ${matches.slice(0, 50).map(c => `
            <div class="result-card">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <span class="cig-badge">${highlight(c.CIG)}</span>
                    <span class="importo">${formatEuro(parseFloat(c.IMPORTO_COMPLESSIVO_GARA) || 0)}</span>
                </div>
                <div class="fw-bold mb-1">${highlight(c.DENOMINAZIONE_AMMINISTRAZIONE || 'N/D')}</div>
                <div class="small text-muted mb-1">${highlight(c.OGGETTO_LOTTO || '')}</div>
                <div class="d-flex gap-2 flex-wrap">
                    <span class="badge bg-primary">${c.categoria_ai || 'N/D'}</span>
                    <span class="badge bg-secondary">${c.settore_pa || 'N/D'}</span>
                    <span class="badge bg-info">${c.COD_ISTAT_PROVINCIA_SEDE || 'N/D'}</span>
                    ${c.is_pnrr ? '<span class="badge bg-success">PNRR</span>' : ''}
                </div>
            </div>
        `).join('')}
        ${matches.length > 50 ? '<div class="text-muted text-center mt-3">Mostrati 50 di ' + matches.length + ' risultati</div>' : ''}
    `;
}

// Filter functionality
function initFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(b => {
                b.classList.remove('btn-primary', 'active');
                b.classList.add('btn-outline-secondary');
            });
            this.classList.remove('btn-outline-secondary');
            this.classList.add('btn-primary', 'active');

            const settore = this.dataset.settore;
            const rows = document.querySelectorAll('#paTableBody tr');
            let visibleCount = 0;

            rows.forEach(row => {
                if (settore === 'all' || row.dataset.settore === settore) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            const filterInfo = document.getElementById('filterInfo');
            if (settore === 'all') {
                filterInfo.style.display = 'none';
            } else {
                filterInfo.style.display = 'block';
                filterInfo.innerHTML = `<i class="bi bi-funnel-fill"></i> Filtro attivo: <strong>${settore}</strong> (${visibleCount} risultati)`;
            }
        });
    });
}

// Show PA contracts in modal
function showPAContracts(element) {
    const paName = element.closest('tr').dataset.pa;
    const contracts = contractsData.filter(c => c.DENOMINAZIONE_AMMINISTRAZIONE === paName);

    document.getElementById('paModalLabel').textContent = paName;
    document.getElementById('paContractsList').innerHTML = contracts.map(c => `
        <div class="contract-item">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <span class="cig-badge">${c.CIG}</span>
                <span class="text-success fw-bold">${formatEuro(parseFloat(c.IMPORTO_COMPLESSIVO_GARA) || 0)}</span>
            </div>
            <div class="small mb-1">${c.OGGETTO_LOTTO || 'N/D'}</div>
            <div class="d-flex gap-1 flex-wrap">
                <span class="badge bg-primary" style="font-size:0.7rem">${c.categoria_ai || 'N/D'}</span>
                <span class="badge bg-info" style="font-size:0.7rem">${c.ANNO_PUBBLICAZIONE || 'N/D'}</span>
                ${c.is_pnrr ? '<span class="badge bg-success" style="font-size:0.7rem">PNRR</span>' : ''}
            </div>
        </div>
    `).join('');

    new bootstrap.Modal(document.getElementById('paModal')).show();
}

// Make showPAContracts globally available
window.showPAContracts = showPAContracts;
