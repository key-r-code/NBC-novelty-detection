#!/bin/bash
#
# run_pipeline.sh - Run the NBC++ novelty detection pipeline
#
# Usage:
#   ./run_pipeline.sh [OPTIONS]
#
# Options:
#   --skip-training    Skip training set creation
#   --skip-jellyfish   Skip k-mer counting
#   --taxa LEVEL       Run only for specific taxa level
#   --kmer SIZE        Run only for specific k-mer size
#   --help             Show this help message

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"

# Defaults
SKIP_TRAINING=false
SKIP_JELLYFISH=false
TAXA_LEVELS=("phylum" "class" "order" "family")
KMER_SIZES=("3" "6" "9" "12" "15")
TRIALS=("Trial_1" "Trial_2" "Trial_3" "Trial_4" "Trial_5")

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-training) SKIP_TRAINING=true; shift ;;
        --skip-jellyfish) SKIP_JELLYFISH=true; shift ;;
        --taxa) TAXA_LEVELS=("$2"); shift 2 ;;
        --kmer) KMER_SIZES=("$2"); shift 2 ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-training    Skip training set creation"
            echo "  --skip-jellyfish   Skip k-mer counting"
            echo "  --taxa LEVEL       Run only for specific taxa level"
            echo "  --kmer SIZE        Run only for specific k-mer size"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "=============================================="
echo "NBC++ Novelty Detection Pipeline"
echo "=============================================="

# Check dependencies
echo "Checking dependencies..."
python3 -c "import pandas, polars, numpy, sklearn, matplotlib, seaborn" 2>/dev/null || {
    echo "ERROR: Missing Python dependencies. Run: pip install -r requirements.txt"
    exit 1
}
echo "  OK"

# Step 1: Training sets
if [[ "${SKIP_TRAINING}" == false ]]; then
    echo ""
    echo "Step 1: Creating Training Sets"
    echo "----------------------------------------------"
    for taxa in "${TAXA_LEVELS[@]}"; do
        for trial in "${TRIALS[@]}"; do
            echo "  ${taxa} - ${trial}"
            python3 "${SRC_DIR}/create_training_sets.py" "${taxa}" "${trial}"
        done
    done
fi

# Step 2: K-mer counting
if [[ "${SKIP_JELLYFISH}" == false ]]; then
    echo ""
    echo "Step 2: K-mer Counting"
    echo "----------------------------------------------"
    if command -v jellyfish &> /dev/null; then
        for kmer in "${KMER_SIZES[@]}"; do
            echo "  ${kmer}-mers (run manually with your source directory)"
        done
    else
        echo "  WARNING: jellyfish not found, skipping"
    fi
fi

# Step 3: NBC++ (manual)
echo ""
echo "Step 3: NBC++ Classification"
echo "----------------------------------------------"
echo "  Run NBC++ separately. See: https://github.com/EESI/Naive_Bayes"

# Step 4: Process results
echo ""
echo "Step 4: Processing Results"
echo "----------------------------------------------"
python3 "${SRC_DIR}/mass_mod.py"

# Step 5: Plots
echo ""
echo "Step 5: Generating Plots"
echo "----------------------------------------------"
python3 "${SRC_DIR}/plot_mean_roc.py"
python3 "${SRC_DIR}/plot_roc_distro.py"

echo ""
echo "=============================================="
echo "Pipeline Complete!"
echo "=============================================="
