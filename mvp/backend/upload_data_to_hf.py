"""
Pierce Maloney
Feb 2024
Uploads the CoqGym dataset to the Hugging Face Hub.
"""

from dotenv import load_dotenv
import os
from datasets import Dataset, DatasetDict
import glob

# Load environment variables from .env file
load_dotenv()

# Access the HF_TOKEN environment variable
token = os.getenv("HF_TOKEN")

# Base directory containing the data proj subdirectories
base_dir = "data/"

# Initialize a dictionary to hold our datasets, with keys for train, test, and val
datasets = {"train": [], "test": [], "val": []}

# The splits according to CoqGym
ttv_splits = {"train": ["constructive-geometry", "higman-s", "int-map", "coq-ext-lib", "amm11262", "system", "bellantonicook", "area-method", "hedges", "mini-compiler", "propcalc", "rem", "miniml", "maths", "bdds", "GeoCoq", "generic-environments", "Categories", "ramsey", "cours-de-coq", "axiomatic-abp", "coq", "railroad-crossing", "pts", "exceptions", "smc", "group-theory", "otway-rees", "float", "lambda", "three-gap", "izf", "groups", "ipc", "InfSeqExt", "StructTact", "fcsl-pcm", "hardware", "qarith-stern-brocot", "dictionaries", "automata", "corespec", "qarith", "twoSquare", "QuickChick", "CompCert", "regexp", "domain-theory", "tarski-geometry", "ieee754", "ctltctl", "bigenough", "subst", "lazy-pcf", "ruler-compass-geometry", "search-trees", "finmap", "quicksort-complexity", "math-comp", "pocklington", "algebra", "schroeder", "euler-formula", "shuffle", "bbv", "lemma-overloading", "fssec-model", "tortoise-hare-algorithm", "zf", "metalib"],
              "test": ["weak-up-to", "buchberger", "jordan-curve-theorem", "dblib", "disel", "zchinese", "zfc", "dep-map", "chinese", "UnifySL", "hoare-tut", "huffman", "PolTac", "angles", "coq-procrastination", "coq-library-undecidability", "tree-automata", "coquelicot", "fermat4", "demos", "coqoban", "goedel", "verdi-raft", "verdi", "zorns-lemma", "coqrel", "fundamental-arithmetics"],
              "val": ["lesniewski-mereology", "graphs", "additions", "ChargeCore", "rsa", "cheerios", "circuits", "mod-red", "traversable-fincontainer", "topology", "checker", "cecoa", "VST", "coq-list-string", "markov", "GeometricAlgebra", "ails", "idxassoc", "param-pi", "SCEV-coq", "higman-cf", "distributed-reference-counting", "lin-alg", "orb-stab", "free-groups", "concat", "zsearch-trees"]}


# Function to add texts to the appropriate split
def add_texts_to_split(split_name, texts):
    if split_name in datasets:
        datasets[split_name].extend(texts)
    else:
        print(f"Split name {split_name} not recognized.")

print("Starting to iterate over each project directory in the base directory.")
# Iterate over each project directory in the base directory
for split in os.listdir(base_dir):
    print(f"Processing split: {split}")
    split_dir = os.path.join(base_dir, split)
    if os.path.isdir(split_dir):
        # Check if the directory contains any .txt files
        if not glob.glob(os.path.join(split_dir, "*.txt")):
            print(f"Directory {split_dir} is empty or contains no .txt files. Skipping.")
            continue  # Skip this directory

        # List to store text data
        texts = []
        # Iterate over each text file in the project directory
        for file_path in glob.glob(os.path.join(split_dir, "*.txt")):
            with open(file_path, 'r', encoding='utf-8') as file:
                texts.append(file.read())
        print(f"Added {len(texts)} texts from {split_dir}.")

        # Determine the split based on ttv_splits and add texts to the appropriate list
        for key, projects in ttv_splits.items():
            if split in projects:
                add_texts_to_split(key, texts)
                print(f"Added texts to {key} split.")
                break

# Convert lists to datasets
for key in datasets:
    datasets[key] = Dataset.from_dict({"text": datasets[key]})
    print(f"Converted {key} list to Dataset with {len(datasets[key])} entries.")

# Create a DatasetDict
dataset_dict = DatasetDict({split: datasets[split] for split in ["train", "test", "val"]})

# Push the dataset to the Hugging Face Hub
dataset_dict.push_to_hub("piercemaloney/coqgym_ttv_split_v2", token=token)
