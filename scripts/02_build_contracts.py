#!/usr/bin/env python3
"""
02_build_contracts.py - Convert extracted ANAC CSVs to data/contracts.json

Reads appalti_ia_YYYY_anac.csv files, applies:
  - Deduplication by CIG
  - Data cleaning and normalization
  - AI category classification
  - PA sector classification
  - PNRR identification
  - Quality checks and validation

Usage:
    python scripts/02_build_contracts.py
    python scripts/02_build_contracts.py --years 2025
    python scripts/02_build_contracts.py --years 2023 2024 2025
"""

import csv
import json
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import Counter

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_YEARS = ["2023", "2024", "2025"]
OUTPUT_FILE = PROJECT_DIR / "data" / "contracts.json"

# Known data corrections
CORRECTIONS = {
    "B1B36B1A1E": {
        "field": "importo_lotto",
        "wrong_value": 293893058.00,
        "correct_value": 357.85,
        "reason": "Acquisto libri biblioteca (confronto CIG B1AA21EEA3, B1B748D667)"
    }
}

# ============================================================================
# AI CATEGORY PATTERNS
# ============================================================================

CATEGORIE_AI = {
    "AI Generativa & LLM": [
        r"ai generativa", r"llm", r"gpt", r"chatbot", r"chat bot",
        r"assistente virtuale", r"conversazional", r"generative ai",
        r"open\s*ai", r"copilot", r"digital human"
    ],
    "Machine Learning & Analytics": [
        r"machine learning", r"ml(?:\s|$)", r"deep learning",
        r"predittiv", r"analytics", r"analisi dati", r"data science",
        r"big data", r"rete neural", r"neural network"
    ],
    "Computer Vision": [
        r"visione artificiale", r"computer vision", r"riconoscimento immagini",
        r"detection", r"rilevamento", r"video analytics", r"ocr",
        r"image processing", r"elaborazione immagini"
    ],
    "NLP & Speech": [
        r"nlp", r"natural language", r"elaborazione linguaggio",
        r"speech", r"vocale", r"riconoscimento vocale", r"text mining",
        r"sentiment analysis", r"text to speech"
    ],
    "RPA & Automazione": [
        r"rpa", r"robotic process", r"automazione", r"workflow automation",
        r"processo automatizzato", r"automazione processo"
    ],
    "Formazione IA": [
        r"formazione.*(?:ia|ai|intelligenza artificiale)",
        r"corso.*(?:ia|ai|intelligenza artificiale)",
        r"training.*(?:ia|ai)", r"didattica.*(?:ia|ai)",
        r"insegnamento.*(?:ia|ai)", r"master.*intelligenza",
        r"seminari?.*(?:ia|ai|intelligenza)", r"mooc.*intelligenza",
        r"laboratori?.*(?:ia|ai|intelligenza)", r"percors.*formativ"
    ],
    "Cybersecurity IA": [
        r"cybersecurity.*(?:ia|ai)", r"sicurezza.*intelligenza artificiale",
        r"threat detection", r"anomaly detection.*security",
        r"cyber.*intelligenza", r"darktrace", r"monitoraggio.*anomalie"
    ],
    "Healthcare IA": [
        r"diagnostica.*(?:ia|ai)", r"medical.*ai", r"radiologia.*(?:ia|ai)",
        r"telemedicina.*(?:ia|ai)", r"clinical.*ai", r"pathology.*ai",
        r"polipi", r"colonscopia", r"endoscopia.*(?:ia|ai)",
        r"mammograf", r"ictus", r"stroke", r"neuroradiologia",
        r"boneview", r"rapidai", r"zeeromed", r"ecocardiograf",
        r"morfologic.*vetrini"
    ],
    "Biometria": [
        r"biometric", r"facial recognition", r"riconoscimento facciale",
        r"fingerprint", r"impronta digitale", r"iris recognition"
    ],
    "Document Intelligence": [
        r"document.*intelligence", r"protocollazione.*(?:ia|ai)",
        r"gestione documentale.*(?:ia|ai)", r"archiviazione.*(?:ia|ai)",
        r"ocr.*(?:ia|ai)"
    ],
    "IoT & Edge AI": [
        r"iot.*(?:ia|ai)", r"edge.*(?:ia|ai)", r"smart.*sensor",
        r"sensori.*intelligenti", r"social robot"
    ],
    "Recommendation Systems": [
        r"recommendation", r"raccomandazione", r"suggerimento automatico",
        r"personalizzazione.*(?:ia|ai)"
    ],
    "AI Ethics & Governance": [
        r"etica.*(?:ia|ai)", r"governance.*(?:ia|ai)", r"responsible.*ai",
        r"trustworthy.*ai", r"ai act", r"trasparenza.*(?:ia|ai|intelligenza)"
    ],
    "Infrastruttura IA": [
        r"gpu", r"cuda", r"tensorflow", r"pytorch", r"cloud.*(?:ia|ai)",
        r"infrastructure.*ai", r"computing.*(?:ia|ai)", r"calcolo.*(?:ia|ai)",
        r"server.*(?:gpu|hpc|ai)", r"workstation.*(?:ia|ai)",
        r"nvidia", r"hpc4ai", r"multi-gpu"
    ],
    "Consulenza IA": [
        r"consulenza.*(?:ia|ai|intelligenza)", r"advisory.*ai",
        r"supporto.*intelligenza artificiale", r"assessment.*ai",
        r"osservatorio.*intelligenza"
    ]
}

