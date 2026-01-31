# Pipeline Documentation

This document provides detailed information about the NBC++ novelty detection pipeline.

## Overview

The pipeline evaluates NBC++'s ability to detect novel taxa by:

1. Partitioning reference databases into "known" (training) and "unknown" (holdout) sets
2. Training NBC++ models at various k-mer lengths
3. Classifying test reads and collecting log-probability scores
4. Using ROC analysis to derive optimal novelty thresholds

## Pipeline Steps

### Step 1: Database Partitioning (`create_training_sets.py`)

Partitions genomes to create training and holdout sets.

**Method:**
- Filter taxa with sufficient representatives (≥400 for extended database)
- Randomly select 50% of taxonomic classes
- Sample 400 genomes from each selected class
- Remaining genomes form the holdout ("unknown") set

**Usage:**
```bash
python src/create_training_sets.py <taxa_level> <trial_number>

# Example
python src/create_training_sets.py Order Trial_1
```

**Parameters:**
- `taxa_level`: Phylum, Class, Order, or Family
- `trial_number`: Trial identifier (Trial_1 through Trial_5)

---

### Step 2: K-mer Counting (`jellyfish_gen.sh`)

Generates k-mer frequency profiles using Jellyfish.

**Usage:**
```bash
./src/jellyfish_gen.sh <source_dir> <kmer_size> <is_full_genome>

# Example
./src/jellyfish_gen.sh /path/to/genomes 9 false
```

**Parameters:**
- `source_dir`: Directory containing `.fna` files
- `kmer_size`: K-mer length (3, 6, 9, 12, or 15)
- `is_full_genome`: `true` for full genomes, `false` for canonical k-mers

**Output:** `.kmr` files with k-mer counts

---

### Step 3: NBC++ Classification

Run NBC++ to classify reads against the training database.

**See:** [NBC++ GitHub](https://github.com/EESI/Naive_Bayes)

**Docker:**
```bash
docker pull eesilab/nbc_complete_toolset
```

**Output:** CSV files with read ID, predicted species, and log-probability

---

### Step 4: Result Processing (`mass_mod.py`)

Enriches classification results with taxonomic information and Known/Unknown labels.

**Usage:**
```bash
python src/mass_mod.py
```

**Processing:**
1. Loads classification results
2. Maps predicted Species_ID to taxonomic classification
3. Maps read IDs to actual species using RefSeq mapping
4. Labels each read as "Known" or "Unknown" based on training set membership

**Output:** Modified CSV files in `modified_results/{taxa}_modified/`

---

### Step 5: ROC Analysis and Plotting

#### Mean ROC Curves (`plot_mean_roc.py`)

Generates average ROC curves across trials with standard deviation bands.

```bash
python src/plot_mean_roc.py
```

**Output:** `{taxa}_mean_roc.png` for each taxonomic level

**Metrics calculated:**
- Mean AUC ± standard deviation
- Optimal threshold (maximizing Youden's J statistic)

#### Distribution Plots (`plot_roc_distro.py`)

Generates ROC curves alongside log-probability histograms.

```bash
python src/plot_roc_distro.py
```

**Output:** `{taxa}_{trial}.png` showing separation between Known/Unknown distributions

---

## Threshold Calculation

The optimal novelty threshold is determined using **Youden's J statistic**:

```
J = Sensitivity + Specificity - 1
J = TPR - FPR
```

The threshold that maximizes J provides the best balance between:
- True Positive Rate (correctly identifying known taxa)
- False Positive Rate (incorrectly labeling unknown as known)

---

## Configuration

All parameters are centralized in `src/config.py`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `TAXA_LEVELS` | Taxonomic levels to analyze | phylum, class, order, family |
| `KMER_LENGTHS` | K-mer sizes to test | 3, 6, 9, 12, 15 |
| `TRIALS` | Number of independent trials | 5 |
| `MIN_REPRESENTATIVES_EXTENDED` | Minimum genomes per class | 400 |
| `GENOMES_PER_CLASS` | Genomes sampled per class | 400 |

---

## Parallel Processing

Scripts automatically detect SLURM environment:

```python
num_threads = int(os.environ.get('SLURM_NTASKS', os.cpu_count()))
```

For SLURM submission, see `scripts/submit_jobs.sh`.

---

## Troubleshooting

### "Path not found" errors

Ensure environment variables are set:
```bash
export NBC_DATA_ROOT=/path/to/data
export NBC_RESULTS_ROOT=/path/to/results
export NBC_IMAGES_ROOT=/path/to/images
```

Or edit `src/config.py` directly.

### Missing dependencies

```bash
pip install -r requirements.txt
```

### Jellyfish not found

```bash
# On HPC systems
module load jellyfish

# Or install via conda
conda install -c bioconda jellyfish
```

---

## Output Summary

| Step | Output Location |
|------|-----------------|
| Training sets | `$RESULTS_ROOT/{taxa}_testing/{kmer}-mers/training_data/` |
| K-mer counts | Same directory as input `.fna` files |
| NBC++ results | `$RESULTS_ROOT/{taxa}_testing/{kmer}-mers/classification_results/` |
| Processed results | `$RESULTS_ROOT/modified_results/{taxa}_modified/` |
| ROC plots | `$IMAGES_ROOT/mean_roc/` and `$IMAGES_ROOT/distributions/` |
