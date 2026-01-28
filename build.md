# 📋 DOCUMENTO REQUISITI: ANALISI E DASHBOARD APPALTI IA ANAC 2023-2025

## 🎯 OBIETTIVO DEL PROGETTO

Creare un sistema completo di analisi e visualizzazione dei contratti pubblici italiani relativi all'Intelligenza Artificiale dal 2023 al 2025, includendo:
1. Caricamento e pulizia dati da 3 file CSV ANAC
2. Validazione automatica anomalie e correzione errori
3. Analisi statistiche e categorizzazioni automatiche
4. Dashboard interattiva professionale con Bootstrap 5 e Chart.js

---

## 📂 SORGENTI DATI

### File di Input (3 CSV)
- `appalti_ia_2023_anac.csv` (111 contratti)
- `appalti_ia_2024_anac.csv` (330 contratti)
- `appalti_ia_2025_anac.csv` (518 contratti)

**Totale record attesi**: 959 contratti

### Formato File
- **Separatore**: `;` (punto e virgola)
- **Encoding**: UTF-8 con BOM
- **Line ending**: Windows (CRLF - `\r\n`)
- **Campi testuali**: Racchiusi tra doppi apici `"`

### Struttura Colonne Principali
```
cig, denominazione_amministrazione_appaltante, cf_amministrazione_appaltante,
provincia, oggetto_gara, oggetto_lotto, importo_complessivo_gara, importo_lotto,
tipo_scelta_contraente, data_pubblicazione, anno_pubblicazione, stato,
cod_cpv, descrizione_cpv, flag_pnrr_pnc
```

---

## ⚠️ PROBLEMI NOTI NEI DATI

### 🚨 ERRORE CRITICO IDENTIFICATO

**CIG B1B36B1A1E - Università degli Studi di Cagliari**
- **Oggetto**: "N.1 COPIA DI CIASCUNO DEI SEGUENTI VOLUMI: MONDADORI - ERA DELL'INTELLIGENZA ARTIFICIALE..." (acquisto libri biblioteca)
- **Importo ERRATO dichiarato**: €293,893,058.00
- **Importo CORRETTO**: ~€357.85 (confrontando CIG B1AA21EEA3 e B1B748D667 con oggetto identico)
- **Impatto**: 62.6% del dataset totale
- **Azione richiesta**: CORREGGERE automaticamente durante caricamento

### Altri Problemi da Validare
1. **Province mancanti/errate**: Alcuni contratti hanno provincia NULL o incoerente con sede PA
2. **Importi outlier**: Identificare contratti con importi >3 deviazioni standard dalla media
3. **Date incongruenti**: data_pubblicazione futura o precedente all'anno_pubblicazione
4. **CPV errati**: Codici CPV che non corrispondono a servizi/forniture AI

---

## 🔍 ANALISI RICHIESTE (8 DOMANDE)

### ✅ ANALISI 1: Statistiche Generali Dataset

**Output richiesto**:
```
- Totale contratti: 959
- Valore totale (corretto): €175,549,668.13
- Valore medio: €183,054.92
- Valore mediano: €25,000.00
- PA coinvolte: 618
- Province coinvolte: 96
- Anni coperti: 2023, 2024, 2025
- Distribuzione temporale:
  * 2023: 111 contratti
  * 2024: 330 contratti (+197%)
  * 2025: 518 contratti (+57%)
```

### ⚠️ ANALISI 2: Totale Somma Aggiudicazione

**Limitazione**: Campo "importo_aggiudicazione" NON presente nei CSV
**Output possibile**:
```
- Valore totale importo_lotto: €175.5M
- Numero contratti: 959
- Valore medio per contratto: €183K
- Nota: Non è possibile distinguere tra base d'asta e importo aggiudicato
```

**Calcoli richiesti**:
- Somma totale `importo_lotto` (dopo correzione errori)
- Distribuzione per anno
- Confronto importo_lotto vs importo_complessivo_gara

### ✅ ANALISI 3 & 4: Classifica Amministrazioni Appaltanti

**Output richiesto**: TOP 30 PA con dettaglio completo

**Campi da calcolare per ogni PA**:
```python
{
  'denominazione_amministrazione_appaltante': str,
  'cf_amministrazione_appaltante': str,
  'provincia': str (più frequente se multipla),
  'importo_totale': float (somma importo_lotto),
  'numero_contratti': int,
  'importo_medio': float,
  'importo_minimo': float,
  'importo_massimo': float,
  'anni_attività': list (anni con contratti),
  'settore_pa': str (vedi classificazione settori)
}
```

