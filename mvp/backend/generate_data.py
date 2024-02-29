"""
Author: Pierce Maloney
Feb 2024
Description: This script is designed to be mounted and run inside a docker container with CoqGym. 
It transforms Coq proof files into a .txt format that alternates between tactics and proof states.
Mirrors the data and coq_projects directories.
"""

import os
import subprocess
from tqdm import tqdm  # Import tqdm

# Paths to the directories
data_dir = '/workspace/CoqGym/data'
projects_dir = '/workspace/CoqGym/coq_projects'
output_dir = '/app/data'

# path to txt_file_builder.py
txt_file_builder_path = '/app/txt_file_builder.py'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

def call_txt_file_builder(json_file_path, v_file_path, output_txt_path):
    subprocess.run(['python', txt_file_builder_path, json_file_path, v_file_path, output_txt_path], check=True)

# Iterate through each project in the data directory
for project_name in os.listdir(data_dir):
    project_data_path = os.path.join(data_dir, project_name)
    project_output_path = os.path.join(output_dir, project_name)

    # Check if the project's output directory already exists
    if os.path.isdir(project_output_path):
        print(f"Skipping {project_name}, output directory already exists.")
        continue  # Skip to the next project
    
    # Check if it's a directory
    if os.path.isdir(project_data_path):
        os.makedirs(project_output_path, exist_ok=True)

        json_files = [f for f in os.listdir(project_data_path) if f.endswith('.json')]
        # Wrap the list of .json files with tqdm for a progress bar
        for json_file in tqdm(json_files, desc=f"Processing {project_name}"):
            json_file_path = os.path.join(project_data_path, json_file)
            v_file_name = json_file.replace('.json', '.v')
            v_file_path = os.path.join(projects_dir, project_name, v_file_name)
            output_txt_path = os.path.join(project_output_path, v_file_name.replace('.v', '.txt'))

            if os.path.exists(v_file_path):
                call_txt_file_builder(json_file_path, v_file_path, output_txt_path)
            else:
                print(f"Warning: No corresponding .v file found for {json_file_path}")