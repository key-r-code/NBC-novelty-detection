import os
import pandas as pd
import random
import sys
import subprocess
from multiprocessing import Pool

def random_400(list_):
    return random.sample(list_, 400)

def copy_folder_batch(args):
    folder, source_dir, destination_path = args
    try:
        source_path = f"{source_dir}/{folder}"
        cmd = f"rsync -a {source_path} {destination_path}/"
        subprocess.run(cmd, shell=True, check=True)
        print(f"Copied: {folder}")
    except subprocess.CalledProcessError as e:
        print(f"Error copying {folder}: {str(e)}")

def parallel_copy(folder_list, destination_path):
    source_dir = r'/ifs/groups/rosenMRIGrp/kr3288/extended/fna_grouped_by_species_tax'
    num_threads = int(os.environ.get('SLURM_NTASKS', 48))
    print(f"Using {num_threads} parallel processes")

    args_list = [(folder, source_dir, destination_path) for folder in folder_list]

    with Pool(processes=num_threads) as pool:
        pool.map(copy_folder_batch, args_list)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Wrong usage")
        print("Correct usage: python3 everything_extended.py <taxa (1st letter cap)> <trial (1st letter cap)>")
        sys.exit(1)

    csv_file = r'/ifs/groups/rosenMRIGrp/kr3288/extended/extended_lineage.csv'

    df = pd.read_csv(csv_file)
    df = df.fillna('')
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    taxa_level = sys.argv[1].capitalize()
    trial_number = sys.argv[2]

    dx = df[['Species_ID', taxa_level]]
    dx = dx[dx[taxa_level].isin(dx[taxa_level].value_counts()[dx[taxa_level].value_counts() >= 400].index)]
    dx = dx[dx[taxa_level] != '']

    grouped_dfs = {name: group.reset_index(drop=True) for name, group in dx.groupby(taxa_level)}
    grouped_dfs = {key.lower(): value for key, value in grouped_dfs.items()}

    folder_name = f'/ifs/groups/rosenMRIGrp/kr3288/extended/{taxa_level.lower()}_testing/3-mers/training_data/{trial_number}'
    os.makedirs(folder_name, exist_ok=True)

    try:
        training_taxa = random.sample(list(grouped_dfs.keys()), int(len(list(grouped_dfs.keys()))/2))
        training_data = []

        for taxa in training_taxa:
            selected_list = random_400(set(grouped_dfs[taxa]['Species_ID'].tolist()))
            training_data.extend(selected_list)

        os.makedirs(folder_name, exist_ok=True)
        parallel_copy(training_data, folder_name)

    except Exception as e:
        print(f"Error processing folder {folder_name}: {str(e)}")