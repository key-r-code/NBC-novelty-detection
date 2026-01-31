"""
Plot mean ROC curves across trials for novelty detection.

Usage:
    python plot_mean_roc.py
"""

import os
import re
from multiprocessing import Pool
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from sklearn.metrics import auc, roc_curve

from config import KMER_LENGTHS, TAXA_LEVELS, ensure_dir, get_mean_roc_image_path, get_modified_results_dir


def roc_multiple_files(files: list, ax: plt.Axes, color: str) -> plt.Axes:
    all_tprs, all_aucs, best_thresholds, best_j_scores = [], [], [], []

    for file in files:
        if not Path(file).exists():
            continue
            
        df = (
            pl.read_csv(file, infer_schema_length=None)
            .filter(pl.col("Predicted Species_ID").cast(pl.Utf8).str.contains(r'\d+'))
            .select(['Logarithmic probability', 'Known/Unknown'])
            .with_columns(pl.col("Known/Unknown").replace({"Known": 1, "Unknown": 0}).cast(pl.Int64))
        )

        fpr, tpr, thresholds = roc_curve(df["Known/Unknown"], df['Logarithmic probability'])
        roc_auc = auc(fpr, tpr)
        
        j_scores = tpr - fpr
        best_idx = np.argmax(j_scores)
        best_thresholds.append(thresholds[best_idx])
        best_j_scores.append(j_scores[best_idx])
        
        interp_tpr = np.interp(np.linspace(0, 1, 100), fpr, tpr)
        interp_tpr[0] = 0.0
        all_tprs.append(interp_tpr)
        all_aucs.append(roc_auc)

    if not all_tprs:
        return ax

    mean_tpr = np.mean(all_tprs, axis=0)
    std_tpr = np.std(all_tprs, axis=0)
    mean_auc = np.mean(all_aucs)
    std_auc = np.std(all_aucs)
    best_threshold = best_thresholds[np.argmax(best_j_scores)]

    ax.plot(np.linspace(0, 1, 100), mean_tpr, color=color, lw=2,
            label=f'Mean ROC (AUC = {mean_auc:.2f} ± {std_auc:.2f})')
    ax.plot([], [], ' ', label=f'Best Th = $\\mathbf{{{best_threshold:.2f}}}$')
    ax.fill_between(np.linspace(0, 1, 100), mean_tpr - std_tpr, mean_tpr + std_tpr,
                    alpha=0.3, color=color, label='±1 std. dev.')
    ax.plot([0, 1], [0, 1], color='darkgrey', lw=2, linestyle='--')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(loc='lower right')

    return ax


def plot_taxa(args: tuple) -> None:
    taxa, color = args
    input_dir = get_modified_results_dir(taxa)
    
    if not input_dir.exists():
        print(f"Warning: Directory not found: {input_dir}")
        return
    
    file_paths = [str(f) for f in input_dir.iterdir() if f.is_file()]
    if not file_paths:
        return
    
    kmers = [f'{k}mers' for k in KMER_LENGTHS]
    file_dict = {kmer: sorted([x for x in file_paths if kmer in x],
                              key=lambda x: int(''.join(filter(str.isdigit, Path(x).name.split("_")[-1]))))
                 for kmer in kmers}

    fig, axes = plt.subplots(len(kmers), 1, figsize=(8, 38))
    plt.subplots_adjust(top=0.95)

    for i, (kmer, files) in enumerate(file_dict.items()):
        if files:
            roc_multiple_files(files, axes[i], color)
        row_title_ax = fig.add_subplot(len(kmers), 1, i + 1, frameon=False)
        row_title_ax.set_xticks([])
        row_title_ax.set_yticks([])
        kmer_num = re.search(r'\d+', kmer)
        row_title_ax.set_title(f"{kmer_num.group()}-mers" if kmer_num else kmer, fontsize=12, fontweight='bold')

    fig.suptitle(taxa.capitalize(), fontsize=15, fontweight='bold')
    
    output_path = get_mean_roc_image_path(taxa)
    ensure_dir(output_path.parent)
    plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")


def main():
    taxa_colors = [("phylum", "blue"), ("class", "mediumturquoise"), ("order", "orange"), ("family", "violet")]
    taxa_colors = [(t, c) for t, c in taxa_colors if t in TAXA_LEVELS]
    
    print(f"Generating mean ROC plots for {len(taxa_colors)} taxonomic levels...")
    num_threads = int(os.environ.get('SLURM_NTASKS', os.cpu_count() or 4))

    with Pool(processes=num_threads) as pool:
        pool.map(plot_taxa, taxa_colors)
    
    print("Plotting complete.")


if __name__ == "__main__":
    main()
