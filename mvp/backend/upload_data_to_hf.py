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

# Initialize a dictionary to hold our datasets, with keys for train, test, and val
datasets = {"train": [], "test": []}

# Function to load data from txt files into lists
def load_data_from_txt(directory):
    data = []
    for filename in glob.glob(os.path.join(directory, '*.txt')):
        with open(filename, 'r', encoding='utf-8') as file:
            data.append({"text": file.read()})
    return data

# Load data from .temp/train and .temp/test directories
datasets["train"] = load_data_from_txt("new_data_with_import_context/train")
datasets["test"] = load_data_from_txt("new_data_with_import_context/test")

# Convert lists of data into Dataset objects
for split in ["train", "test"]:
    text_data = [item["text"] for item in datasets[split]]
    datasets[split] = Dataset.from_dict({"text": text_data})

# Create a DatasetDict
dataset_dict = DatasetDict({split: datasets[split] for split in ["train", "test"]})

# Push the dataset to the Hugging Face Hub
dataset_dict.push_to_hub("piercemaloney/coqgym_with_goals_partial", token=token)