# ============================================================================
# PA SECTOR PATTERNS
# ============================================================================

SETTORI_PA = {
    "Sanità": [
        r"\basl\b", r"azienda sanitaria", r"ospedale", r"\birccs\b", r"agenas",
        r"policlinico", r"\busl\b", r"\bausl\b", r"\basst\b", r"\bats\b",
        r"\baou\b", r"\basp\b", r"ospedalier[ao]", r"azienda.*sanitar",
        r"azienda.*colli", r"fondazione.*pascale", r"fondazione.*policlinico"
    ],
    "Università e Ricerca": [
        r"universit[àa]", r"university", r"politecnico", r"\bcnr\b",
        r"scuola superiore", r"istituto nazionale", r"\binfn\b", r"\benea\b",
        r"istituto superiore", r"ricerca metrologica", r"crea", r"inrim"
    ],
    "PA Centrale": [
        r"ministero", r"agenzia entrate", r"\binps\b", r"\binail\b", r"\baci\b",
        r"agenzia nazionale", r"\bagid\b", r"sogei", r"consip", r"agenzia dogane",
        r"presidenza.*consiglio", r"commissione.*borsa", r"consob",
        r"agenzia spaziale", r"\bice\b.*agenzia", r"\benit\b"
    ],
    "PA Locale": [
        r"\bcomune\b", r"\bprovincia\b", r"\bregione\b", r"citt[àa] metropolitana",
        r"municipio", r"unione comuni", r"comunit[àa] montana",
        r"camera.*commercio", r"c\.c\.i\.a"
    ],
    "Istruzione": [
        r"istituto comprensivo", r"\bliceo\b", r"istituto tecnico",
        r"istituto professionale", r"convitto", r"\bscuola\b",
        r"direzione didattica", r"circolo didattico", r"\bits\b.*academy",
        r"istituto.*istruzione.*superiore", r"i\.i\.s\."
    ],
    "Difesa e Sicurezza": [
        r"\bdifesa\b", r"carabinieri", r"polizia", r"guardia.*finanza",
        r"vigili.*fuoco", r"esercito", r"\bmarina\b", r"aeronautica",
        r"corpo forestale", r"interno.*p\.?s\.?", r"comando.*rete"
    ],
    "Utilities & Trasporti": [
        r"\brai\b", r"trenitalia", r"\brfi\b", r"\banas\b", r"\benav\b",
        r"\bacea\b", r"\batac\b", r"\batm\b", r"\bamat\b", r"metropolitana",
        r"ferrovie", r"\bamtab\b", r"\bhera\b", r"\bcap\b.*holding",
        r"acquevenete", r"ve\.la\b"
    ],
    "Enti Pubblici Economici": [
        r"cassa depositi", r"\bcdp\b", r"\beur\b.*spa", r"invitalia", r"\bsace\b",
        r"banca.*italia", r"digital library"
    ],
    "Giustizia": [
        r"tribunale", r"\bcorte\b", r"\bprocura\b", r"consiglio.*magistratura",
        r"avvocatura", r"\btar\b", r"consiglio.*stato"
    ]
}

