"""
Author: Pierce Maloney
Feb 2024
Description: This script generates context files from Coq proof files (.v) using import_context_file_builder.py.
The output directory is set to store the context files.
"""

import os
import subprocess
from tqdm import tqdm
import glob

# Paths to the directories
projects_dir = '/Users/piercemaloney/Desktop/Thesis/CoqGym/coq_projects'
output_dir = './import_context'
context_file_builder_path = './import_context_file_builder.py'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

def call_context_file_builder(v_file_path, output_txt_path):
    try:
        subprocess.run(['python', context_file_builder_path, v_file_path, output_txt_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing {v_file_path}: {e}")

# Function to find all .v files within a given directory, including nested directories
def find_v_files(directory):
    return glob.glob(f'{directory}/**/*.v', recursive=True)

# Iterate through each project in the projects directory
for project_name in os.listdir(projects_dir):
    if project_name == 'coq':
        continue
    
    project_path = os.path.join(projects_dir, project_name)
    project_output_path = os.path.join(output_dir, project_name)

    # Check if the project's output directory already exists
    if os.path.isdir(project_output_path):
        print(f"Skipping {project_name}, output directory already exists.")
        continue  # Skip to the next project
    
    # Check if it's a directory
    if os.path.isdir(project_path):
        # print(f"Creating output directory at {project_output_path} if it doesn't exist.")
        os.makedirs(project_output_path, exist_ok=True)

        # Find all .v files in the project directory, including nested directories
        # print(f"Searching for .v files in {project_path}.")
        v_files = find_v_files(project_path)
        # print(f"Found {len(v_files)} .v files.")

        for v_file in tqdm(v_files, desc=f"Processing {project_name}"):
            v_file_path = v_file  # This already contains the full path
            v_file_relative_path = os.path.relpath(v_file_path, start=projects_dir)  # Get the relative path of the .v file from the projects_dir
            output_txt_path = os.path.join(project_output_path, v_file_relative_path.replace('.v', '.txt').replace(os.sep, '.'))

            # print(f"Calling context file builder for {v_file_path}.")
            call_context_file_builder(v_file_path, output_txt_path)
    