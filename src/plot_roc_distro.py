import os
import re
import seaborn as sns
import polars as pl
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from multiprocessing import Pool

def roc(file, ax):

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
    ax.plot(fpr, tpr, color='red', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    ax.plot([0, 1], [0, 1], color='darkgrey', lw=2, linestyle='--')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('FPR')
    ax.set_ylabel('TPR')
    ax.legend(loc='lower right')


def distro_graph(file, ax):

    filtered_data = (
        pl.read_csv(file, infer_schema_length=None)
        .filter(pl.col("Predicted Species_ID").cast(pl.Utf8).str.contains(r'\d+'))
        .select(['Logarithmic probability', 'Known/Unknown'])
    )

    sns.histplot(data=filtered_data, x="Logarithmic probability", hue="Known/Unknown", ax=ax, fill=True, palette={"Known": "navy", "Unknown": "red"}, hue_order=["Unknown", "Known"], bins=1000)

    mode = filtered_data["Logarithmic probability"].mode()[0]
    margin = 150
    ax.set_xlim(mode - margin, mode + margin)
    ax.set_xlabel("Log probability")
    ax.set_ylabel("Count")


def main(taxa):

    directory = Path(f'/ifs/groups/rosenMRIGrp/kr3288/extended/modified_results/{taxa}_modified')

    file_paths = [str(file) for file in directory.iterdir()]
    trials = ['trial_1', 'trial_2', 'trial_3', 'trial_4', 'trial_5']
    file_dict = {trial: [x for x in file_paths if trial in x] for trial in trials}

    file_dict = {trial: sorted(paths, key=lambda x: int(''.join(filter(str.isdigit, x.split("/")[-1].split("_")[-1])))) for trial, paths in file_dict.items()}

    for title, files in file_dict.items():

        fig, ax = plt.subplots(5, 2, figsize=(20, 40))
        plt.subplots_adjust(top=0.95)
        for i, f in enumerate(files):
            roc(f, ax[i,0])
            distro_graph(f, ax[i,1])
            row_title_ax = fig.add_subplot(5, 1, i+1, frameon=False)
            row_title_ax.set_xticks([])
            row_title_ax.set_yticks([])
            row_title_ax.set_title(re.search(r'\d+', f.split("/")[-1].split("_")[-1].split("_")[0]).group() + "-mers", fontsize=14, fontweight='bold')

        fig.suptitle(title.capitalize(), fontsize=16, fontweight='bold')
        plt.savefig(f'/ifs/groups/rosenMRIGrp/kr3288/extended/images/{taxa}_{title}.png')


if __name__ == "__main__":

    num_threads = int(os.environ.get('SLURM_NTASKS', 48))

    with Pool(processes=num_threads) as pool:
        pool.map(main, ["phylum", "class", "order", "family"])
