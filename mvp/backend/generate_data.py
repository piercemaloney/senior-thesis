"""
Author: Pierce Maloney
Feb 2024
Description: This script is designed to be mounted and run inside a docker container with CoqGym. 
It transforms Coq proof files into a .txt format that alternates between tactics and proof states.
Mirrors the data and coq_projects directories.
"""

import os
import subprocess
from tqdm import tqdm
import glob

# Paths to the directories
# data_dir = '/workspace/CoqGym/data'
# projects_dir = '/workspace/CoqGym/coq_projects'
# output_dir = '/app/data'
# txt_file_builder_path = '/app/txt_file_builder.py'

data_dir = '/Users/piercemaloney/Desktop/Thesis/CoqGym/data'
projects_dir = '/Users/piercemaloney/Desktop/Thesis/CoqGym/coq_projects'
output_dir = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/data'
txt_file_builder_path = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/txt_file_builder.py'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

def call_txt_file_builder(json_file_path, v_file_path, output_txt_path):
    try:
        subprocess.run(['python', txt_file_builder_path, json_file_path, v_file_path, output_txt_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing {v_file_path}: {e}")

# Function to find all .v files within a given directory, including nested directories
def find_v_files(directory):
    return glob.glob(f'{directory}/**/*.v', recursive=True)

# Iterate through each project in the data directory
for project_name in os.listdir(data_dir):
    if project_name == 'coq':
        continue

    project_data_path = os.path.join(data_dir, project_name)
    project_output_path = os.path.join(output_dir, project_name)

    # Check if the project's output directory already exists
    if os.path.isdir(project_output_path):
        print(f"Skipping {project_name}, output directory already exists.")
        continue  # Skip to the next project
    
    # Check if it's a directory
    if os.path.isdir(project_data_path):
        # print(f"Creating output directory at {project_output_path} if it doesn't exist.")
        os.makedirs(project_output_path, exist_ok=True)

        # print(f"Listing all JSON files in {project_data_path}.")
        json_files = glob.glob(f'{project_data_path}/**/*.json', recursive=True)
        # print(f"Found {len(json_files)} JSON files.")

        # Find all .v files in the corresponding project directory within projects_dir, including nested directories
        # print(f"Searching for .v files in {os.path.join(projects_dir, project_name)}.")
        v_files = find_v_files(os.path.join(projects_dir, project_name))
        # print(f"Found {len(v_files)} .v files.")

        for json_file in tqdm(json_files, desc=f"Processing {project_name}"):
            json_file_path = json_file  # This already contains the full path
            json_relative_path = os.path.relpath(json_file_path, start=data_dir)  # Get the relative path of the json file from the data_dir
            v_file_relative_path = json_relative_path.replace('.json', '.v')  # Replace .json with .v to get the relative path of the .v file
            v_file_path = os.path.join(projects_dir, v_file_relative_path)  # Construct the full path to the .v file within the projects_dir

            # print(f"Looking for {v_file_path}.") 

            if os.path.exists(v_file_path):
                # print(f"Found corresponding .v file for {json_file_path}.")
                output_txt_path = os.path.join(project_output_path, v_file_relative_path.replace('.v', '.txt').replace(os.sep, '.'))
                # print(f"Calling txt file builder for {json_file_path}.")
                call_txt_file_builder(json_file_path, v_file_path, output_txt_path)
            else:
                print(f"Warning: No corresponding .v file found for {json_file_path}")