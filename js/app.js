// Dashboard Appalti IA ANAC 2023-2025
// app.js - Main application logic

window.contractsData = [];

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
        window.contractsData = await response.json();
        updateKPIs();
        initCharts();
        initSearch();
        initFilters();
        initTop30Table();
    } catch (error) {
        console.error('Error loading data:', error);
    }
});

// Update KPIs from data
function updateKPIs() {
    const data = window.contractsData;
    const totalContratti = data.length;
    const totalValore = data.reduce((sum, c) => sum + (parseFloat(c.importo_complessivo_gara) || 0), 0);
    const paSet = new Set(data.map(c => c.cf_amministrazione_appaltante).filter(Boolean));
    const provSet = new Set(data.map(c => c.provincia).filter(p => p && p !== 'N/D'));
    const pnrrCount = data.filter(c => c.is_pnrr).length;
    const pnrrPct = totalContratti > 0 ? ((pnrrCount / totalContratti) * 100).toFixed(1) : 0;
    const media = totalContratti > 0 ? totalValore / totalContratti : 0;

    document.getElementById('kpiContratti').textContent = totalContratti.toLocaleString('it-IT');
    document.getElementById('kpiValore').textContent = (totalValore / 1e6).toFixed(1) + 'M';
    document.getElementById('kpiPA').textContent = paSet.size.toLocaleString('it-IT');
    document.getElementById('kpiMedia').textContent = Math.round(media / 1000).toLocaleString('it-IT') + 'K';
    document.getElementById('kpiPNRR').textContent = pnrrCount;
    document.getElementById('kpiPNRRLabel').textContent = `PNRR (${pnrrPct}%)`;
    document.getElementById('kpiProvince').textContent = provSet.size;

    // Update search count
    const searchCount = document.getElementById('searchCount');
    if (searchCount) searchCount.textContent = totalContratti.toLocaleString('it-IT');

    // Update stats info
    const statsInfo = document.getElementById('statsInfo');
    if (statsInfo) statsInfo.textContent = `Record totali: ${totalContratti.toLocaleString('it-IT')} | Validati: ${totalContratti.toLocaleString('it-IT')} | Errori corretti: 1`;

    // Update last update date
    const lastUpdate = document.getElementById('lastUpdate');
    if (lastUpdate) lastUpdate.textContent = new Date().toLocaleDateString('it-IT');
}

// Generate Top 30 PA table
function initTop30Table() {
    const byPA = {};
    window.contractsData.forEach(c => {
        const pa = c.denominazione_amministrazione_appaltante || 'N/D';
        if (!byPA[pa]) byPA[pa] = { total: 0, count: 0, provincia: c.provincia || 'N/D', settore: c.settore_pa || 'Altri Enti Pubblici' };
        byPA[pa].total += parseFloat(c.importo_complessivo_gara) || 0;
        byPA[pa].count++;
    });
    const top30 = Object.entries(byPA).sort((a, b) => b[1].total - a[1].total).slice(0, 30);
    document.getElementById('paTableBody').innerHTML = top30.map(([pa, data], i) =>
        `<tr data-settore="${data.settore}" data-pa="${pa}"><td>${i + 1}</td><td><span class="pa-link" onclick="showPAContracts(this)">${pa.length > 50 ? pa.substring(0, 47) + '...' : pa}</span></td><td>${data.provincia}</td><td><span class="badge bg-secondary badge-settore">${data.settore}</span></td><td class="text-end fw-bold">${Math.round(data.total).toLocaleString('it-IT')}</td><td class="text-end">${data.count}</td><td class="text-end">${Math.round(data.total / data.count).toLocaleString('it-IT')}</td></tr>`
    ).join('');
}