**Ranking dopo correzione errori**:
```
1. Agenzia Spaziale Italiana: €34.3M (13 contratti)
2. Ministero Interno P.S.: €29.0M (3 contratti)
3. CONSOB: €10.0M (1 contratto)
4. Digital Library: €8.0M (1 contratto)
5. CNR: €7.2M (21 contratti)
...
```

### ❌ ANALISI 5: Classifica Società Aggiudicatarie

**STATUS**: IMPOSSIBILE - dato non disponibile nei CSV

**Messaggio da mostrare nella dashboard**:
```
⚠️ ANALISI NON DISPONIBILE

I dati ANAC forniti non contengono informazioni sulle società aggiudicatarie.
Campi mancanti: aggiudicatario, operatore_economico, ditta, fornitore.

Per questa analisi è necessario:
- Integrare con API ANAC endpoint /v1/contratti/{CIG}
- Utilizzare dataset complementari ANAC con dati aggiudicatari
- Accedere al portale contrattipubblici.it
```

### ✅ ANALISI 6: Clusterizzazione Acquisti per Tipologia AI

**Algoritmo di classificazione**: Pattern matching con regex su campi `oggetto_lotto` e `oggetto_gara`

**Categorie AI da identificare** (15 categorie):

```python
categorie_ai = {
    'AI Generativa & LLM': [
        r'ai generativa', r'llm', r'gpt', r'chatbot', r'chat bot',
        r'assistente virtuale', r'conversazional', r'generative ai'
    ],
    'Machine Learning & Analytics': [
        r'machine learning', r'ml(?:\s|$)', r'deep learning',
        r'predittiv', r'analytics', r'analisi dati', r'data science'
    ],
    'Computer Vision': [
        r'visione artificiale', r'computer vision', r'riconoscimento immagini',
        r'detection', r'rilevamento', r'video analytics', r'ocr'
    ],
    'NLP & Speech': [
        r'nlp', r'natural language', r'elaborazione linguaggio',
        r'speech', r'vocale', r'riconoscimento vocale', r'text mining'
    ],
    'RPA & Automazione': [
        r'rpa', r'robotic process', r'automazione', r'workflow automation',
        r'processo automatizzato'
    ],
    'Formazione IA': [
        r'formazione.*ia', r'corso.*intelligenza artificiale',
        r'training.*ai', r'didattica.*ia', r'insegnamento.*ai'
    ],
    'Cybersecurity IA': [
        r'cybersecurity.*ia', r'sicurezza.*intelligenza artificiale',
        r'threat detection', r'anomaly detection.*security'
    ],
    'Healthcare IA': [
        r'diagnostica.*ia', r'medical.*ai', r'radiologia.*ia',
        r'telemedicina.*ia', r'clinical.*ai', r'pathology.*ai',
        r'polipi', r'colonscopia', r'endoscopia.*ia'
    ],
    'Biometria': [
        r'biometric', r'facial recognition', r'riconoscimento facciale',
        r'fingerprint', r'impronta digitale', r'iris recognition'
    ],
    'Document Intelligence': [
        r'document.*intelligence', r'protocollazione.*ia',
        r'gestione documentale.*ia', r'archiviazione.*ia'
    ],
    'IoT & Edge AI': [
        r'iot.*ai', r'edge.*ai', r'smart.*sensor', r'sensori.*intelligenti'
    ],
    'Recommendation Systems': [
        r'recommendation', r'raccomandazione', r'suggerimento automatico',
        r'personalizzazione.*ai'
    ],
    'AI Ethics & Governance': [
        r'etica.*ia', r'governance.*ai', r'responsible.*ai',
        r'trustworthy.*ai', r'ai act'
    ],
    'Infrastruttura IA': [
        r'gpu', r'cuda', r'tensorflow', r'pytorch', r'cloud.*ai',
        r'infrastructure.*ai', r'computing.*ai', r'calcolo.*ai'
    ],
    'Consulenza IA': [
        r'consulenza.*ia', r'advisory.*ai', r'supporto.*intelligenza artificiale',
        r'assessment.*ai'
    ],
    'Altre applicazioni IA': []  # Catch-all per contratti non classificati
}
```

