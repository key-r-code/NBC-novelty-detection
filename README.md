# NBC++ for Out-of-Distribution Detection of Novel Taxa

[![DOI](https://zenodo.org/badge/1146072663.svg)](https://doi.org/10.5281/zenodo.18444493)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

This repository contains the code and analysis pipeline for evaluating the Naïve Bayes Classifier++ (NBC++) as an out-of-distribution (OOD) detector for novel taxa in metagenomic classification.

**Paper:** Naïve Bayes Classifier++ as an out-of-distribution detector of novel taxa [preprint](https://www.biorxiv.org/content/10.1101/2025.10.18.683227v2)

## Repository Structure

```
NBC-novelty-detection/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── run_pipeline.sh
├── docs/
│   ├── DATA_FORMAT.md           # Input file format specifications
│   └── PIPELINE.md              # Detailed pipeline documentation
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration - SET YOUR PATHS HERE
│   ├── create_training_sets.py
│   ├── mass_mod.py
│   ├── plot_mean_roc.py
│   ├── plot_roc_distro.py
│   └── jellyfish_gen.sh
├── examples/
│   ├── sample_lineage.csv
│   ├── sample_species_mapping.json
│   └── sample_training_list.txt
└── scripts/
    └── submit_jobs.sh           # SLURM job submission
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/NBC-novelty-detection.git
cd NBC-novelty-detection

# Install Python dependencies
pip install -r requirements.txt
```

### Prerequisites

- Python 3.8+
- Jellyfish (for k-mer counting)
- SLURM (optional, for HPC parallel processing)

## Quick Start

```bash
# 1. Configure your paths (edit src/config.py or use environment variables)
export NBC_DATA_ROOT=/path/to/your/data
export NBC_RESULTS_ROOT=/path/to/your/results
export NBC_IMAGES_ROOT=/path/to/your/images

# 2. Run the full pipeline
./run_pipeline.sh

# Or run with options
./run_pipeline.sh --skip-training --taxa order --kmer 9
```

## Configuration

All paths are configured in `src/config.py`. You can either edit the file directly or set environment variables:

```bash
export NBC_DATA_ROOT=/path/to/your/data
export NBC_RESULTS_ROOT=/path/to/your/results
export NBC_IMAGES_ROOT=/path/to/your/images
```

See [`docs/DATA_FORMAT.md`](docs/DATA_FORMAT.md) for detailed input file specifications, or check [`examples/`](examples/) for sample files.

## Usage

### Step 1: Create Training Sets

```bash
python src/create_training_sets.py <taxa_level> <trial_number>

# Example
python src/create_training_sets.py Order Trial_1
```

### Step 2: Generate K-mer Counts

```bash
./src/jellyfish_gen.sh <source_dir> <k-mer_size> <is_full_genome>

# Example
./src/jellyfish_gen.sh /path/to/genomes 9 false
```

### Step 3: Run NBC++ Classification

See [NBC++ documentation](https://github.com/EESI/Naive_Bayes) for classification instructions.

### Step 4: Process Results

```bash
python src/mass_mod.py
```

### Step 5: Generate Plots

```bash
python src/plot_mean_roc.py
python src/plot_roc_distro.py
```

For detailed pipeline documentation, see [`docs/PIPELINE.md`](docs/PIPELINE.md).

## Results

### K-mer Length and Classification Accuracy

Longer k-mers consistently improve discrimination between known and unknown sequences:

| K-mer Length | AUC Performance |
|--------------|-----------------|
| 3-mers | ~0.5-0.6 (baseline) |
| 6-mers | Moderate improvement |
| 9-mers | Good discrimination |
| 12-mers | ~0.81 (order level) |
| 15-mers | >0.85 (best) |

### Threshold Stability

Novelty thresholds remained stable between basic and extended databases. At 9-mers:
- Extended phylum threshold: -1049.62
- Basic phylum threshold: -1053.81

### Human Gut Metagenome Application

Applied to a real human gut metagenome (SRA ID: SRS105153):

| Model | % Classified as "Known" |
|-------|------------------------|
| Basic (NBC++) | 98.09% |
| Extended (NBC++) | 92.77% |
| Basic (Kraken2) | 8.87% |
| Extended (Kraken2) | 82.30% |

## Data Availability

- **NBC++ Source Code**: [GitHub](http://github.com/EESI/Naive_Bayes)
- **Docker Container**: [Docker Hub](https://hub.docker.com/r/eesilab/nbc_complete_toolset)
- **Training Data**: [Zenodo](https://zenodo.org/records/11657719)
- **Human Gut Sample**: [SRA SRS105153](https://www.ncbi.nlm.nih.gov/sra/SRS105153)