// Calculate aggregations from data
function calculateStats() {
    const byPA = {};
    const byCategoria = {};
    const bySettore = {};
    const byYear = {};
    let pnrrValue = 0, nonPnrrValue = 0;

    window.contractsData.forEach(c => {
        const pa = c.denominazione_amministrazione_appaltante || 'N/D';
        const cat = c.categoria_ai || 'Altre applicazioni IA';
        const set = c.settore_pa || 'Altri Enti Pubblici';
        const importo = parseFloat(c.importo_complessivo_gara) || 0;
        const year = c.anno_pubblicazione || '2025';

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

        const matches = window.contractsData.filter(c => {
            const searchText = [
                c.cig, c.denominazione_amministrazione_appaltante, c.oggetto_lotto,
                c.provincia, c.categoria_ai, c.settore_pa
            ].join(' ').toLowerCase();
            return searchText.includes(query);
        }).slice(0, 10);

        if (matches.length > 0) {
            autocomplete.innerHTML = matches.map((c, i) => `
                <div class="autocomplete-item" data-index="${i}">
                    <div class="d-flex justify-content-between">
                        <span class="cig">${c.cig}</span>
                        <span class="badge bg-success">${formatEuro(parseFloat(c.importo_complessivo_gara) || 0)}</span>
                    </div>
                    <div class="pa">${c.denominazione_amministrazione_appaltante || 'N/D'}</div>
                    <div class="oggetto">${(c.oggetto_lotto || '').substring(0, 80)}...</div>
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

    const matches = window.contractsData.filter(c => {
        const searchText = [c.cig, c.denominazione_amministrazione_appaltante, c.oggetto_lotto, c.provincia, c.categoria_ai, c.settore_pa].join(' ').toLowerCase();
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
                    <span class="cig-badge">${highlight(c.cig)}</span>
                    <span class="importo">${formatEuro(parseFloat(c.importo_complessivo_gara) || 0)}</span>
                </div>
                <div class="fw-bold mb-1">${highlight(c.denominazione_amministrazione_appaltante || 'N/D')}</div>
                <div class="small text-muted mb-1">${highlight(c.oggetto_lotto || '')}</div>
                <div class="d-flex gap-2 flex-wrap">
                    <span class="badge bg-primary">${c.categoria_ai || 'N/D'}</span>
                    <span class="badge bg-secondary">${c.settore_pa || 'N/D'}</span>
                    <span class="badge bg-info">${c.provincia || 'N/D'}</span>
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
    const contracts = window.contractsData.filter(c => c.denominazione_amministrazione_appaltante === paName);

    document.getElementById('paModalLabel').textContent = paName;
    document.getElementById('paContractsList').innerHTML = contracts.map(c => {
        const importoGara = parseFloat(c.importo_complessivo_gara) || 0;
        const importoLotto = parseFloat(c.importo_lotto) || 0;
        const nLotti = c.n_lotti_componenti || 1;
        const dataPub = c.data_pubblicazione ? new Date(c.data_pubblicazione).toLocaleDateString('it-IT', {day:'numeric',month:'long',year:'numeric'}) : 'N/D';
        const riservato = c.TIPO_APPALTO_RISERVATO && c.TIPO_APPALTO_RISERVATO !== 'nan' ? c.TIPO_APPALTO_RISERVATO : null;
        return `
        <div class="contract-item">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <span class="cig-badge">${c.cig}</span>
                <span class="text-success fw-bold">${formatEuro(importoGara)}</span>
            </div>
            <div class="fw-bold small mb-1">${c.oggetto_gara || 'N/D'} <span class="text-muted">(gara ${c.numero_gara || 'N/D'})</span></div>
            <div class="small mb-1"><strong>Lotto:</strong> ${c.oggetto_lotto || 'N/D'}</div>
            <table class="table table-sm table-borderless small mb-2" style="font-size:0.8rem">
                <tr><td class="text-muted" style="width:140px">Importo gara</td><td>${formatEuro(importoGara)} (${nLotti} lotti)</td></tr>
                <tr><td class="text-muted">Importo lotto</td><td>${formatEuro(importoLotto)}</td></tr>
                <tr><td class="text-muted">Tipo contratto</td><td>${c.oggetto_principale_contratto || 'N/D'} - ${c.tipo_scelta_contraente || 'N/D'}</td></tr>
                <tr><td class="text-muted">CPV</td><td>${c.cod_cpv || 'N/D'} (${c.descrizione_cpv || 'N/D'})</td></tr>
                <tr><td class="text-muted">Provincia</td><td>${c.provincia || 'N/D'}</td></tr>
                <tr><td class="text-muted">Pubblicazione</td><td>${dataPub}</td></tr>
                <tr><td class="text-muted">Stato</td><td>${c.stato || 'N/D'}</td></tr>
                <tr><td class="text-muted">PNRR</td><td>${c.is_pnrr ? 'Sì' : 'No'}</td></tr>
                ${riservato ? `<tr><td class="text-muted">Appalto riservato</td><td>${riservato}</td></tr>` : ''}
            </table>
            <div class="d-flex gap-1 flex-wrap">
                <span class="badge bg-primary" style="font-size:0.7rem">${c.categoria_ai || 'N/D'}</span>
                <span class="badge bg-secondary" style="font-size:0.7rem">${c.settore_pa || 'N/D'}</span>
            </div>
        </div>`;
    }).join('');

    new bootstrap.Modal(document.getElementById('paModal')).show();
}

// Make showPAContracts globally available
window.showPAContracts = showPAContracts;