**Output atteso** (dopo correzione):
```
1. Altre applicazioni IA: €143.2M (81.5%, 635 contratti)
2. Consulenza IA: €12.3M (7.0%, 81 contratti)
3. Formazione IA: €3.8M (2.2%, 144 contratti)
4. Cybersecurity IA: €3.7M (2.1%, 12 contratti)
5. Machine Learning: €3.1M (1.8%, 19 contratti)
...
```

### ✅ ANALISI 7: Clusterizzazione Settori PA

**Algoritmo**: Pattern matching su `denominazione_amministrazione_appaltante`

**Macro-settori da identificare** (10 categorie):

```python
settori_pa = {
    'Sanità': [
        r'asl', r'azienda sanitaria', r'ospedale', r'irccs', r'agenas',
        r'policlinico', r'usl', r'ausl', r'asst', r'ats', r'aou', r'asp'
    ],
    'Università e Ricerca': [
        r'università', r'university', r'politecnico', r'cnr',
        r'scuola superiore', r'istituto nazionale', r'infn', r'enea',
        r'istituto superiore'
    ],
    'PA Centrale': [
        r'ministero', r'agenzia entrate', r'inps', r'inail', r'aci',
        r'agenzia nazionale', r'agid', r'sogei', r'consip', r'agenzia dogane'
    ],
    'PA Locale': [
        r'comune', r'provincia', r'regione', r'città metropolitana',
        r'municipio', r'unione comuni', r'comunità montana'
    ],
    'Istruzione': [
        r'istituto comprensivo', r'liceo', r'istituto tecnico',
        r'istituto professionale', r'convitto', r'scuola',
        r'direzione didattica', r'circolo didattico'
    ],
    'Difesa e Sicurezza': [
        r'difesa', r'carabinieri', r'polizia', r'guardia di finanza',
        r'vigili del fuoco', r'esercito', r'marina', r'aeronautica',
        r'corpo forestale'
    ],
    'Utilities & Trasporti': [
        r'rai', r'trenitalia', r'rfi', r'anas', r'enav', r'acea',
        r'atac', r'atm', r'amat', r'metropolitana', r'ferrovie'
    ],
    'Enti Pubblici Economici': [
        r'cassa depositi', r'cdp', r'eur spa', r'invitalia', r'sace',
        r'banca d.italia', r'banca italia'
    ],
    'Giustizia': [
        r'tribunale', r'corte', r'procura', r'consiglio superiore magistratura',
        r'avvocatura', r'tar', r'consiglio di stato'
    ],
    'Altri Enti Pubblici': []  # Catch-all
}
```

**Output atteso** (dopo correzione):
```
1. Altri Enti Pubblici: €101.2M (57.6%, 331 PA)
2. PA Centrale: €30.8M (17.5%, 16 PA)
3. PA Locale: €20.8M (11.8%, 114 PA)
4. Difesa e Sicurezza: €6.9M (3.9%, 9 PA)
5. Sanità: €6.5M (3.7%, 32 PA)
...
```

### ✅ ANALISI 8: Contratti PNRR vs Non-PNRR

**Algoritmo di identificazione**:
1. Verifica campo `flag_pnrr_pnc` = 1
2. Text mining su `oggetto_lotto` e `oggetto_gara` per pattern PNRR

**Pattern PNRR**:
```python
pnrr_patterns = [
    r'pnrr', r'piano nazionale ripresa', r'next generation',
    r'ngeu', r'recovery fund', r'recovery plan', r'rrf'
]
```

**Output atteso**:
```
CONTRATTI PNRR:
- Numero: 117 contratti (12.2%)
- Valore: €6.4M (3.7% del totale)
- Valore medio: €54,945.80
- Valore mediano: €13,200.00

CONTRATTI NON-PNRR:
- Numero: 842 contratti (87.8%)
- Valore: €169.1M (96.3% del totale)
- Valore medio: €200,849.76
- Valore mediano: €26,331.75

TREND TEMPORALE PNRR:
- 2023: 20 contratti, €542,930.02
- 2024: 56 contratti, €2,861,655.89 (+427%)
- 2025: 41 contratti, €3,024,072.39 (+6%)

INSIGHT: I contratti PNRR hanno valore medio molto più basso
(€55K vs €201K), indicando progetti di formazione/consulenza
piuttosto che infrastrutture AI.
```

---

## 🔧 VALIDAZIONI AUTOMATICHE

### Controlli da Implementare

