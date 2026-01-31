"""
Configuration for NBC++ novelty detection pipeline.

Set your paths here or use environment variables:
    export NBC_DATA_ROOT=/path/to/data
    export NBC_RESULTS_ROOT=/path/to/results
    export NBC_IMAGES_ROOT=/path/to/images
"""

import os
from pathlib import Path

# =============================================================================
# BASE DIRECTORIES
# =============================================================================

DATA_ROOT = Path(os.environ.get('NBC_DATA_ROOT', '/path/to/your/data'))
RESULTS_ROOT = Path(os.environ.get('NBC_RESULTS_ROOT', '/path/to/your/results'))
IMAGES_ROOT = Path(os.environ.get('NBC_IMAGES_ROOT', '/path/to/your/images'))

# =============================================================================
# INPUT PATHS
# =============================================================================

FNA_GROUPED_DIR = DATA_ROOT / 'fna_grouped_by_species_tax'
LINEAGE_CSV = DATA_ROOT / 'extended_lineage.csv'
NEW_LINEAGE_CSV = DATA_ROOT / 'new_extended_lineage.csv'
SPECIES_MAPPING_JSON = DATA_ROOT / 'species_mapping.json'
TRAINING_LISTS_DIR = DATA_ROOT / 'training_lists'

# =============================================================================
# OUTPUT PATH FUNCTIONS
# =============================================================================

def get_training_data_dir(taxa: str, kmer: str, trial: str) -> Path:
    return RESULTS_ROOT / f'{taxa.lower()}_testing' / f'{kmer}-mers' / 'training_data' / trial

def get_classification_results_dir(taxa: str, kmer: str) -> Path:
    return RESULTS_ROOT / f'{taxa.lower()}_testing' / f'{kmer}-mers' / 'classification_results'

def get_modified_results_dir(taxa: str) -> Path:
    return RESULTS_ROOT / 'modified_results' / f'{taxa.lower()}_modified'

def get_mean_roc_image_path(taxa: str) -> Path:
    return IMAGES_ROOT / 'mean_roc' / f'{taxa.lower()}_mean_roc.png'

def get_distro_image_path(taxa: str, trial: str) -> Path:
    return IMAGES_ROOT / 'distributions' / f'{taxa.lower()}_{trial}.png'

def get_training_list_path(taxa: str, trial: str) -> Path:
    return TRAINING_LISTS_DIR / f'{taxa.lower()}_{trial}.txt'

# =============================================================================
# HELPERS
# =============================================================================

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def validate_paths() -> bool:
    required = [('FNA_GROUPED_DIR', FNA_GROUPED_DIR), ('LINEAGE_CSV', LINEAGE_CSV)]
    missing = [(n, p) for n, p in required if not p.exists()]
    
    if missing:
        print("WARNING: Missing required paths:")
        for name, path in missing:
            print(f"  {name}: {path}")
        print("\nSet environment variables or edit src/config.py")
        return False
    return True

# =============================================================================
# EXPERIMENT PARAMETERS
# =============================================================================

TAXA_LEVELS = ['phylum', 'class', 'order', 'family']
KMER_LENGTHS = ['3', '6', '9', '12', '15']
TRIALS = ['trial_1', 'trial_2', 'trial_3', 'trial_4', 'trial_5']

MIN_REPRESENTATIVES_BASIC = 30
MIN_REPRESENTATIVES_EXTENDED = 400
GENOMES_PER_CLASS = 400