PNRR_PATTERNS = [
    r"\bpnrr\b", r"piano nazionale ripresa", r"next generation",
    r"\bngeu\b", r"recovery fund", r"recovery plan", r"\brrf\b",
    r"d\.?m\.?\s*66", r"m4c1"
]

# CSV field mapping (all fields from ANAC CIG dataset)
CSV_FIELDS = [
    "cig", "cig_accordo_quadro", "numero_gara", "oggetto_gara",
    "importo_complessivo_gara", "n_lotti_componenti", "oggetto_lotto",
    "importo_lotto", "oggetto_principale_contratto", "stato", "settore",
    "luogo_istat", "provincia", "data_pubblicazione", "data_scadenza_offerta",
    "cod_tipo_scelta_contraente", "tipo_scelta_contraente",
    "cod_modalita_realizzazione", "modalita_realizzazione", "codice_ausa",
    "cf_amministrazione_appaltante", "denominazione_amministrazione_appaltante",
    "sezione_regionale", "id_centro_costo", "denominazione_centro_costo",
    "anno_pubblicazione", "mese_pubblicazione", "cod_cpv", "descrizione_cpv",
    "flag_prevalente", "COD_MOTIVO_CANCELLAZIONE", "MOTIVO_CANCELLAZIONE",
    "DATA_CANCELLAZIONE", "DATA_ULTIMO_PERFEZIONAMENTO",
    "COD_MODALITA_INDIZIONE_SPECIALI", "MODALITA_INDIZIONE_SPECIALI",
    "COD_MODALITA_INDIZIONE_SERVIZI", "MODALITA_INDIZIONE_SERVIZI",
    "DURATA_PREVISTA", "COD_STRUMENTO_SVOLGIMENTO", "STRUMENTO_SVOLGIMENTO",
    "FLAG_URGENZA", "COD_MOTIVO_URGENZA", "MOTIVO_URGENZA", "FLAG_DELEGA",
    "FUNZIONI_DELEGATE", "CF_SA_DELEGANTE", "DENOMINAZIONE_SA_DELEGANTE",
    "CF_SA_DELEGATA", "DENOMINAZIONE_SA_DELEGATA", "IMPORTO_SICUREZZA",
    "TIPO_APPALTO_RISERVATO", "CUI_PROGRAMMA", "FLAG_PREV_RIPETIZIONI",
    "COD_IPOTESI_COLLEGAMENTO", "IPOTESI_COLLEGAMENTO", "CIG_COLLEGAMENTO",
    "COD_ESITO", "ESITO", "DATA_COMUNICAZIONE_ESITO", "FLAG_PNRR_PNC"
]


# ============================================================================
# CLASSIFICATION FUNCTIONS
# ============================================================================

def classify_ai_category(oggetto_lotto, oggetto_gara):
    """Classify contract by AI category based on text content."""
    text = f"{oggetto_lotto} {oggetto_gara}".lower()
    for category, patterns in CATEGORIE_AI.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return category
    return "Altre applicazioni IA"