#### 1. Validazione Importi
```python
def valida_importi(df):
    """
    Controlla anomalie negli importi
    """
    # Calcola statistiche
    media = df['importo_lotto'].mean()
    std = df['importo_lotto'].std()
    
    # Identifica outlier (>3 deviazioni standard)
    outliers = df[df['importo_lotto'] > media + 3*std]
    
    # Controlla coerenza importo_lotto vs importo_complessivo_gara
    incoerenti = df[df['importo_lotto'] > df['importo_complessivo_gara']]
    
    # CORREZIONE AUTOMATICA ERRORE NOTO
    df.loc[df['cig'] == 'B1B36B1A1E', 'importo_lotto'] = 357.85
    df.loc[df['cig'] == 'B1B36B1A1E', 'importo_complessivo_gara'] = 357.85
    
    return {
        'outliers': outliers,
        'incoerenti': incoerenti,
        'correzioni_applicate': ['CIG B1B36B1A1E: €293.8M → €357.85']
    }
```

#### 2. Validazione Date
```python
def valida_date(df):
    """
    Controlla coerenza date
    """
    # Converti date
    df['data_pubblicazione'] = pd.to_datetime(df['data_pubblicazione'], errors='coerce')
    
    # Date future (oltre data odierna)
    oggi = pd.Timestamp.now()
    future = df[df['data_pubblicazione'] > oggi]
    
    # Anno pubblicazione incoerente con data
    df['anno_da_data'] = df['data_pubblicazione'].dt.year
    incoerenti = df[df['anno_pubblicazione'] != df['anno_da_data']]
    
    return {
        'date_future': future,
        'anni_incoerenti': incoerenti
    }
```

#### 3. Validazione Geografica
```python
def valida_geografia(df):
    """
    Controlla coerenza dati geografici
    """
    # Province mancanti
    province_null = df[df['provincia'].isna()]
    
    # Province non valide (confronto con lista ISTAT)
    province_valide = ['ROMA', 'MILANO', 'NAPOLI', ...]  # Lista completa 110 province
    province_invalide = df[~df['provincia'].isin(province_valide)]
    
    return {
        'province_mancanti': len(province_null),
        'province_invalide': province_invalide
    }
```

#### 4. Validazione Campi Obbligatori
```python
def valida_campi_obbligatori(df):
    """
    Verifica presenza campi essenziali
    """
    campi_obbligatori = [
        'cig', 'denominazione_amministrazione_appaltante',
        'importo_lotto', 'oggetto_lotto', 'anno_pubblicazione'
    ]
    
    problemi = {}
    for campo in campi_obbligatori:
        null_count = df[campo].isna().sum()
        if null_count > 0:
            problemi[campo] = {
                'record_mancanti': null_count,
                'percentuale': (null_count / len(df)) * 100
            }
    
    return problemi
```

---

## 🎨 DASHBOARD: SPECIFICHE TECNICHE

### Stack Tecnologico
- **HTML5** + **CSS3**
- **Bootstrap 5.3** (CDN)
- **Chart.js 4.4** (CDN)
- **Vanilla JavaScript** (ES6+)
- **Responsive design** (mobile-first)

### Layout Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                    HEADER                                     │
│  🤖 Dashboard Appalti Intelligenza Artificiale ANAC           │
│     Periodo: 2023-2025 | Ultimo aggiornamento: [data]        │
└─────────────────────────────────────────────────────────────┘

┌────────┬────────┬────────┬────────┬────────┬────────┐
│  KPI   │  KPI   │  KPI   │  KPI   │  KPI   │  KPI   │
│   1    │   2    │   3    │   4    │   5    │   6    │
└────────┴────────┴────────┴────────┴────────┴────────┘

┌─────────────────────────────────────────────────────────────┐
│  📊 Top 10 Amministrazioni per Spesa                          │
│  [Grafico a barre orizzontali - Chart.js]                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────┬──────────────────────────────┐
│  🎯 Categorie AI              │  🏢 Settori PA                │
│  [Grafico donut]              │  [Grafico barre]              │
└──────────────────────────────┴──────────────────────────────┘

