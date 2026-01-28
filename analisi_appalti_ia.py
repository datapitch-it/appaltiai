#!/usr/bin/env python3
"""
Analisi e Dashboard Appalti IA ANAC 2023-2025
Genera statistiche, validazioni e dashboard interattiva
"""

import pandas as pd
import numpy as np
import json
import re
from datetime import datetime
from collections import defaultdict

# ============================================================================
# CONFIGURAZIONE
# ============================================================================

INPUT_FILES = [
    'appalti_ia_2023_anac.csv',
    'appalti_ia_2024_anac.csv',
    'appalti_ia_2025_anac.csv'
]

# Errore critico da correggere
ERRORE_CRITICO = {
    'cig': 'B1B36B1A1E',
    'importo_errato': 293893058.00,
    'importo_corretto': 357.85,
    'motivo': 'Acquisto libri biblioteca (confronto CIG B1AA21EEA3, B1B748D667)'
}

# ============================================================================
# PATTERN DI CATEGORIZZAZIONE
# ============================================================================

CATEGORIE_AI = {
    'AI Generativa & LLM': [
        r'ai generativa', r'llm', r'gpt', r'chatbot', r'chat bot',
        r'assistente virtuale', r'conversazional', r'generative ai',
        r'open\s*ai', r'copilot', r'digital human'
    ],
    'Machine Learning & Analytics': [
        r'machine learning', r'ml(?:\s|$)', r'deep learning',
        r'predittiv', r'analytics', r'analisi dati', r'data science',
        r'big data', r'rete neural', r'neural network'
    ],
    'Computer Vision': [
        r'visione artificiale', r'computer vision', r'riconoscimento immagini',
        r'detection', r'rilevamento', r'video analytics', r'ocr',
        r'image processing', r'elaborazione immagini'
    ],
    'NLP & Speech': [
        r'nlp', r'natural language', r'elaborazione linguaggio',
        r'speech', r'vocale', r'riconoscimento vocale', r'text mining',
        r'sentiment analysis', r'text to speech'
    ],
    'RPA & Automazione': [
        r'rpa', r'robotic process', r'automazione', r'workflow automation',
        r'processo automatizzato', r'automazione processo'
    ],
    'Formazione IA': [
        r'formazione.*(?:ia|ai|intelligenza artificiale)',
        r'corso.*(?:ia|ai|intelligenza artificiale)',
        r'training.*(?:ia|ai)', r'didattica.*(?:ia|ai)',
        r'insegnamento.*(?:ia|ai)', r'master.*intelligenza',
        r'seminari?.*(?:ia|ai|intelligenza)', r'mooc.*intelligenza',
        r'laboratori?.*(?:ia|ai|intelligenza)', r'percors.*formativ'
    ],
    'Cybersecurity IA': [
        r'cybersecurity.*(?:ia|ai)', r'sicurezza.*intelligenza artificiale',
        r'threat detection', r'anomaly detection.*security',
        r'cyber.*intelligenza', r'darktrace', r'monitoraggio.*anomalie'
    ],
    'Healthcare IA': [
        r'diagnostica.*(?:ia|ai)', r'medical.*ai', r'radiologia.*(?:ia|ai)',
        r'telemedicina.*(?:ia|ai)', r'clinical.*ai', r'pathology.*ai',
        r'polipi', r'colonscopia', r'endoscopia.*(?:ia|ai)',
        r'mammograf', r'ictus', r'stroke', r'neuroradiologia',
        r'boneview', r'rapidai', r'zeeromed', r'ecocardiograf',
        r'morfologic.*vetrini'
    ],
    'Biometria': [
        r'biometric', r'facial recognition', r'riconoscimento facciale',
        r'fingerprint', r'impronta digitale', r'iris recognition'
    ],
    'Document Intelligence': [
        r'document.*intelligence', r'protocollazione.*(?:ia|ai)',
        r'gestione documentale.*(?:ia|ai)', r'archiviazione.*(?:ia|ai)',
        r'ocr.*(?:ia|ai)'
    ],
    'IoT & Edge AI': [
        r'iot.*(?:ia|ai)', r'edge.*(?:ia|ai)', r'smart.*sensor',
        r'sensori.*intelligenti', r'social robot'
    ],
    'Recommendation Systems': [
        r'recommendation', r'raccomandazione', r'suggerimento automatico',
        r'personalizzazione.*(?:ia|ai)'
    ],
    'AI Ethics & Governance': [
        r'etica.*(?:ia|ai)', r'governance.*(?:ia|ai)', r'responsible.*ai',
        r'trustworthy.*ai', r'ai act', r'trasparenza.*(?:ia|ai|intelligenza)'
    ],
    'Infrastruttura IA': [
        r'gpu', r'cuda', r'tensorflow', r'pytorch', r'cloud.*(?:ia|ai)',
        r'infrastructure.*ai', r'computing.*(?:ia|ai)', r'calcolo.*(?:ia|ai)',
        r'server.*(?:gpu|hpc|ai)', r'workstation.*(?:ia|ai)',
        r'nvidia', r'hpc4ai', r'multi-gpu'
    ],
    'Consulenza IA': [
        r'consulenza.*(?:ia|ai|intelligenza)', r'advisory.*ai',
        r'supporto.*intelligenza artificiale', r'assessment.*ai',
        r'osservatorio.*intelligenza'
    ]
}

