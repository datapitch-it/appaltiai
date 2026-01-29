#!/usr/bin/env bash
# ============================================================================
# pipeline.sh - Full data pipeline: extract from ANAC -> build contracts.json
#
# Usage:
#   ./scripts/pipeline.sh              # Process all years (2023-2025)
#   ./scripts/pipeline.sh 2025         # Process only 2025
#   ./scripts/pipeline.sh 2023 2024    # Process specific years
#   ./scripts/pipeline.sh --skip-extract  # Skip download, rebuild from existing CSVs
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

SKIP_EXTRACT=false
YEARS=()

# Parse args
for arg in "$@"; do
    if [[ "$arg" == "--skip-extract" ]]; then
        SKIP_EXTRACT=true
    else
        YEARS+=("$arg")
    fi
done

# Default to all years if none specified
if [[ ${#YEARS[@]} -eq 0 ]]; then
    YEARS=(2023 2024 2025)
fi

echo ""
echo "============================================================"
echo " Appalti IA - Data Pipeline"
echo " Years: ${YEARS[*]}"
echo " Skip extract: $SKIP_EXTRACT"
echo "============================================================"
echo ""

# Step 1: Extract from ANAC
if [[ "$SKIP_EXTRACT" == false ]]; then
    echo "[PIPELINE] Step 1/2: Extracting from ANAC..."
    echo ""
    bash "$SCRIPT_DIR/01_extract_cig.sh" "${YEARS[@]}"
    echo ""
else
    echo "[PIPELINE] Step 1/2: Skipped (--skip-extract)"
    echo ""
fi

# Step 2: Build contracts.json
echo "[PIPELINE] Step 2/2: Building contracts.json..."
echo ""
python3 "$SCRIPT_DIR/02_build_contracts.py" --years "${YEARS[@]}"

echo ""
echo "============================================================"
echo " Pipeline complete!"
echo " Output: data/contracts.json"
echo "============================================================"
