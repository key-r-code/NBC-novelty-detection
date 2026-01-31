"""
Process NBC++ classification results.

Adds taxonomic annotations and Known/Unknown labels based on training set membership.

Usage:
    python mass_mod.py
"""

import json
import os
from multiprocessing import Pool
from pathlib import Path

import polars as pl

from config import (
    KMER_LENGTHS,
    NEW_LINEAGE_CSV,
    SPECIES_MAPPING_JSON,
    TAXA_LEVELS,
    TRIALS,
    ensure_dir,
    get_classification_results_dir,
    get_modified_results_dir,
    get_training_list_path,
)


def get_training_list(taxa: str, trial: str) -> list:
    file_path = get_training_list_path(taxa, trial)
    if not file_path.exists():
        print(f"Warning: Training list not found: {file_path}")
        return []
    with open(file_path, 'r') as f:
        return [line.strip('\n')[1:] for line in f.readlines()]


def create_trial_map(taxa: str) -> dict:
    trial_map = {str(i): [] for i in range(1, 6)}
    for trial in TRIALS:
        trial_num = trial.split('_')[1]
        trial_map[trial_num] = get_training_list(taxa, trial)
    return trial_map


def create_lookup(taxa: str) -> pl.DataFrame:
    if not NEW_LINEAGE_CSV.exists():
        raise FileNotFoundError(f"Lineage CSV not found: {NEW_LINEAGE_CSV}")
    return (
        pl.read_csv(str(NEW_LINEAGE_CSV))
        .fill_null('')
        .with_columns(pl.col(pl.Utf8).str.strip_chars(), pl.col('Species_ID').cast(str))
        .select(['Species_ID', taxa])
        .unique()
    )


def load_species_mapping() -> dict:
    if not SPECIES_MAPPING_JSON.exists():
        raise FileNotFoundError(f"Species mapping not found: {SPECIES_MAPPING_JSON}")
    with open(SPECIES_MAPPING_JSON, 'r') as f:
        dict_ = json.load(f)
    return {value: key for key, values in dict_.items() for value in values}


def output_modifier(csv_file_path: str) -> None:
    csv_path = Path(csv_file_path)
    if not csv_path.exists():
        print(f"Warning: File not found: {csv_file_path}")
        return
    
    filename_parts = csv_path.name.split("_")
    taxa = filename_parts[2] if len(filename_parts) > 2 else "unknown"
    trial_number = filename_parts[1] if len(filename_parts) > 1 else "1"
    
    trial_map = create_trial_map(taxa)
    lookup = create_lookup(taxa.capitalize())
    species_mapping = load_species_mapping()

    mod_path = get_modified_results_dir(taxa)
    ensure_dir(mod_path)

    df = (
        pl.read_csv(csv_file_path, has_header=False,
                    new_columns=['NCBI RefSeq', 'Predicted Species_ID', 'Logarithmic probability'])
        .filter(~pl.col('NCBI RefSeq').cast(str).str.contains(r'^\d+$'))
        .with_columns(pl.col('Predicted Species_ID').cast(str))
    )

    df = (
        df.join(lookup.select(['Species_ID', pl.col(taxa.capitalize())]),
                left_on='Predicted Species_ID', right_on='Species_ID', how='left')
        .rename({taxa.capitalize(): f'Predicted {taxa.capitalize()}'})
    )

    df = df.with_columns(
        pl.col('NCBI RefSeq').replace_strict(species_mapping, default='').str.strip_chars().alias('Actual Species')
    )

    df = (
        df.join(lookup.select(['Species_ID', pl.col(taxa.capitalize())]),
                left_on='Actual Species', right_on='Species_ID', how='left')
        .rename({taxa.capitalize(): f'Actual {taxa.capitalize()}'})
    )

    df = (
        df.with_columns(
            pl.col('NCBI RefSeq').str.split('_').list.slice(0, 2).list.join('_').alias('NCBI RefSeq striped')
        )
        .with_columns(
            pl.col('NCBI RefSeq striped')
            .replace_strict({k: 'Known' for k in trial_map.get(trial_number, [])}, default='Unknown')
            .alias('Known/Unknown')
        )
    )

    output_path = mod_path / f'mod_{csv_path.name}'
    df.write_csv(str(output_path))
    print(f"Processed: {output_path}")


def get_all_csv_paths() -> list:
    paths = []
    for trial in TRIALS:
        for kmer in KMER_LENGTHS:
            for taxa in TAXA_LEVELS:
                csv_path = get_classification_results_dir(taxa, kmer) / f'{trial}_{taxa}_{kmer}mers.csv'
                paths.append(str(csv_path))
    return paths


def main():
    paths = get_all_csv_paths()
    print(f"Processing {len(paths)} classification result files...")
    
    num_threads = int(os.environ.get('SLURM_NTASKS', os.cpu_count() or 4))
    with Pool(processes=num_threads) as pool:
        pool.map(output_modifier, paths)
    
    print("Processing complete.")


if __name__ == "__main__":
    main()
