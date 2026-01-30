import os
import re
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from multiprocessing import Pool
from pathlib import Path

def roc_multiple_files(files, ax, couleur):
    all_fprs = []
    all_tprs = []
    all_aucs = []
    best_thresholds = []
    best_j_scores = []  

    for file in files:
        df = (
            pl.read_csv(file, infer_schema_length=None)
            .filter(pl.col("Predicted Species_ID").cast(pl.Utf8).str.contains(r'\d+'))
            .select(['Logarithmic probability', 'Known/Unknown'])
            .with_columns(
                pl.col("Known/Unknown").replace({
                    "Known": 1,
                    "Unknown": 0
                }).cast(pl.Int64)
            )
        )

        y_actual = df["Known/Unknown"]
        y_probs_log = df['Logarithmic probability']
        fpr, tpr, thresholds = roc_curve(y_actual, y_probs_log)
        roc_auc = auc(fpr, tpr)
        
        j_scores = tpr - fpr
        best_idx = np.argmax(j_scores)
        best_threshold = thresholds[best_idx]
        best_j = j_scores[best_idx]
        best_thresholds.append(best_threshold)
        best_j_scores.append(best_j)
        
        interp_tpr = np.interp(np.linspace(0, 1, 100), fpr, tpr)
        interp_tpr[0] = 0.0
        
        all_fprs.append(np.linspace(0, 1, 100))
        all_tprs.append(interp_tpr)
        all_aucs.append(roc_auc)

    mean_tpr = np.mean(all_tprs, axis=0)
    std_tpr = np.std(all_tprs, axis=0)
    mean_auc = np.mean(all_aucs)
    std_auc = np.std(all_aucs)
    
    idx_best_overall = np.argmax(best_j_scores)
    best_threshold_overall = best_thresholds[idx_best_overall]

    ax.plot(np.linspace(0, 1, 100), mean_tpr, color=couleur, lw=2, 
            label=f'Mean ROC (AUC = {mean_auc:.2f} ± {std_auc:.2f})')

    ax.plot([], [], ' ', label=f'Best Th = $\mathbf{{{best_threshold_overall:.2f}}}$')

    ax.fill_between(np.linspace(0, 1, 100), mean_tpr - std_tpr, mean_tpr + std_tpr, 
                    alpha=0.3, color=couleur, label='±1 std. dev.')

    ax.plot([0, 1], [0, 1], color='darkgrey', lw=2, linestyle='--')

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(loc='lower right')

    return ax

def plot(taxa, couleur):
    directory = Path(f'/ifs/groups/rosenMRIGrp/kr3288/extended/modified_results/{taxa}_modified')
    file_paths = [str(file) for file in directory.iterdir()]
    kmers = ['3mers', '6mers', '9mers', '12mers', '15mers']
    file_dict = {kmer: [x for x in file_paths if kmer in x] for kmer in kmers}
    file_dict = {kmer: sorted(paths, key=lambda x: int(''.join(filter(str.isdigit, x.split("/")[-1].split("_")[-1])))) for kmer, paths in file_dict.items()}

    fig, ax = plt.subplots(5, 1, figsize=(8, 38))
    plt.subplots_adjust(top=0.95)

    for i, (kmer, files) in enumerate(file_dict.items()):
        roc_multiple_files(files, ax[i], couleur)
        row_title_ax = fig.add_subplot(5, 1, i+1, frameon=False)
        row_title_ax.set_xticks([])
        row_title_ax.set_yticks([])
        row_title_ax.set_title(re.search(r'\d+', kmer).group() + "-mers", fontsize=12, fontweight='bold')
        
    fig.suptitle(taxa.capitalize(), fontsize=15, fontweight='bold')
    plt.savefig(f'/ifs/groups/rosenMRIGrp/kr3288/extended/images_mean/{taxa}_mean_roc.png')

if __name__ == "__main__":
    num_threads = int(os.environ.get('SLURM_NTASKS', 48))
    
    taxa_colors = [
        ("phylum", "blue"),
        ("class", "mediumturquoise"),
        ("order", "orange"),
        ("family", "violet")
    ]

    with Pool(processes=num_threads) as pool:
        pool.starmap(plot, taxa_colors)