SETTORI_PA = {
    'Sanità': [
        r'\basl\b', r'azienda sanitaria', r'ospedale', r'\birccs\b', r'agenas',
        r'policlinico', r'\busl\b', r'\bausl\b', r'\basst\b', r'\bats\b',
        r'\baou\b', r'\basp\b', r'ospedalier[ao]', r'azienda.*sanitar',
        r'azienda.*colli', r'fondazione.*pascale', r'fondazione.*policlinico'
    ],
    'Università e Ricerca': [
        r'universit[àa]', r'university', r'politecnico', r'\bcnr\b',
        r'scuola superiore', r'istituto nazionale', r'\binfn\b', r'\benea\b',
        r'istituto superiore', r'ricerca metrologica', r'crea', r'inrim'
    ],
    'PA Centrale': [
        r'ministero', r'agenzia entrate', r'\binps\b', r'\binail\b', r'\baci\b',
        r'agenzia nazionale', r'\bagid\b', r'sogei', r'consip', r'agenzia dogane',
        r'presidenza.*consiglio', r'commissione.*borsa', r'consob',
        r'agenzia spaziale', r'\bice\b.*agenzia', r'\benit\b'
    ],
    'PA Locale': [
        r'\bcomune\b', r'\bprovincia\b', r'\bregione\b', r'citt[àa] metropolitana',
        r'municipio', r'unione comuni', r'comunit[àa] montana',
        r'camera.*commercio', r'c\.c\.i\.a'
    ],
    'Istruzione': [
        r'istituto comprensivo', r'\bliceo\b', r'istituto tecnico',
        r'istituto professionale', r'convitto', r'\bscuola\b',
        r'direzione didattica', r'circolo didattico', r'\bits\b.*academy',
        r'istituto.*istruzione.*superiore', r'i\.i\.s\.'
    ],
    'Difesa e Sicurezza': [
        r'\bdifesa\b', r'carabinieri', r'polizia', r'guardia.*finanza',
        r'vigili.*fuoco', r'esercito', r'\bmarina\b', r'aeronautica',
        r'corpo forestale', r'interno.*p\.?s\.?', r'comando.*rete'
    ],
    'Utilities & Trasporti': [
        r'\brai\b', r'trenitalia', r'\brfi\b', r'\banas\b', r'\benav\b',
        r'\bacea\b', r'\batac\b', r'\batm\b', r'\bamat\b', r'metropolitana',
        r'ferrovie', r'\bamtab\b', r'\bhera\b', r'\bcap\b.*holding',
        r'acquevenete', r've\.la\b'
    ],
    'Enti Pubblici Economici': [
        r'cassa depositi', r'\bcdp\b', r'\beur\b.*spa', r'invitalia', r'\bsace\b',
        r'banca.*italia', r'digital library'
    ],
    'Giustizia': [
        r'tribunale', r'\bcorte\b', r'\bprocura\b', r'consiglio.*magistratura',
        r'avvocatura', r'\btar\b', r'consiglio.*stato'
    ]
}

PNRR_PATTERNS = [
    r'\bpnrr\b', r'piano nazionale ripresa', r'next generation',
    r'\bngeu\b', r'recovery fund', r'recovery plan', r'\brrf\b',
    r'd\.?m\.?\s*66', r'm4c1'
]

# ============================================================================
# FUNZIONI DI CARICAMENTO E PULIZIA
# ============================================================================

def carica_csv(files):
    """Carica e unifica i CSV"""
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, sep=';', encoding='utf-8-sig', low_memory=False)
            anno = f.split('_')[2]  # Estrai anno dal nome file
            df['anno_dataset'] = anno
            dfs.append(df)
            print(f"✓ Caricato {f}: {len(df)} record")
        except Exception as e:
            print(f"✗ Errore caricamento {f}: {e}")

    df = pd.concat(dfs, ignore_index=True)
    print(f"\n→ Totale record unificati: {len(df)}")
    return df