┌──────────────────────────────┬──────────────────────────────┐
│  🇪🇺 PNRR vs Non-PNRR          │  📈 Trend Temporale           │
│  [Grafico donut]              │  [Grafico linee]              │
└──────────────────────────────┴──────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📋 Tabella Top 30 PA                                         │
│  [Tabella interattiva con ordinamento]                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  ⚠️ Validazioni e Anomalie                                    │
│  [Sezione con alert Bootstrap]                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  FOOTER                                                       │
│  © 2026 | Fonte: ANAC | Download: CSV, JSON                  │
└─────────────────────────────────────────────────────────────┘
```

### KPI Cards (6 metriche principali)

**Card 1 - Totale Contratti**
```html
<div class="col-md-4 col-lg-2">
  <div class="card text-white bg-primary mb-3">
    <div class="card-body">
      <h6 class="card-title text-uppercase">Totale Contratti</h6>
      <h2 class="display-4">959</h2>
      <p class="card-text">Anni 2023-2025</p>
    </div>
  </div>
</div>
```

**Card 2 - Valore Totale**
- Valore: €175.5M
- Colore: bg-success
- Icona: 💰

**Card 3 - PA Coinvolte**
- Valore: 618
- Colore: bg-info
- Icona: 🏛️

**Card 4 - Valore Medio**
- Valore: €183K
- Colore: bg-warning
- Icona: 📊

**Card 5 - Contratti PNRR**
- Valore: 117 (12.2%)
- Colore: bg-success
- Icona: 🇪🇺

**Card 6 - Province**
- Valore: 96
- Colore: bg-secondary
- Icona: 🗺️

### Grafici Chart.js

#### Grafico 1: Top 10 PA (Bar Orizzontale)
```javascript
{
    type: 'bar',
    data: {
        labels: ['Ag. Spaziale', 'Min. Interno', 'CONSOB', ...],
        datasets: [{
            label: 'Spesa Totale (€)',
            data: [34274022, 28975206, 9986895, ...],
            backgroundColor: 'rgba(54, 162, 235, 0.8)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2
        }]
    },
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: { display: true, text: 'Top 10 PA per Spesa' },
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx) => '€' + ctx.parsed.x.toLocaleString('it-IT')
                }
            }
        },
        scales: {
            x: {
                beginAtZero: true,
                ticks: {
                    callback: (value) => '€' + (value/1000000).toFixed(1) + 'M'
                }
            }
        }
    }
}
```

#### Grafico 2: Categorie AI (Donut)
```javascript
{
    type: 'doughnut',
    data: {
        labels: ['Altre IA', 'Consulenza', 'Formazione', 'Cybersecurity', ...],
        datasets: [{
            data: [143151304, 12331614, 3793211, 3715755, ...],
            backgroundColor: [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
            ],
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: { display: true, text: 'Distribuzione per Categoria AI' },
            legend: { position: 'right' },
            tooltip: {
                callbacks: {
                    label: (ctx) => {
                        const label = ctx.label;
                        const value = ctx.parsed;
                        const total = ctx.dataset.data.reduce((a,b) => a+b, 0);
                        const pct = ((value/total)*100).toFixed(1);
                        return `${label}: €${value.toLocaleString('it-IT')} (${pct}%)`;
                    }
                }
            }
        }
    }
}
```

#### Grafico 3: Settori PA (Bar)
- Tipo: bar
- Orientamento: verticale
- Colori: scala gradiente Bootstrap
- Tooltip: mostra n. PA e n. contratti per settore

#### Grafico 4: PNRR vs Non-PNRR (Donut)
- Colori: Verde (#28a745) per PNRR, Grigio (#6c757d) per Non-PNRR
- Centro: mostra valore totale
- Tooltip: percentuali e valori assoluti

#### Grafico 5: Trend Temporale (Line)
```javascript
{
    type: 'line',
    data: {
        labels: ['2023', '2024', '2025'],
        datasets: [
            {
                label: 'Totale Contratti',
                data: [111, 330, 518],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                yAxisID: 'y'
            },
            {
                label: 'Valore (€M)',
                data: [valore_2023/1e6, valore_2024/1e6, valore_2025/1e6],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1,
                yAxisID: 'y1'
            }
        ]
    },
    options: {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        plugins: {
            title: { display: true, text: 'Evoluzione Temporale Contratti AI' }
        },
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: { display: true, text: 'Numero Contratti' }
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: { display: true, text: 'Valore (€M)' },
                grid: { drawOnChartArea: false }
            }
        }
    }
}
```

### Tabella Top 30 PA

**Colonne**:
1. Posizione (#)
2. Denominazione PA
3. Provincia
4. Settore
5. Spesa Totale (€)
6. N. Contratti
7. Spesa Media (€)
8. Anno Primo Contratto
9. Anno Ultimo Contratto

**Features**:
- Ordinamento cliccabile su ogni colonna
- Ricerca/filtro in tempo reale
- Evidenziazione riga al hover
- Colori alternati (striped)
- Responsive (scroll orizzontale su mobile)
- Badge colorati per settori

**Codice Bootstrap**:
```html
<div class="table-responsive">
  <table class="table table-striped table-hover">
    <thead class="table-dark">
      <tr>
        <th scope="col" class="sortable" data-sort="pos">#</th>
        <th scope="col" class="sortable" data-sort="pa">PA</th>
        <th scope="col" class="sortable" data-sort="provincia">Provincia</th>
        <th scope="col" class="sortable" data-sort="settore">Settore</th>
        <th scope="col" class="sortable text-end" data-sort="spesa">Spesa Tot.</th>
        <th scope="col" class="sortable text-end" data-sort="num">N. Contr.</th>
        <th scope="col" class="sortable text-end" data-sort="media">Spesa Med.</th>
      </tr>
    </thead>
    <tbody id="tableBody">
      <!-- Popolato dinamicamente via JS -->
    </tbody>
  </table>
