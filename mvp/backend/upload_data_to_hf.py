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

# Base directory containing the data subdirectories
base_dir = "data/"

# Initialize a dictionary to hold our datasets
datasets = {}

# Iterate over each subdirectory in the base directory
for split in os.listdir(base_dir):
    # Replace dashes with underscores in split names
    split_name = split.replace('-', '_')
    split_dir = os.path.join(base_dir, split)
    if os.path.isdir(split_dir):
        # Check if the directory contains any .txt files
        if not glob.glob(os.path.join(split_dir, "*.txt")):
            print(f"Directory {split_dir} is empty or contains no .txt files. Skipping.")
            continue  # Skip this directory

        # List to store text data
        texts = []
        # Iterate over each text file in the subdirectory
        for file_path in glob.glob(os.path.join(split_dir, "*.txt")):
            with open(file_path, 'r', encoding='utf-8') as file:
                texts.append(file.read())
        # Create a dataset for this split
        datasets[split_name] = Dataset.from_dict({"text": texts})

# Create a DatasetDict
dataset_dict = DatasetDict(datasets)

# Push the dataset to the Hugging Face Hub
dataset_dict.push_to_hub("piercemaloney/coqgym_coq_projects_v1", token=token)