def pulisci_dati(df):
    """Pulizia e normalizzazione dati"""
    # Converti importi
    df['importo_lotto'] = pd.to_numeric(df['importo_lotto'], errors='coerce').fillna(0)
    df['importo_complessivo_gara'] = pd.to_numeric(df['importo_complessivo_gara'], errors='coerce').fillna(0)

    # Pulisci campi testuali
    for col in ['oggetto_lotto', 'oggetto_gara', 'denominazione_amministrazione_appaltante', 'provincia']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()

    # Converti date
    df['data_pubblicazione'] = pd.to_datetime(df['data_pubblicazione'], errors='coerce')

    # Normalizza provincia
    df['provincia'] = df['provincia'].str.upper().str.strip()
    df.loc[df['provincia'] == '', 'provincia'] = 'N/D'

    return df

def applica_correzioni(df, validazioni):
    """Applica correzioni note"""
    correzioni = []

    # Correzione errore critico CIG B1B36B1A1E
    mask = df['cig'] == ERRORE_CRITICO['cig']
    if mask.any():
        importo_originale = df.loc[mask, 'importo_lotto'].values[0]
        df.loc[mask, 'importo_lotto'] = ERRORE_CRITICO['importo_corretto']
        df.loc[mask, 'importo_complessivo_gara'] = ERRORE_CRITICO['importo_corretto']
        correzioni.append({
            'cig': ERRORE_CRITICO['cig'],
            'tipo': 'ERRORE CRITICO',
            'campo': 'importo_lotto',
            'valore_originale': importo_originale,
            'valore_corretto': ERRORE_CRITICO['importo_corretto'],
            'motivo': ERRORE_CRITICO['motivo']
        })
        print(f"✓ Corretto CIG {ERRORE_CRITICO['cig']}: €{importo_originale:,.2f} → €{ERRORE_CRITICO['importo_corretto']:.2f}")

    validazioni['correzioni_applicate'] = correzioni
    return df

# ============================================================================
# FUNZIONI DI VALIDAZIONE
# ============================================================================

def valida_importi(df):
    """Valida importi e identifica outlier"""
    media = df['importo_lotto'].mean()
    std = df['importo_lotto'].std()
    soglia = media + 3 * std

    outliers = df[df['importo_lotto'] > soglia][['cig', 'denominazione_amministrazione_appaltante',
                                                   'importo_lotto', 'oggetto_lotto']].copy()
    outliers = outliers.sort_values('importo_lotto', ascending=False)

    # Contratti con importo 0
    zero_importo = df[df['importo_lotto'] == 0]

    return {
        'media': media,
        'mediana': df['importo_lotto'].median(),
        'std': std,
        'soglia_outlier': soglia,
        'n_outliers': len(outliers),
        'outliers': outliers.head(20).to_dict('records'),
        'n_importo_zero': len(zero_importo)
    }

def valida_date(df):
    """Valida coerenza date"""
    oggi = pd.Timestamp.now()

    # Date future
    date_future = df[df['data_pubblicazione'] > oggi]

    # Incoerenza anno
    df_temp = df.copy()
    df_temp['anno_da_data'] = df_temp['data_pubblicazione'].dt.year
    incoerenti = df_temp[df_temp['anno_pubblicazione'].astype(float) != df_temp['anno_da_data']]

    return {
        'n_date_future': len(date_future),
        'n_anni_incoerenti': len(incoerenti),
        'date_mancanti': df['data_pubblicazione'].isna().sum()
    }

def valida_campi(df):
    """Valida campi obbligatori"""
    campi = ['cig', 'denominazione_amministrazione_appaltante', 'importo_lotto',
             'oggetto_lotto', 'anno_pubblicazione']

    problemi = {}
    for campo in campi:
        if campo in df.columns:
            null_count = df[campo].isna().sum() + (df[campo] == '').sum()
            if null_count > 0:
                problemi[campo] = {
                    'mancanti': int(null_count),
                    'percentuale': round((null_count / len(df)) * 100, 2)
                }

    return problemi

# ============================================================================
# FUNZIONI DI CATEGORIZZAZIONE
# ============================================================================

def categorizza_ai(row):
    """Categorizza contratto per tipologia AI"""
    testo = f"{row.get('oggetto_lotto', '')} {row.get('oggetto_gara', '')}".lower()

    for categoria, patterns in CATEGORIE_AI.items():
        for pattern in patterns:
            if re.search(pattern, testo, re.IGNORECASE):
                return categoria

    return 'Altre applicazioni IA'

def categorizza_settore(row):
    """Categorizza PA per settore"""
    nome = str(row.get('denominazione_amministrazione_appaltante', '')).lower()

    for settore, patterns in SETTORI_PA.items():
        for pattern in patterns:
            if re.search(pattern, nome, re.IGNORECASE):
                return settore

    return 'Altri Enti Pubblici'