</div>
```

### Sezione Validazioni

**Alert per Anomalie Identificate**:

```html
<!-- Errore Critico Corretto -->
<div class="alert alert-danger d-flex align-items-center" role="alert">
  <svg class="bi flex-shrink-0 me-2" width="24" height="24">
    <use xlink:href="#exclamation-triangle-fill"/>
  </svg>
  <div>
    <strong>Errore Critico Corretto</strong><br>
    CIG <code>B1B36B1A1E</code> - Importo errato €293.8M corretto a €357.85
    (acquisto libri biblioteca Univ. Cagliari)
  </div>
</div>

<!-- Dato Mancante -->
<div class="alert alert-warning d-flex align-items-center" role="alert">
  <svg class="bi flex-shrink-0 me-2" width="24" height="24">
    <use xlink:href="#exclamation-triangle-fill"/>
  </svg>
  <div>
    <strong>Analisi Aggiudicatari Non Disponibile</strong><br>
    I dati ANAC non contengono informazioni sulle società aggiudicatarie.
    È necessaria integrazione con API ANAC o fonti esterne.
  </div>
</div>

<!-- Info Outlier -->
<div class="alert alert-info d-flex align-items-center" role="alert">
  <svg class="bi flex-shrink-0 me-2" width="24" height="24">
    <use xlink:href="#info-fill"/>
  </svg>
  <div>
    <strong>Outlier Identificati</strong><br>
    Rilevati <span class="badge bg-primary">X</span> contratti con importi
    superiori a 3 deviazioni standard dalla media.
    <button class="btn btn-sm btn-outline-info ms-2" data-bs-toggle="modal" 
            data-bs-target="#outlierModal">Visualizza</button>
  </div>
</div>
```

### Palette Colori

**Colori Primari**:
```css
--primary: #0d6efd;      /* Bootstrap primary blue */
--success: #198754;      /* Bootstrap green */
--warning: #ffc107;      /* Bootstrap yellow */
--danger: #dc3545;       /* Bootstrap red */
--info: #0dcaf0;         /* Bootstrap cyan */
--secondary: #6c757d;    /* Bootstrap gray */
```

**Colori Chart.js** (15 categorie AI):
```javascript
[
  '#0d6efd', // Primary blue
  '#6610f2', // Indigo
  '#6f42c1', // Purple
  '#d63384', // Pink
  '#dc3545', // Red
  '#fd7e14', // Orange
  '#ffc107', // Yellow
  '#198754', // Green
  '#20c997', // Teal
  '#0dcaf0', // Cyan
  '#6c757d', // Gray
  '#adb5bd', // Gray 500
  '#495057', // Gray 700
  '#212529', // Dark
  '#f8f9fa'  // Light
]
```

### Responsive Breakpoints

```css
/* Mobile First */
@media (max-width: 576px) {
  /* Cards stack verticalmente */
  .col-lg-2 { width: 100%; }
  /* Font size ridotto */
  .display-4 { font-size: 2rem; }
}

@media (min-width: 768px) {
  /* Tablet: 2 cards per riga */
  .col-md-4 { width: 50%; }
}