def classify_pa_sector(denominazione):
    """Classify PA by sector based on name."""
    name = denominazione.lower()
    for sector, patterns in SETTORI_PA.items():
        for pattern in patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return sector
    return "Altri Enti Pubblici"


def is_pnrr(row):
    """Check if contract is PNRR-funded."""
    flag = str(row.get("FLAG_PNRR_PNC", "")).strip()
    if flag == "1":
        return True
    text = f"{row.get('oggetto_lotto', '')} {row.get('oggetto_gara', '')}".lower()
    for pattern in PNRR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ============================================================================
# DATA LOADING AND CLEANING
# ============================================================================

def clean_value(value):
    """Clean a CSV field value - normalize empty strings to None."""
    if value is None:
        return None
    v = value.strip().strip('"')
    if v == "" or v.lower() == "nan":
        return None
    return v


def parse_float(value):
    """Parse a float value, returning None for invalid values."""
    v = clean_value(value)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def load_csv(filepath, year):
    """Load a single ANAC CSV file and return list of dicts."""
    records = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            record = {}
            for field in CSV_FIELDS:
                record[field] = clean_value(row.get(field))
            record["anno_dataset"] = year
            records.append(record)
    return records


def apply_corrections(records):
    """Apply known data corrections."""
    corrections_applied = []
    for record in records:
        cig = record.get("cig")
        if cig in CORRECTIONS:
            correction = CORRECTIONS[cig]
            field = correction["field"]
            old_val = parse_float(record.get(field))
            record[field] = str(correction["correct_value"])
            if field == "importo_lotto":
                record["importo_complessivo_gara"] = str(correction["correct_value"])
            corrections_applied.append({
                "cig": cig,
                "field": field,
                "old_value": old_val,
                "new_value": correction["correct_value"],
                "reason": correction["reason"]
            })
            print(f"  [CORRECTED] CIG {cig}: {field} {old_val} -> {correction['correct_value']}")
    return corrections_applied


# ============================================================================
# VALIDATION
# ============================================================================

def validate_records(records):
    """Run quality checks on records."""
    issues = {
        "missing_cig": 0,
        "missing_oggetto": 0,
        "missing_importo": 0,
        "missing_pa": 0,
        "zero_importo": 0,
        "negative_importo": 0,
        "total": len(records)
    }

    for r in records:
        if not r.get("cig"):
            issues["missing_cig"] += 1
        if not r.get("oggetto_lotto") and not r.get("oggetto_gara"):
            issues["missing_oggetto"] += 1
        importo = parse_float(r.get("importo_lotto"))
        if importo is None:
            issues["missing_importo"] += 1
        elif importo == 0:
            issues["zero_importo"] += 1
        elif importo < 0:
            issues["negative_importo"] += 1
        if not r.get("denominazione_amministrazione_appaltante"):
            issues["missing_pa"] += 1

    return issues


def print_validation_report(issues):
    """Print validation summary."""
    print(f"\n  Validation Report ({issues['total']} records):")
    for key, count in issues.items():
        if key == "total":
            continue
        if count > 0:
            pct = (count / issues["total"]) * 100
            status = "[WARN]" if pct > 5 else "[OK]"
            print(f"    {status} {key}: {count} ({pct:.1f}%)")
        else:
            print(f"    [OK] {key}: 0")


# ============================================================================
# ENRICHMENT
# ============================================================================

def enrich_records(records):
    """Add AI category, PA sector, PNRR flag to each record."""
    for r in records:
        r["categoria_ai"] = classify_ai_category(
            r.get("oggetto_lotto", "") or "",
            r.get("oggetto_gara", "") or ""
        )
        r["settore_pa"] = classify_pa_sector(
            r.get("denominazione_amministrazione_appaltante", "") or ""
        )
        r["is_pnrr"] = is_pnrr(r)

    # Print category distribution
    cat_counts = Counter(r["categoria_ai"] for r in records)
    print(f"\n  AI Categories ({len(cat_counts)} categories):")
    for cat, count in cat_counts.most_common():
        print(f"    {cat}: {count}")

    sector_counts = Counter(r["settore_pa"] for r in records)
    print(f"\n  PA Sectors ({len(sector_counts)} sectors):")
    for sec, count in sector_counts.most_common():
        print(f"    {sec}: {count}")

    pnrr_count = sum(1 for r in records if r["is_pnrr"])
    print(f"\n  PNRR contracts: {pnrr_count} ({pnrr_count/len(records)*100:.1f}%)")