def identifica_pnrr(row):
    """Identifica contratti PNRR"""
    # Check flag
    if row.get('FLAG_PNRR_PNC') == 1 or row.get('FLAG_PNRR_PNC') == '1':
        return True

    # Check testo
    testo = f"{row.get('oggetto_lotto', '')} {row.get('oggetto_gara', '')}".lower()
    for pattern in PNRR_PATTERNS:
        if re.search(pattern, testo, re.IGNORECASE):
            return True

    return False

# ============================================================================
# FUNZIONI DI ANALISI
# ============================================================================

def calcola_statistiche_generali(df):
    """Calcola statistiche generali del dataset"""
    return {
        'totale_contratti': len(df),
        'valore_totale': round(df['importo_lotto'].sum(), 2),
        'valore_medio': round(df['importo_lotto'].mean(), 2),
        'valore_mediano': round(df['importo_lotto'].median(), 2),
        'pa_coinvolte': df['cf_amministrazione_appaltante'].nunique(),
        'province_coinvolte': df[df['provincia'] != 'N/D']['provincia'].nunique(),
        'anni_coperti': sorted(df['anno_pubblicazione'].dropna().unique().tolist()),
        'distribuzione_annuale': df.groupby('anno_pubblicazione').agg({
            'cig': 'count',
            'importo_lotto': 'sum'
        }).rename(columns={'cig': 'n_contratti', 'importo_lotto': 'valore'}).to_dict('index')
    }

def classifica_pa(df, top_n=30):
    """Classifica PA per spesa"""
    grouped = df.groupby(['cf_amministrazione_appaltante', 'denominazione_amministrazione_appaltante']).agg({
        'importo_lotto': ['sum', 'mean', 'min', 'max', 'count'],
        'provincia': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'N/D',
        'anno_pubblicazione': lambda x: sorted(x.dropna().unique().tolist()),
        'settore_pa': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Altri Enti'
    }).reset_index()

    grouped.columns = ['cf', 'denominazione', 'importo_totale', 'importo_medio',
                       'importo_min', 'importo_max', 'n_contratti', 'provincia',
                       'anni_attivita', 'settore']

    grouped = grouped.sort_values('importo_totale', ascending=False).head(top_n)
    grouped['posizione'] = range(1, len(grouped) + 1)

    return grouped.to_dict('records')

def raggruppa_per_categoria(df):
    """Raggruppa contratti per categoria AI"""
    grouped = df.groupby('categoria_ai').agg({
        'importo_lotto': 'sum',
        'cig': 'count'
    }).rename(columns={'cig': 'n_contratti', 'importo_lotto': 'valore'})

    totale = grouped['valore'].sum()
    grouped['percentuale'] = round((grouped['valore'] / totale) * 100, 2)
    grouped = grouped.sort_values('valore', ascending=False).reset_index()

    return grouped.to_dict('records')

def raggruppa_per_settore(df):
    """Raggruppa per settore PA"""
    grouped = df.groupby('settore_pa').agg({
        'importo_lotto': 'sum',
        'cig': 'count',
        'cf_amministrazione_appaltante': 'nunique'
    }).rename(columns={
        'cig': 'n_contratti',
        'importo_lotto': 'valore',
        'cf_amministrazione_appaltante': 'n_pa'
    })

    totale = grouped['valore'].sum()
    grouped['percentuale'] = round((grouped['valore'] / totale) * 100, 2)
    grouped = grouped.sort_values('valore', ascending=False).reset_index()

    return grouped.to_dict('records')

def analisi_pnrr(df):
    """Analisi contratti PNRR vs non-PNRR"""
    pnrr = df[df['is_pnrr'] == True]
    non_pnrr = df[df['is_pnrr'] == False]

    pnrr_per_anno = pnrr.groupby('anno_pubblicazione').agg({
        'cig': 'count',
        'importo_lotto': 'sum'
    }).rename(columns={'cig': 'n_contratti', 'importo_lotto': 'valore'}).to_dict('index')

    return {
        'pnrr': {
            'n_contratti': len(pnrr),
            'valore': round(pnrr['importo_lotto'].sum(), 2),
            'valore_medio': round(pnrr['importo_lotto'].mean(), 2) if len(pnrr) > 0 else 0,
            'valore_mediano': round(pnrr['importo_lotto'].median(), 2) if len(pnrr) > 0 else 0,
            'percentuale_contratti': round(len(pnrr) / len(df) * 100, 2),
            'percentuale_valore': round(pnrr['importo_lotto'].sum() / df['importo_lotto'].sum() * 100, 2),
            'per_anno': pnrr_per_anno
        },
        'non_pnrr': {
            'n_contratti': len(non_pnrr),
            'valore': round(non_pnrr['importo_lotto'].sum(), 2),
            'valore_medio': round(non_pnrr['importo_lotto'].mean(), 2) if len(non_pnrr) > 0 else 0,
            'valore_mediano': round(non_pnrr['importo_lotto'].median(), 2) if len(non_pnrr) > 0 else 0
        }
    }

