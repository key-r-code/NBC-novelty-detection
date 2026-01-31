#!/bin/bash
#
# jellyfish_gen.sh - Generate k-mer counts using Jellyfish
#
# Usage:
#   ./jellyfish_gen.sh <source_dir> <kmer_size> <is_full_genome> [resume_from]
#
# Arguments:
#   source_dir     - Directory containing .fna files
#   kmer_size      - K-mer length (e.g., 3, 6, 9, 12, 15)
#   is_full_genome - "true" for full genomes, "false" for canonical k-mers
#   resume_from    - Optional: resume from file number N

set -e

# Load jellyfish module if available (HPC environments)
module load jellyfish 2>/dev/null || true

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: ./jellyfish_gen.sh <source_dir> <kmer_size> <is_full_genome> [resume_from]"
    echo ""
    echo "Arguments:"
    echo "  source_dir     - Directory containing .fna files"
    echo "  kmer_size      - K-mer length (e.g., 9)"
    echo "  is_full_genome - 'true' for full genomes, 'false' for canonical k-mers"
    echo "  resume_from    - Optional: resume from file number N"
    exit 1
fi

SOURCE_DIR="$1"
KMER_SIZE="$2"
IS_FULL_GENOME="$3"
RESUME_FROM="${4:-0}"

echo "=============================================="
echo "Jellyfish K-mer Counting"
echo "=============================================="
echo "Source directory: ${SOURCE_DIR}"
echo "K-mer size: ${KMER_SIZE}"
echo "Full genome mode: ${IS_FULL_GENOME}"
echo ""

# Count files
file_count=$(find "$SOURCE_DIR" -iname "*.fna" | wc -l)
echo "Found ${file_count} .fna files"
echo ""

progress=1
for file in $(find "$SOURCE_DIR" -iname "*.fna"); do
    # Skip if resuming
    if [ "$progress" -lt "$RESUME_FROM" ]; then
        progress=$((progress + 1))
        continue
    fi

    echo "(${progress}/${file_count}) Processing: ${file}"
    
    filename="${file%.*}"
    size=$(cat "$file" | wc -c)
    
    # Run jellyfish with retry logic
    if [ "$IS_FULL_GENOME" == "true" ]; then
        # Full genome mode
        while true; do
            if timeout 300 jellyfish count -m "$KMER_SIZE" -s "$size" -t 32 -o "${filename}.jf" "$file"; then
                break
            else
                echo "  Retry..."
                rm -f "${filename}.jf"
            fi
        done
    else
        # Canonical k-mer mode (for partial sequences)
        while true; do
            if timeout 300 jellyfish count -m "$KMER_SIZE" -s "$size" -t 48 -C -o "${filename}.jf" "$file"; then
                break
            else
                echo "  Retry..."
                rm -f "${filename}.jf"
            fi
        done
    fi
    
    # Dump counts and clean up
    jellyfish dump -c "${filename}.jf" > "${filename}.kmr"
    rm "${filename}.jf"
    
    echo "  Done: ${filename}.kmr"
    progress=$((progress + 1))
done

echo ""
echo "=============================================="
echo "K-mer counting complete!"
echo "=============================================="
