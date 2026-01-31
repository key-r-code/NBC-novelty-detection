"""
Create training and holdout sets for NBC++ novelty detection.

Usage:
    python create_training_sets.py <taxa_level> <trial_number>
    
Example:
    python create_training_sets.py Order Trial_1
"""

import os
import random
import subprocess
import sys
from multiprocessing import Pool

import pandas as pd

from config import (
    FNA_GROUPED_DIR,
    GENOMES_PER_CLASS,
    LINEAGE_CSV,
    MIN_REPRESENTATIVES_EXTENDED,
    ensure_dir,
    get_training_data_dir,
    validate_paths,
)


def random_sample(items: list, n: int) -> list:
    return random.sample(items, min(n, len(items)))


def copy_folder_batch(args: tuple) -> None:
    folder, source_dir, destination_path = args
    try:
        source_path = source_dir / folder
        cmd = f"rsync -a {source_path} {destination_path}/"
        subprocess.run(cmd, shell=True, check=True)
        print(f"Copied: {folder}")
    except subprocess.CalledProcessError as e:
        print(f"Error copying {folder}: {e}")


def parallel_copy(folder_list: list, destination_path, source_dir=None) -> None:
    if source_dir is None:
        source_dir = FNA_GROUPED_DIR
    
    num_threads = int(os.environ.get('SLURM_NTASKS', os.cpu_count() or 4))
    print(f"Using {num_threads} parallel processes")

    args_list = [(folder, source_dir, destination_path) for folder in folder_list]

    with Pool(processes=num_threads) as pool:
        pool.map(copy_folder_batch, args_list)


def create_training_set(taxa_level: str, trial_number: str,
                        min_representatives: int = MIN_REPRESENTATIVES_EXTENDED,
                        genomes_per_class: int = GENOMES_PER_CLASS) -> None:
    
    if not validate_paths():
        sys.exit(1)
    
    print(f"Loading lineage data from {LINEAGE_CSV}")
    df = pd.read_csv(LINEAGE_CSV)
    df = df.fillna('')
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    taxa_level = taxa_level.capitalize()
    
    dx = df[['Species_ID', taxa_level]]
    dx = dx[dx[taxa_level].isin(
        dx[taxa_level].value_counts()[dx[taxa_level].value_counts() >= min_representatives].index
    )]
    dx = dx[dx[taxa_level] != '']

    grouped_dfs = {name: group.reset_index(drop=True) for name, group in dx.groupby(taxa_level)}
    grouped_dfs = {key.lower(): value for key, value in grouped_dfs.items()}

    print(f"Found {len(grouped_dfs)} taxonomic groups with >= {min_representatives} representatives")

    output_dir = get_training_data_dir(taxa_level, '3', trial_number)
    ensure_dir(output_dir)
    print(f"Output directory: {output_dir}")

    try:
        training_taxa = random.sample(list(grouped_dfs.keys()), len(grouped_dfs) // 2)
        print(f"Selected {len(training_taxa)} taxa for training set")
        
        training_data = []
        for taxa in training_taxa:
            species_ids = list(set(grouped_dfs[taxa]['Species_ID'].tolist()))
            selected = random_sample(species_ids, genomes_per_class)
            training_data.extend(selected)

        print(f"Total genomes in training set: {len(training_data)}")
        parallel_copy(training_data, output_dir)
        print(f"Training set created successfully")

    except Exception as e:
        print(f"Error creating training set: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python create_training_sets.py <taxa_level> <trial_number>")
        print("Example: python create_training_sets.py Order Trial_1")
        sys.exit(1)

    create_training_set(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