# ============================================================================
# GENERAZIONE DASHBOARD HTML
# ============================================================================

def genera_dashboard_html(stats, top_pa, categorie, settori, pnrr_data, validazioni):
    """Genera dashboard HTML standalone"""

    # Prepara dati per grafici
    top10_pa = top_pa[:10]
    top10_labels = [p['denominazione'][:40] + '...' if len(p['denominazione']) > 40 else p['denominazione'] for p in top10_pa]
    top10_values = [p['importo_totale'] for p in top10_pa]

    cat_labels = [c['categoria_ai'] for c in categorie]
    cat_values = [c['valore'] for c in categorie]

    sett_labels = [s['settore_pa'] for s in settori]
    sett_values = [s['valore'] for s in settori]

    # Trend temporale
    anni = sorted(stats['distribuzione_annuale'].keys())
    trend_contratti = [stats['distribuzione_annuale'][a]['n_contratti'] for a in anni]
    trend_valori = [stats['distribuzione_annuale'][a]['valore'] / 1e6 for a in anni]

    html = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Appalti IA ANAC 2023-2025</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary: #0d6efd;
            --success: #198754;
            --warning: #ffc107;
            --danger: #dc3545;
            --info: #0dcaf0;
        }}
        body {{
            background-color: #f8f9fa;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }}
        .navbar-brand {{
            font-weight: 700;
        }}
        .kpi-card {{
            border: none;
            border-radius: 12px;
            transition: transform 0.2s;
        }}
        .kpi-card:hover {{
            transform: translateY(-5px);
        }}
        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
        }}
        .kpi-label {{
            font-size: 0.85rem;
            text-transform: uppercase;
            opacity: 0.9;
        }}
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .table-container {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .badge-settore {{
            font-size: 0.75rem;
        }}
        .alert-section {{
            margin-top: 30px;
        }}
        footer {{
            margin-top: 40px;
            padding: 20px 0;
            background: #212529;
            color: white;
        }}
        .header-section {{
            background: linear-gradient(135deg, #0d6efd 0%, #6610f2 100%);
            color: white;
            padding: 40px 0;
            margin-bottom: 30px;
        }}
        @media (max-width: 768px) {{
            .kpi-value {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header-section">
        <div class="container">
            <h1 class="mb-2">Dashboard Appalti Intelligenza Artificiale</h1>
            <p class="mb-0 opacity-75">Analisi contratti pubblici ANAC | Periodo 2023-2025 | Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
    </div>

    <div class="container">
        <!-- KPI Cards -->
        <div class="row g-3 mb-4">
            <div class="col-6 col-md-4 col-lg-2">
                <div class="card kpi-card bg-primary text-white h-100">
                    <div class="card-body text-center">
                        <div class="kpi-value">{stats['totale_contratti']:,}</div>
                        <div class="kpi-label">Contratti</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="card kpi-card bg-success text-white h-100">
                    <div class="card-body text-center">
                        <div class="kpi-value">{stats['valore_totale']/1e6:.1f}M</div>
                        <div class="kpi-label">Valore Totale</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="card kpi-card bg-info text-white h-100">
                    <div class="card-body text-center">
                        <div class="kpi-value">{stats['pa_coinvolte']:,}</div>
                        <div class="kpi-label">PA Coinvolte</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="card kpi-card bg-warning text-dark h-100">
                    <div class="card-body text-center">
                        <div class="kpi-value">{stats['valore_medio']/1e3:.0f}K</div>
                        <div class="kpi-label">Valore Medio</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="card kpi-card bg-success text-white h-100">
                    <div class="card-body text-center">
                        <div class="kpi-value">{pnrr_data['pnrr']['n_contratti']}</div>
                        <div class="kpi-label">PNRR ({pnrr_data['pnrr']['percentuale_contratti']:.1f}%)</div>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="card kpi-card bg-secondary text-white h-100">
                    <div class="card-body text-center">
                        <div class="kpi-value">{stats['province_coinvolte']}</div>
                        <div class="kpi-label">Province</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Top 10 PA -->
        <div class="chart-container">
            <h5 class="mb-3">Top 10 Amministrazioni per Spesa</h5>
            <div style="height: 400px;">
                <canvas id="chartTop10"></canvas>
            </div>
        </div>

        <!-- Row con 2 grafici -->
        <div class="row">
            <div class="col-lg-6">
                <div class="chart-container">
                    <h5 class="mb-3">Distribuzione per Categoria AI</h5>
                    <div style="height: 350px;">
                        <canvas id="chartCategorie"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="chart-container">
                    <h5 class="mb-3">Distribuzione per Settore PA</h5>
                    <div style="height: 350px;">
                        <canvas id="chartSettori"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Row PNRR e Trend -->
        <div class="row">
            <div class="col-lg-4">
                <div class="chart-container">
                    <h5 class="mb-3">PNRR vs Non-PNRR</h5>
                    <div style="height: 300px;">
                        <canvas id="chartPnrr"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-lg-8">
                <div class="chart-container">
                    <h5 class="mb-3">Trend Temporale</h5>
                    <div style="height: 300px;">
                        <canvas id="chartTrend"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tabella Top 30 PA -->
        <div class="table-container">
            <h5 class="mb-3">Top 30 Amministrazioni Appaltanti</h5>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>#</th>
                            <th>Amministrazione</th>
                            <th>Provincia</th>
                            <th>Settore</th>
                            <th class="text-end">Spesa Totale</th>
                            <th class="text-end">N. Contr.</th>
                            <th class="text-end">Media</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f'''
                        <tr>
                            <td>{p['posizione']}</td>
                            <td title="{p['denominazione']}">{p['denominazione'][:50]}{'...' if len(p['denominazione']) > 50 else ''}</td>
                            <td>{p['provincia']}</td>
                            <td><span class="badge bg-secondary badge-settore">{p['settore']}</span></td>
                            <td class="text-end fw-bold">{p['importo_totale']:,.0f}</td>
                            <td class="text-end">{p['n_contratti']}</td>
                            <td class="text-end">{p['importo_medio']:,.0f}</td>
                        </tr>
                        ''' for p in top_pa])}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Sezione Validazioni -->
        <div class="alert-section">
            <h5 class="mb-3">Validazioni e Anomalie</h5>

            {f'''
            <div class="alert alert-danger d-flex align-items-start" role="alert">
                <div>
                    <strong>Errore Critico Corretto</strong><br>
                    CIG <code>{validazioni['correzioni_applicate'][0]['cig']}</code> -
                    Importo errato €{validazioni['correzioni_applicate'][0]['valore_originale']:,.2f}
                    corretto a €{validazioni['correzioni_applicate'][0]['valore_corretto']:.2f}
                    <br><small class="text-muted">{validazioni['correzioni_applicate'][0]['motivo']}</small>
                </div>
            </div>
            ''' if validazioni.get('correzioni_applicate') else ''}

            <div class="alert alert-warning d-flex align-items-start" role="alert">
                <div>
                    <strong>Analisi Aggiudicatari Non Disponibile</strong><br>
                    I dati ANAC non contengono informazioni sulle società aggiudicatarie.
                    Per questa analisi è necessario integrare con API ANAC o fonti esterne.
                </div>
            </div>

            <div class="alert alert-info d-flex align-items-start" role="alert">
                <div>
                    <strong>Outlier Identificati</strong><br>
                    Rilevati <span class="badge bg-primary">{validazioni['importi']['n_outliers']}</span> contratti
                    con importi superiori a 3 deviazioni standard dalla media (> €{validazioni['importi']['soglia_outlier']:,.0f}).
                </div>
            </div>
        </div>
    </div>

    <footer class="text-center">
        <div class="container">
            <p class="mb-1">Dashboard Appalti IA ANAC 2023-2025</p>
            <small class="opacity-75">Fonte: ANAC - Autorità Nazionale Anticorruzione | Elaborazione: {datetime.now().strftime('%d/%m/%Y %H:%M')}</small>
        </div>
    </footer>

    <script>
        // Colori
        const colors = [
            '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545',
            '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0',
            '#6c757d', '#adb5bd', '#495057', '#212529', '#f8f9fa', '#343a40'
        ];

        // Formatta numeri
        const formatEuro = (value) => '€' + value.toLocaleString('it-IT');
        const formatMilioni = (value) => '€' + (value/1000000).toFixed(1) + 'M';

        // Grafico Top 10 PA
        new Chart(document.getElementById('chartTop10'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top10_labels)},
                datasets: [{{
                    label: 'Spesa Totale',
                    data: {json.dumps(top10_values)},
                    backgroundColor: 'rgba(13, 110, 253, 0.8)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: (ctx) => formatEuro(ctx.parsed.x)
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: (value) => formatMilioni(value)
                        }}
                    }}
                }}
            }}
        }});

        // Grafico Categorie AI
        new Chart(document.getElementById('chartCategorie'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(cat_labels)},
                datasets: [{{
                    data: {json.dumps(cat_values)},
                    backgroundColor: colors.slice(0, {len(cat_labels)}),
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{ boxWidth: 12, font: {{ size: 10 }} }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: (ctx) => {{
                                const total = ctx.dataset.data.reduce((a,b) => a+b, 0);
                                const pct = ((ctx.parsed/total)*100).toFixed(1);
                                return ctx.label + ': ' + formatEuro(ctx.parsed) + ' (' + pct + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Grafico Settori PA
        new Chart(document.getElementById('chartSettori'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(sett_labels)},
                datasets: [{{
                    label: 'Valore',
                    data: {json.dumps(sett_values)},
                    backgroundColor: colors.slice(0, {len(sett_labels)}),
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: (ctx) => formatEuro(ctx.parsed.y)
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: (value) => formatMilioni(value)
                        }}
                    }},
                    x: {{
                        ticks: {{
                            maxRotation: 45,
                            minRotation: 45,
                            font: {{ size: 10 }}
                        }}
                    }}
                }}
            }}
        }});

        // Grafico PNRR
        new Chart(document.getElementById('chartPnrr'), {{
            type: 'doughnut',
            data: {{
                labels: ['PNRR', 'Non-PNRR'],
                datasets: [{{
                    data: [{pnrr_data['pnrr']['valore']}, {pnrr_data['non_pnrr']['valore']}],
                    backgroundColor: ['#198754', '#6c757d'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom' }},
                    tooltip: {{
                        callbacks: {{
                            label: (ctx) => {{
                                const total = ctx.dataset.data.reduce((a,b) => a+b, 0);
                                const pct = ((ctx.parsed/total)*100).toFixed(1);
                                return ctx.label + ': ' + formatEuro(ctx.parsed) + ' (' + pct + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Grafico Trend
        new Chart(document.getElementById('chartTrend'), {{
            type: 'line',
            data: {{
                labels: {json.dumps([str(a) for a in anni])},
                datasets: [
                    {{
                        label: 'N. Contratti',
                        data: {json.dumps(trend_contratti)},
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1,
                        yAxisID: 'y',
                        fill: true
                    }},
                    {{
                        label: 'Valore (€M)',
                        data: {json.dumps(trend_valori)},
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1,
                        yAxisID: 'y1',
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{
                    legend: {{ position: 'top' }}
                }},
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{ display: true, text: 'N. Contratti' }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{ display: true, text: 'Valore (€M)' }},
                        grid: {{ drawOnChartArea: false }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''
    return html

def genera_report_validazioni(validazioni, filename):
    """Genera report testuale validazioni"""
    report = f'''================================================================================
REPORT VALIDAZIONI DATASET ANAC - APPALTI IA 2023-2025
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
================================================================================

1. CORREZIONI AUTOMATICHE APPLICATE
-------------------------------------------------------------------------------
'''
    if validazioni.get('correzioni_applicate'):
        for c in validazioni['correzioni_applicate']:
            report += f'''   - CIG {c['cig']}: {c['tipo']}
     Campo: {c['campo']}
     Valore originale: €{c['valore_originale']:,.2f}
     Valore corretto: €{c['valore_corretto']:.2f}
     Motivo: {c['motivo']}

'''
    else:
        report += "   Nessuna correzione applicata.\n\n"

    report += f'''
2. STATISTICHE IMPORTI
-------------------------------------------------------------------------------
   Media: €{validazioni['importi']['media']:,.2f}
   Mediana: €{validazioni['importi']['mediana']:,.2f}
   Deviazione standard: €{validazioni['importi']['std']:,.2f}
   Soglia outlier (3σ): €{validazioni['importi']['soglia_outlier']:,.2f}
   Numero outlier identificati: {validazioni['importi']['n_outliers']}
   Contratti con importo zero: {validazioni['importi']['n_importo_zero']}

3. VALIDAZIONE DATE
-------------------------------------------------------------------------------
   Date future: {validazioni['date']['n_date_future']}
   Anni incoerenti: {validazioni['date']['n_anni_incoerenti']}
   Date mancanti: {validazioni['date']['date_mancanti']}

4. CAMPI OBBLIGATORI MANCANTI
-------------------------------------------------------------------------------
'''
    if validazioni['campi']:
        for campo, info in validazioni['campi'].items():
            report += f"   {campo}: {info['mancanti']} record ({info['percentuale']}%)\n"
    else:
        report += "   Tutti i campi obbligatori sono presenti.\n"

    report += f'''
5. OUTLIER PRINCIPALI (Top 10)
-------------------------------------------------------------------------------
'''
    for i, o in enumerate(validazioni['importi']['outliers'][:10], 1):
        report += f'''   {i}. CIG: {o['cig']}
      PA: {o['denominazione_amministrazione_appaltante'][:60]}
      Importo: €{o['importo_lotto']:,.2f}

'''

    report += '''
================================================================================
FINE REPORT
================================================================================
'''

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ Report validazioni salvato: {filename}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("ANALISI APPALTI IA ANAC 2023-2025")
    print("=" * 70)
    print()

    # 1. Caricamento dati
    print("1. CARICAMENTO DATI")
    print("-" * 40)
    df = carica_csv(INPUT_FILES)

    # 2. Pulizia
    print("\n2. PULIZIA DATI")
    print("-" * 40)
    df = pulisci_dati(df)
    print("✓ Dati puliti e normalizzati")

    # 3. Validazioni
    print("\n3. VALIDAZIONI")
    print("-" * 40)
    validazioni = {
        'importi': valida_importi(df),
        'date': valida_date(df),
        'campi': valida_campi(df)
    }
    print(f"✓ Outlier identificati: {validazioni['importi']['n_outliers']}")

    # 4. Correzioni
    print("\n4. CORREZIONI")
    print("-" * 40)
    df = applica_correzioni(df, validazioni)

    # 5. Categorizzazioni
    print("\n5. CATEGORIZZAZIONI")
    print("-" * 40)
    df['categoria_ai'] = df.apply(categorizza_ai, axis=1)
    df['settore_pa'] = df.apply(categorizza_settore, axis=1)
    df['is_pnrr'] = df.apply(identifica_pnrr, axis=1)
    print(f"✓ Categorie AI assegnate: {df['categoria_ai'].nunique()}")
    print(f"✓ Settori PA assegnati: {df['settore_pa'].nunique()}")
    print(f"✓ Contratti PNRR: {df['is_pnrr'].sum()}")

    # 6. Calcolo statistiche
    print("\n6. CALCOLO STATISTICHE")
    print("-" * 40)
    stats = calcola_statistiche_generali(df)
    top_pa = classifica_pa(df, 30)
    categorie = raggruppa_per_categoria(df)
    settori = raggruppa_per_settore(df)
    pnrr_data = analisi_pnrr(df)

    print(f"✓ Totale contratti: {stats['totale_contratti']}")
    print(f"✓ Valore totale: €{stats['valore_totale']:,.2f}")
    print(f"✓ PA coinvolte: {stats['pa_coinvolte']}")

    # 7. Generazione output
    print("\n7. GENERAZIONE OUTPUT")
    print("-" * 40)

    # Dashboard HTML
    html = genera_dashboard_html(stats, top_pa, categorie, settori, pnrr_data, validazioni)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✓ Dashboard salvata: index.html")

    # JSON dati processati
    output_json = {
        'metadata': {
            'data_elaborazione': datetime.now().isoformat(),
            'totale_contratti': stats['totale_contratti'],
            'valore_totale': stats['valore_totale'],
            'anni': [str(a) for a in stats['anni_coperti']],
            'correzioni_applicate': validazioni.get('correzioni_applicate', [])
        },
        'statistiche_generali': stats,
        'top_pa': top_pa,
        'categorie_ai': categorie,
        'settori_pa': settori,
        'pnrr': pnrr_data,
        'validazioni': {
            'importi': {k: v for k, v in validazioni['importi'].items() if k != 'outliers'},
            'date': validazioni['date'],
            'campi': validazioni['campi']
        }
    }

    with open('dati_processati.json', 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False, default=str)
    print("✓ Dati JSON salvati: dati_processati.json")

    # CSV corretto
    df['importo_corretto'] = df['importo_lotto']
    df['is_outlier'] = df['importo_lotto'] > validazioni['importi']['soglia_outlier']
    df.to_csv('dataset_corretto.csv', index=False, sep=';', encoding='utf-8-sig')
    print("✓ Dataset corretto salvato: dataset_corretto.csv")

    # Report validazioni
    genera_report_validazioni(validazioni, 'report_validazioni.txt')

    print("\n" + "=" * 70)
    print("ELABORAZIONE COMPLETATA")
    print("=" * 70)
    print(f"\nRiepilogo finale:")
    print(f"  - Totale contratti: {stats['totale_contratti']}")
    print(f"  - Valore totale: €{stats['valore_totale']:,.2f}")
    print(f"  - PA coinvolte: {stats['pa_coinvolte']}")
    print(f"  - Top PA: {top_pa[0]['denominazione'][:50]} (€{top_pa[0]['importo_totale']:,.0f})")
    print(f"  - Contratti PNRR: {pnrr_data['pnrr']['n_contratti']} ({pnrr_data['pnrr']['percentuale_contratti']:.1f}%)")

    return df, stats, validazioni

if __name__ == '__main__':
    main()
