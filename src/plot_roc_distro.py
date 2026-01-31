"""
Plot ROC curves and log-probability distributions.

Usage:
    python plot_roc_distro.py
"""

import os
import re
from multiprocessing import Pool
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns
from sklearn.metrics import auc, roc_curve

from config import TAXA_LEVELS, TRIALS, ensure_dir, get_distro_image_path, get_modified_results_dir


def plot_roc(file: str, ax: plt.Axes) -> None:
    df = (
        pl.read_csv(file, infer_schema_length=None)
        .filter(pl.col("Predicted Species_ID").cast(pl.Utf8).str.contains(r'\d+'))
        .select(['Logarithmic probability', 'Known/Unknown'])
        .with_columns(pl.col("Known/Unknown").replace({"Known": 1, "Unknown": 0}).cast(pl.Int64))
    )

    fpr, tpr, _ = roc_curve(df["Known/Unknown"], df['Logarithmic probability'])
    roc_auc = auc(fpr, tpr)
    
    ax.plot(fpr, tpr, color='red', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    ax.plot([0, 1], [0, 1], color='darkgrey', lw=2, linestyle='--')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('FPR')
    ax.set_ylabel('TPR')
    ax.legend(loc='lower right')


def plot_distribution(file: str, ax: plt.Axes) -> None:
    data = (
        pl.read_csv(file, infer_schema_length=None)
        .filter(pl.col("Predicted Species_ID").cast(pl.Utf8).str.contains(r'\d+'))
        .select(['Logarithmic probability', 'Known/Unknown'])
    )

    sns.histplot(data=data, x="Logarithmic probability", hue="Known/Unknown", ax=ax,
                 fill=True, palette={"Known": "navy", "Unknown": "red"},
                 hue_order=["Unknown", "Known"], bins=1000)

    mode = data["Logarithmic probability"].mode()[0]
    ax.set_xlim(mode - 150, mode + 150)
    ax.set_xlabel("Log probability")
    ax.set_ylabel("Count")


def process_taxa(taxa: str) -> None:
    input_dir = get_modified_results_dir(taxa)
    if not input_dir.exists():
        print(f"Warning: Directory not found: {input_dir}")
        return

    file_paths = [str(f) for f in input_dir.iterdir() if f.is_file()]
    if not file_paths:
        return

    file_dict = {trial: sorted([x for x in file_paths if trial in x],
                               key=lambda x: int(''.join(filter(str.isdigit, Path(x).name.split("_")[-1].split("_")[0]))))
                 for trial in TRIALS}

    for trial, files in file_dict.items():
        if not files:
            continue
            
        fig, axes = plt.subplots(len(files), 2, figsize=(20, 40))
        plt.subplots_adjust(top=0.95)
        
        for i, f in enumerate(files):
            if not Path(f).exists():
                continue
            plot_roc(f, axes[i, 0])
            plot_distribution(f, axes[i, 1])
            
            row_title_ax = fig.add_subplot(len(files), 1, i + 1, frameon=False)
            row_title_ax.set_xticks([])
            row_title_ax.set_yticks([])
            kmer_match = re.search(r'(\d+)mers', Path(f).name)
            row_title_ax.set_title(f"{kmer_match.group(1)}-mers" if kmer_match else f"Row {i+1}",
                                   fontsize=14, fontweight='bold')

        fig.suptitle(trial.replace('_', ' ').title(), fontsize=16, fontweight='bold')
        
        output_path = get_distro_image_path(taxa, trial)
        ensure_dir(output_path.parent)
        plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved: {output_path}")


def main():
    print(f"Generating plots for {len(TAXA_LEVELS)} taxonomic levels...")
    num_threads = int(os.environ.get('SLURM_NTASKS', os.cpu_count() or 4))

    with Pool(processes=num_threads) as pool:
        pool.map(process_taxa, TAXA_LEVELS)
    
    print("Plotting complete.")


if __name__ == "__main__":
    main()
