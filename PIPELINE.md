# Pipeline Dati Appalti IA - Istruzioni per l'AI

Questo documento descrive come estrarre, filtrare e costruire il dataset degli appalti pubblici italiani relativi all'intelligenza artificiale, a partire dai dati ANAC (dati.anticorruzione.it).

## Prerequisiti

- Python 3.x
- bash, curl, unzip (disponibili su Linux/macOS)
- Connessione internet (per scaricare da dati.anticorruzione.it)
- Working directory: root del progetto (`/home/nelsonmau/Coding/infonodes/appalti-ai`)

## Esecuzione rapida

```bash
# Pipeline completa (2023-2025): scarica da ANAC + costruisce contracts.json
./scripts/pipeline.sh

# Solo un anno specifico
./scripts/pipeline.sh 2025

# Solo anni specifici
./scripts/pipeline.sh 2023 2024

# Ricostruire contracts.json senza riscaricare (usa CSV già presenti)
./scripts/pipeline.sh --skip-extract
```

## Step-by-step dettagliato

### Step 1: Estrazione da ANAC

```bash
./scripts/01_extract_cig.sh 2023 2024 2025
```

**Cosa fa:**
1. Per ogni anno, scarica i 12 file ZIP mensili da `https://dati.anticorruzione.it/opendata/download/dataset/cig-YYYY/filesystem/cig_csv_YYYY_MM.zip`
2. Estrae i CSV dai ZIP
3. Filtra le righe che contengono (case-insensitive): `intelligenza artificiale`, `artificial intelligence`, `machine learning`, `deep learning`, `apprendimento automatico`
4. Deduplica per CIG (primo campo del CSV)
5. Produce: `appalti_ia_YYYY_anac.csv` nella root del progetto (un file per anno)

**Output atteso (indicativo, i numeri crescono nel tempo):**
- `appalti_ia_2023_anac.csv` (~143 record)
- `appalti_ia_2024_anac.csv` (~422 record)
- `appalti_ia_2025_anac.csv` (~737 record)

**Formato CSV:** separatore `;`, quoting `"`, encoding `utf-8-sig`, 61 colonne. L'header è identico a quello dei CSV ANAC originali.

**Tempo di esecuzione:** 3-8 minuti per anno (dipende dalla connessione). I download dei 12 mesi avvengono in parallelo.

**File temporanei:** vengono creati in `.tmp_extract/` e rimossi automaticamente alla fine.

### Step 2: Costruzione contracts.json

```bash
python3 scripts/02_build_contracts.py --years 2023 2024 2025
```

**Cosa fa (in ordine):**
1. **Caricamento**: legge i file `appalti_ia_YYYY_anac.csv` dalla root del progetto
2. **Deduplicazione cross-anno**: se lo stesso CIG appare in più anni, tiene la versione dal dataset più recente
3. **Correzioni note**: applica correzioni hardcoded (es. CIG `B1B36B1A1E`: importo errato €293M corretto a €357.85)
4. **Validazione**: verifica campi obbligatori (cig, oggetto, importo, PA), segnala importi zero/negativi
5. **Classificazione AI**: assegna una delle 16 categorie (`AI Generativa & LLM`, `Machine Learning & Analytics`, `Formazione IA`, ecc.) in base a pattern regex su `oggetto_lotto` + `oggetto_gara`
6. **Classificazione PA**: assegna uno dei 10 settori (`Sanità`, `PA Centrale`, `Università e Ricerca`, ecc.) in base a pattern regex su `denominazione_amministrazione_appaltante`
7. **Identificazione PNRR**: flag `is_pnrr` = true se `FLAG_PNRR_PNC` == "1" oppure se il testo contiene pattern PNRR
8. **Ordinamento**: per `data_pubblicazione` decrescente (più recenti prima)
9. **Scrittura**: produce `data/contracts.json` (array JSON)

**Output:** `data/contracts.json` - array JSON con tutti i record arricchiti. Ogni record ha i 61 campi ANAC originali + 3 campi aggiunti: `anno_dataset`, `categoria_ai`, `settore_pa`, `is_pnrr`.

## Struttura dei file

```
appalti-ai/
├── scripts/
│   ├── 01_extract_cig.sh        # Step 1: download + filtro
│   ├── 02_build_contracts.py    # Step 2: pulizia + arricchimento
│   └── pipeline.sh              # Orchestratore
├── appalti_ia_2023_anac.csv     # Output step 1 (intermedio)
├── appalti_ia_2024_anac.csv     # Output step 1 (intermedio)
├── appalti_ia_2025_anac.csv     # Output step 1 (intermedio)
├── data/
│   └── contracts.json           # Output finale (usato dal frontend)
├── js/
│   └── app.js                   # Frontend - legge contracts.json
├── css/
│   └── style.css
└── index.html                   # Dashboard HTML
```

## Fonte dati

- **Server CKAN**: `https://dati.anticorruzione.it/opendata` (CKAN 2.6.8)
- **Dataset**: `cig-YYYY` per ogni anno (es. `cig-2025`)
- **Risorse**: 12 file CSV mensili per anno, compressi in ZIP
- **URL pattern**: `https://dati.anticorruzione.it/opendata/download/dataset/cig-YYYY/filesystem/cig_csv_YYYY_MM.zip`
- **Licenza**: CC-BY-SA 4.0

## Keyword di filtro IA

La ricerca è case-insensitive e avviene su tutta la riga CSV (tutti i campi):

| Keyword | Lingua |
|---------|--------|
| `intelligenza artificiale` | IT |
| `artificial intelligence` | EN |
| `machine learning` | EN |
| `deep learning` | EN |
| `apprendimento automatico` | IT |

## Categorie AI assegnate

Le categorie vengono assegnate in base al primo match trovato (ordine di priorità):

1. AI Generativa & LLM
2. Machine Learning & Analytics
3. Computer Vision
4. NLP & Speech
5. RPA & Automazione
6. Formazione IA
7. Cybersecurity IA
8. Healthcare IA
9. Biometria
10. Document Intelligence
11. IoT & Edge AI
12. Recommendation Systems
13. AI Ethics & Governance
14. Infrastruttura IA
15. Consulenza IA
16. Altre applicazioni IA (fallback)

## Aggiungere un nuovo anno

Per aggiungere il 2026 quando sarà disponibile:

```bash
# Verifica che il dataset esista su ANAC
# (il dataset cig-2026 deve esistere su dati.anticorruzione.it)

# Esegui la pipeline includendo il nuovo anno
./scripts/pipeline.sh 2023 2024 2025 2026
```

Non serve modificare alcun codice. Lo script 01 scaricherà automaticamente i mesi disponibili per quell'anno (anche se non sono ancora tutti e 12).

## Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| `Address already in use` quando testi con `python3 -m http.server` | Usa una porta diversa: `python3 -m http.server 9999` |
| Lo step 1 fallisce su un anno | Il dataset `cig-YYYY` potrebbe non esistere ancora su ANAC. Verifica su https://dati.anticorruzione.it/opendata |
| I CSV intermedi esistono già e vuoi solo ricostruire il JSON | Usa `./scripts/pipeline.sh --skip-extract` |
| Il frontend mostra dati vecchi dopo un rebuild | Hard refresh nel browser: `Ctrl+Shift+R` |
| Lo step 1 è lento | I download dei 12 mesi avvengono in parallelo. Se la connessione è lenta, è normale. |
