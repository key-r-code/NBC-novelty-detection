# Data Format Specifications

This document describes the expected format for all input files.

## Required Files

| File | Description | Used By |
|------|-------------|---------|
| `extended_lineage.csv` | Taxonomic lineage metadata | `create_training_sets.py` |
| `new_extended_lineage.csv` | Updated lineage metadata | `mass_mod.py` |
| `species_mapping.json` | NCBI RefSeq → Species ID mapping | `mass_mod.py` |
| `fna_grouped_by_species_tax/` | Genome files by species | `create_training_sets.py` |
| `training_lists/` | Species in each training set | `mass_mod.py` |

---

## 1. Lineage CSV Files

**Files:** `extended_lineage.csv`, `new_extended_lineage.csv`

Taxonomic metadata mapping species to their lineage.

**Required Columns:**

| Column | Type | Example |
|--------|------|---------|
| `Species_ID` | string | `12345` |
| `Phylum` | string | `Proteobacteria` |
| `Class` | string | `Gammaproteobacteria` |
| `Order` | string | `Enterobacterales` |
| `Family` | string | `Enterobacteriaceae` |

**Example:**
```csv
Species_ID,Phylum,Class,Order,Family,Genus,Species
12345,Proteobacteria,Gammaproteobacteria,Enterobacterales,Enterobacteriaceae,Escherichia,Escherichia coli
67890,Firmicutes,Bacilli,Lactobacillales,Streptococcaceae,Streptococcus,Streptococcus pneumoniae
```

---

## 2. Species Mapping JSON

**File:** `species_mapping.json`

Maps NCBI RefSeq accessions to Species IDs.

**Format:**
```json
{
    "12345": ["GCF_000005845", "GCF_000008865"],
    "67890": ["GCF_000006785"]
}
```

---

## 3. Genome Directory

**Directory:** `fna_grouped_by_species_tax/`

Genome files organized by accession.

```
fna_grouped_by_species_tax/
├── GCF_000005845/
│   └── GCF_000005845.fna
├── GCF_000008865/
│   └── GCF_000008865.fna
└── ...
```

---

## 4. Training Lists

**Directory:** `training_lists/`

Text files listing species in each training set.

**Filename pattern:** `{taxa}_{trial}.txt`

**Format:** One accession per line with `>` prefix
```
>GCF_000005845
>GCF_000008865
>GCF_000006785
```

---

## 5. Classification Results (NBC++ Output)

**Directory:** `{taxa}_testing/{kmer}-mers/classification_results/`

**Filename pattern:** `{trial}_{taxa}_{kmer}mers.csv`

**Format:** CSV without header
```
GCF_000005845_read_001,12345,-1045.67
GCF_000005845_read_002,12345,-1052.34
```

| Column | Description |
|--------|-------------|
| 1 | Read identifier (NCBI RefSeq) |
| 2 | Predicted Species_ID |
| 3 | Log-probability score |

---

## Directory Structure

```
$NBC_DATA_ROOT/
├── fna_grouped_by_species_tax/
├── extended_lineage.csv
├── new_extended_lineage.csv
├── species_mapping.json
└── training_lists/
    ├── phylum_trial_1.txt
    ├── phylum_trial_2.txt
    └── ...

$NBC_RESULTS_ROOT/
├── phylum_testing/
│   ├── 3-mers/
│   │   ├── training_data/
│   │   └── classification_results/
│   └── ...
└── modified_results/
    └── phylum_modified/

$NBC_IMAGES_ROOT/
├── mean_roc/
└── distributions/
```

---

## Example Files

See the [`examples/`](../examples/) directory for sample files demonstrating each format.

## Real Data

For actual data used in the paper:
- **Zenodo**: https://zenodo.org/records/11657719
- **SRA**: SRS105153 (human gut metagenome)