@media (min-width: 992px) {
  /* Desktop: layout completo */
  .col-lg-2 { width: 16.666%; }
}
```

---

## 📤 OUTPUT RICHIESTI

### 1. File HTML Completo (`dashboard.html`)
- Single page application
- Bootstrap 5.3 CDN
- Chart.js 4.4 CDN
- CSS inline o in `<style>` tag
- JavaScript inline o in `<script>` tag
- Tutti i dati embedded (no file esterni)

### 2. File Dati Processati (`dati_processati.json`)
```json
{
  "metadata": {
    "data_elaborazione": "2026-01-28T12:00:00Z",
    "totale_contratti": 959,
    "valore_totale": 175549668.13,
    "anni": ["2023", "2024", "2025"],
    "correzioni_applicate": [
      "CIG B1B36B1A1E: €293,893,058.00 → €357.85"
    ]
  },
  "statistiche_generali": { ... },
  "top_pa": [ ... ],
  "categorie_ai": [ ... ],
  "settori_pa": [ ... ],
  "pnrr": { ... },
  "validazioni": { ... }
}
```

### 3. Dataset Corretto CSV (`dataset_corretto.csv`)
- Formato: CSV con separatore `;`
- Encoding: UTF-8 con BOM
- Colonne aggiunte:
  - `categoria_ai`: categoria AI assegnata
  - `settore_pa`: settore PA assegnato
  - `is_pnrr`: boolean (True/False)
  - `is_outlier`: boolean
  - `importo_corretto`: importo dopo validazioni

### 4. Report Validazioni (`report_validazioni.txt`)
```
================================================================================
REPORT VALIDAZIONI DATASET ANAC - APPALTI IA 2023-2025
Data: 28/01/2026
================================================================================

1. CORREZIONI AUTOMATICHE APPLICATE
   - CIG B1B36B1A1E: Importo €293,893,058.00 → €357.85
     Motivo: Errore palese (acquisto libri biblioteca per ~€300M)
     Riferimenti: CIG B1AA21EEA3, B1B748D667 (oggetto identico, ~€358)

2. OUTLIER IDENTIFICATI (>3σ)
   [Lista contratti]

3. ANOMALIE DATE
   [Elenco]

4. PROVINCE MANCANTI/ERRATE
   [Elenco]

5. CAMPI OBBLIGATORI MANCANTI
   [Statistiche]

================================================================================
```

---

## 🔄 FLUSSO DI LAVORO

### Step 1: Caricamento Dati
```python
# Leggi i 3 CSV
df_2023 = pd.read_csv('appalti_ia_2023_anac.csv', sep=';', encoding='utf-8-sig')
df_2024 = pd.read_csv('appalti_ia_2024_anac.csv', sep=';', encoding='utf-8-sig')
df_2025 = pd.read_csv('appalti_ia_2025_anac.csv', sep=';', encoding='utf-8-sig')

# Aggiungi colonna anno
df_2023['anno_dataset'] = '2023'
df_2024['anno_dataset'] = '2024'
df_2025['anno_dataset'] = '2025'

# Unifica
df = pd.concat([df_2023, df_2024, df_2025], ignore_index=True)
```

### Step 2: Pulizia Dati
```python
# Converti campi numerici
df['importo_lotto'] = pd.to_numeric(df['importo_lotto'], errors='coerce')
df['importo_complessivo_gara'] = pd.to_numeric(df['importo_complessivo_gara'], errors='coerce')

# Pulisci campi testuali
df['oggetto_lotto'] = df['oggetto_lotto'].fillna('').astype(str).str.strip()
df['denominazione_amministrazione_appaltante'] = df['denominazione_amministrazione_appaltante'].fillna('').astype(str).str.strip()

# Converti date
df['data_pubblicazione'] = pd.to_datetime(df['data_pubblicazione'], errors='coerce')
```

### Step 3: Validazioni
```python
validazioni = {
    'importi': valida_importi(df),
    'date': valida_date(df),
    'geografia': valida_geografia(df),
    'campi_obbligatori': valida_campi_obbligatori(df)
}
```

### Step 4: Categorizzazioni
```python
df['categoria_ai'] = categorizza_acquisti(df)
df['settore_pa'] = categorizza_settori(df)
df['is_pnrr'] = identifica_pnrr(df)
```

### Step 5: Calcolo Statistiche
```python
stats = {
    'generali': calcola_statistiche_generali(df),
    'top_pa': classifica_pa(df, top_n=30),
    'categorie_ai': raggruppa_per_categoria(df),
    'settori_pa': raggruppa_per_settore(df),
    'pnrr': analisi_pnrr(df)
}
```

### Step 6: Generazione Dashboard
```python
html = genera_dashboard_html(df, stats, validazioni)
with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