# ============================================================================
# DEDUPLICATION
# ============================================================================

def deduplicate(records):
    """Deduplicate by CIG, keeping the record from the most recent dataset year."""
    by_cig = {}
    duplicates = 0
    for r in records:
        cig = r.get("cig")
        if not cig:
            continue
        if cig in by_cig:
            duplicates += 1
            # Keep the one from the most recent dataset year
            existing_year = by_cig[cig].get("anno_dataset", "0")
            new_year = r.get("anno_dataset", "0")
            if new_year > existing_year:
                by_cig[cig] = r
        else:
            by_cig[cig] = r

    if duplicates > 0:
        print(f"  [DEDUP] Removed {duplicates} duplicate CIG entries")

    return list(by_cig.values())


# ============================================================================
# MAIN
# ============================================================================

def main():
    years = DEFAULT_YEARS
    if len(sys.argv) > 1:
        if sys.argv[1] == "--years":
            years = sys.argv[2:]
        else:
            years = sys.argv[1:]

    print("=" * 60)
    print(" Build contracts.json from ANAC CSVs")
    print("=" * 60)

    # 1. Load CSVs
    all_records = []
    for year in years:
        csv_path = PROJECT_DIR / f"appalti_ia_{year}_anac.csv"
        if not csv_path.exists():
            print(f"\n[SKIP] {csv_path.name} not found")
            continue
        print(f"\n[LOAD] {csv_path.name}")
        records = load_csv(csv_path, year)
        print(f"  Loaded {len(records)} records")
        all_records.extend(records)

    if not all_records:
        print("\n[ERROR] No records loaded. Run 01_extract_cig.sh first.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f" Total loaded: {len(all_records)} records from {len(years)} year(s)")
    print(f"{'='*60}")

    # 2. Deduplicate
    print("\n[STEP] Deduplication...")
    records = deduplicate(all_records)
    print(f"  Final unique records: {len(records)}")

    # 3. Apply corrections
    print("\n[STEP] Applying corrections...")
    corrections = apply_corrections(records)
    if not corrections:
        print("  No corrections needed")

    # 4. Validate
    print("\n[STEP] Validation...")
    issues = validate_records(records)
    print_validation_report(issues)

    # 5. Enrich
    print("\n[STEP] Enrichment (AI categories, PA sectors, PNRR)...")
    enrich_records(records)

    # 6. Sort by date (newest first)
    records.sort(
        key=lambda r: r.get("data_pubblicazione") or "0000-00-00",
        reverse=True
    )

    # 7. Write output
    print(f"\n[STEP] Writing {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False, default=str)

    file_size = OUTPUT_FILE.stat().st_size
    print(f"  Written {len(records)} records ({file_size/1024/1024:.1f} MB)")

    # 8. Summary
    year_counts = Counter(r.get("anno_dataset") for r in records)
    total_value = sum(parse_float(r.get("importo_lotto")) or 0 for r in records)

    print(f"\n{'='*60}")
    print(f" Summary")
    print(f"{'='*60}")
    print(f"  Total contracts: {len(records)}")
    print(f"  Total value: EUR {total_value:,.2f}")
    print(f"  By year:")
    for year in sorted(year_counts.keys()):
        print(f"    {year}: {year_counts[year]} contracts")
    if corrections:
        print(f"  Corrections applied: {len(corrections)}")
    print(f"\n  Output: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
