#!/bin/bash
#
# submit_jobs.sh - Submit SLURM jobs for NBC++ novelty detection pipeline
#
# Usage:
#   ./scripts/submit_jobs.sh [step]
#
# Steps:
#   training   - Submit training set creation jobs
#   jellyfish  - Submit k-mer counting jobs
#   process    - Submit result processing job
#   plot       - Submit plotting job
#   all        - Submit all steps (default)

STEP="${1:-all}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# SLURM defaults - adjust for your cluster
PARTITION="defq"
TIME="24:00:00"
CPUS="48"
MEM="64G"

echo "Submitting jobs from: ${SCRIPT_DIR}"
echo "Step: ${STEP}"
echo ""

# Training set creation
submit_training() {
    for taxa in phylum class order family; do
        for trial in Trial_1 Trial_2 Trial_3 Trial_4 Trial_5; do
            sbatch --job-name="train_${taxa}_${trial}" \
                   --partition="${PARTITION}" \
                   --time="${TIME}" \
                   --cpus-per-task="${CPUS}" \
                   --mem="${MEM}" \
                   --output="slurm-train-${taxa}-${trial}-%j.out" \
                   --wrap="cd ${SCRIPT_DIR} && python src/create_training_sets.py ${taxa} ${trial}"
            echo "Submitted: train_${taxa}_${trial}"
        done
    done
}

# K-mer counting (requires SOURCE_DIR environment variable)
submit_jellyfish() {
    if [ -z "${SOURCE_DIR}" ]; then
        echo "ERROR: Set SOURCE_DIR environment variable"
        exit 1
    fi
    
    for kmer in 3 6 9 12 15; do
        sbatch --job-name="jellyfish_${kmer}mer" \
               --partition="${PARTITION}" \
               --time="${TIME}" \
               --cpus-per-task="${CPUS}" \
               --mem="${MEM}" \
               --output="slurm-jellyfish-${kmer}mer-%j.out" \
               --wrap="cd ${SCRIPT_DIR} && ./src/jellyfish_gen.sh ${SOURCE_DIR} ${kmer} false"
        echo "Submitted: jellyfish_${kmer}mer"
    done
}

# Result processing
submit_process() {
    sbatch --job-name="mass_mod" \
           --partition="${PARTITION}" \
           --time="04:00:00" \
           --cpus-per-task="${CPUS}" \
           --mem="${MEM}" \
           --output="slurm-mass_mod-%j.out" \
           --wrap="cd ${SCRIPT_DIR} && python src/mass_mod.py"
    echo "Submitted: mass_mod"
}

# Plotting
submit_plot() {
    sbatch --job-name="plot_roc" \
           --partition="${PARTITION}" \
           --time="02:00:00" \
           --cpus-per-task="${CPUS}" \
           --mem="${MEM}" \
           --output="slurm-plot-%j.out" \
           --wrap="cd ${SCRIPT_DIR} && python src/plot_mean_roc.py && python src/plot_roc_distro.py"
    echo "Submitted: plot_roc"
}

# Run requested step(s)
case "${STEP}" in
    training)  submit_training ;;
    jellyfish) submit_jellyfish ;;
    process)   submit_process ;;
    plot)      submit_plot ;;
    all)
        submit_training
        echo ""
        echo "Note: Submit jellyfish jobs manually after training completes"
        echo "Note: Submit process/plot jobs after NBC++ classification completes"
        ;;
    *)
        echo "Unknown step: ${STEP}"
        echo "Valid steps: training, jellyfish, process, plot, all"
        exit 1
        ;;
esac

echo ""
echo "Done. Check job status with: squeue -u \$USER"