### Step 7: Export Dati
```python
# JSON per API
with open('dati_processati.json', 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

# CSV corretto
df.to_csv('dataset_corretto.csv', index=False, sep=';', encoding='utf-8-sig')

# Report testuale
genera_report_validazioni(validazioni, 'report_validazioni.txt')
```

---

## 📋 CHECKLIST FINALE

### Funzionalità Core
- [ ] Caricamento e unificazione 3 CSV ANAC
- [ ] Correzione automatica errore CIG B1B36B1A1E
- [ ] Validazione importi con identificazione outlier
- [ ] Validazione date e coerenza temporale
- [ ] Validazione geografica (province)
- [ ] Categorizzazione AI (15 categorie)
- [ ] Categorizzazione settori PA (10 settori)
- [ ] Identificazione contratti PNRR
- [ ] Calcolo statistiche generali
- [ ] Ranking Top 30 PA

### Dashboard
- [ ] 6 KPI cards responsive
- [ ] Grafico Top 10 PA (bar orizzontale)
- [ ] Grafico Categorie AI (donut)
- [ ] Grafico Settori PA (bar)
- [ ] Grafico PNRR vs Non-PNRR (donut)
- [ ] Grafico Trend Temporale (line)
- [ ] Tabella Top 30 PA con ordinamento
- [ ] Sezione validazioni con alert
- [ ] Design responsive mobile-first
- [ ] Palette colori coerente Bootstrap

### Output Files
- [ ] dashboard.html (standalone, tutti assets embedded)
- [ ] dati_processati.json
- [ ] dataset_corretto.csv
- [ ] report_validazioni.txt

### Testing
- [ ] Test su dataset completo (959 contratti)
- [ ] Verifica correzione errore Cagliari
- [ ] Test responsive (mobile, tablet, desktop)
- [ ] Verifica tutti i grafici renderizzano
- [ ] Controllo somme e percentuali (devono fare 100%)
- [ ] Validazione cross-browser (Chrome, Firefox, Safari, Edge)

---

## 🎯 METRICHE DI SUCCESSO

### Accuratezza Dati
- ✅ Valore totale: €175,549,668.13 (dopo correzione)
- ✅ Top PA #1: Agenzia Spaziale Italiana (€34.3M)
- ✅ Contratti PNRR: 117 (12.2%)
- ✅ Categoria AI dominante: "Altre IA" (81.5%)
- ✅ Settore PA dominante: "Altri Enti" (57.6%)

### Performance Dashboard
- Tempo caricamento < 3 secondi
- Rendering grafici < 1 secondo
- Responsive su tutti i device
- Accessibilità WCAG 2.1 Level AA

### Completezza Analisi
- 6.25/8 domande risposte (78%)
- 2 sezioni documentate come "non disponibile"
- 1 errore critico identificato e corretto
- Report validazioni completo

---

## 📞 SUPPORTO E RIFERIMENTI

### Link Utili
- ANAC Dati Aperti: https://dati.anticorruzione.it
- Bootstrap 5 Docs: https://getbootstrap.com/docs/5.3/
- Chart.js Docs: https://www.chartjs.org/docs/latest/
- Pandas Docs: https://pandas.pydata.org/docs/

### Contatti
- Dataset issues: verificare con ANAC per CIG B1B36B1A1E
- Feature requests: implementare filtri interattivi dashboard
- Bug reports: validare su browser aggiuntivi

---

**VERSIONE DOCUMENTO**: 1.0
**DATA**: 28 Gennaio 2026
**AUTORE**: Analisi Claude + Dataset ANAC
**STATO**: ✅ PRONTO PER IMPLEMENTAZIONE

---

## 🚀 COMANDO RAPIDO PER L'AI

```
Usando questo documento di requisiti e i 3 file CSV allegati 
(appalti_ia_2023_anac.csv, appalti_ia_2024_anac.csv, appalti_ia_2025_anac.csv),
genera:

1. Script Python completo per analisi dati
2. Dashboard HTML standalone con Bootstrap 5 e Chart.js 4
3. File dati_processati.json
4. Dataset corretto CSV
5. Report validazioni

Applica OBBLIGATORIAMENTE la correzione dell'errore CIG B1B36B1A1E.
Implementa tutte le validazioni e categorizzazioni specificate.
Usa la palette colori Bootstrap e i layout grafici dettagliati nel documento.
```
