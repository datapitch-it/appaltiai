#!/usr/bin/env bash
# ============================================================================
# 01_extract_cig.sh - Download CIG data from ANAC and filter AI contracts
#
# Usage:
#   ./scripts/01_extract_cig.sh 2025
#   ./scripts/01_extract_cig.sh 2023 2024 2025
#   ./scripts/01_extract_cig.sh --all  # processes 2023-2025
#
# Output:
#   appalti_ia_YYYY_anac.csv for each year
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WORK_DIR="$PROJECT_DIR/.tmp_extract"
BASE_URL="https://dati.anticorruzione.it/opendata/download/dataset"

# AI keywords (grep -i -E pattern)
AI_PATTERN="intelligenza artificiale|artificial intelligence|machine learning|deep learning|apprendimento automatico"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*" >&2; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Determine which years to process
resolve_years() {
    if [[ "${1:-}" == "--all" ]]; then
        echo "2023 2024 2025"
    elif [[ $# -eq 0 ]]; then
        echo "2025"
    else
        echo "$@"
    fi
}

# Download and extract CSV for a single month
download_month() {
    local year=$1
    local month=$2
    local month_padded
    month_padded=$(printf "%02d" "$month")
    local zip_file="$WORK_DIR/cig_csv_${year}_${month_padded}.zip"
    local csv_dir="$WORK_DIR/cig_${year}_${month_padded}"
    local csv_file="$csv_dir/cig_csv_${year}_${month_padded}.csv"
    local url="${BASE_URL}/cig-${year}/filesystem/cig_csv_${year}_${month_padded}.zip"

    if [[ -f "$csv_file" ]]; then
        return 0
    fi

    curl -sL "$url" -o "$zip_file" 2>/dev/null
    if [[ ! -s "$zip_file" ]]; then
        rm -f "$zip_file"
        return 1
    fi

    mkdir -p "$csv_dir"
    unzip -o -q "$zip_file" -d "$csv_dir" 2>/dev/null || {
        rm -f "$zip_file"
        return 1
    }
    rm -f "$zip_file"

    if [[ ! -f "$csv_file" ]]; then
        return 1
    fi
    return 0
}

# Process a single year
process_year() {
    local year=$1
    local output_csv="$PROJECT_DIR/appalti_ia_${year}_anac.csv"

    log_info "Processing year $year..."

    # Download all months in parallel
    local pids=()
    local available_months=()
    for month in $(seq 1 12); do
        download_month "$year" "$month" &
        pids+=($!)
    done

    # Wait and collect results
    local month=0
    for pid in "${pids[@]}"; do
        month=$((month + 1))
        if wait "$pid" 2>/dev/null; then
            available_months+=("$month")
        fi
    done

    if [[ ${#available_months[@]} -eq 0 ]]; then
        log_error "No data available for year $year"
        return 1
    fi

    log_info "  Downloaded ${#available_months[@]}/12 months"

    # Extract header from first available month
    local first_month
    first_month=$(printf "%02d" "${available_months[0]}")
    local first_csv="$WORK_DIR/cig_${year}_${first_month}/cig_csv_${year}_${first_month}.csv"
    head -1 "$first_csv" > "$output_csv"

    # Filter AI contracts from all months
    local total_rows=0
    local ai_rows=0
    for month in "${available_months[@]}"; do
        local month_padded
        month_padded=$(printf "%02d" "$month")
        local csv_file="$WORK_DIR/cig_${year}_${month_padded}/cig_csv_${year}_${month_padded}.csv"

        local month_total
        month_total=$(($(wc -l < "$csv_file") - 1))
        total_rows=$((total_rows + month_total))

        local month_ai
        month_ai=$(tail -n +2 "$csv_file" | grep -i -E "$AI_PATTERN" | tee -a "$output_csv.tmp" | wc -l)
        ai_rows=$((ai_rows + month_ai))
    done

    # Deduplicate by CIG (first field) keeping first occurrence
    if [[ -f "$output_csv.tmp" ]]; then
        sort -t';' -k1,1 -u "$output_csv.tmp" >> "$output_csv"
        rm -f "$output_csv.tmp"
    fi

    # Count final deduplicated rows
    local final_count
    final_count=$(($(wc -l < "$output_csv") - 1))

    log_ok "  Year $year: $total_rows total CIG -> $ai_rows AI matches -> $final_count unique CIG"
    log_ok "  Output: $output_csv"

    echo "$final_count"
}

# Cleanup temp files
cleanup() {
    if [[ -d "$WORK_DIR" ]]; then
        rm -rf "$WORK_DIR"
        log_info "Cleaned up temporary files"
    fi
}

# Main
main() {
    local years
    years=$(resolve_years "$@")

    echo "============================================================"
    echo " ANAC CIG Extraction - AI Procurement Contracts"
    echo "============================================================"
    echo ""
    log_info "Years to process: $years"
    echo ""

    mkdir -p "$WORK_DIR"
    trap cleanup EXIT

    local grand_total=0
    for year in $years; do
        count=$(process_year "$year") || continue
        grand_total=$((grand_total + count))
        echo ""
    done

    echo "============================================================"
    log_ok "Extraction complete. Total AI contracts: $grand_total"
    echo "============================================================"
}

main "$@"
