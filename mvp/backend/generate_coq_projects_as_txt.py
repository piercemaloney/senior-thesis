""" This file just takes the .v files and converts them to .txt files and removes the deep nesting structure."""

from tqdm import tqdm
import os
import glob


def find_v_files(directory):
    """
    Recursively finds all .v files within the given directory.
    """
    return glob.glob(f'{directory}/**/*.v', recursive=True)

def process_v_files(project_dir, output_dir):
    """
    Processes all .v files found in the projects_dir, converting them to .txt files
    and placing them in the output_dir directory.
    """
    v_files = find_v_files(project_dir)
    project_dir_name = os.path.basename(project_dir)  # Get the last part of the project_dir as the project name
    for v_file in tqdm(v_files, desc=f"Processing {str(project_dir)}"):
        v_file_path = v_file  # This already contains the full path
        v_file_relative_path = os.path.relpath(v_file_path, start=project_dir)  # Get the relative path of the .v file from the project_dir
        output_txt_filename =  f"{project_dir_name}.{v_file_relative_path.replace('.v', '.txt').replace(os.sep, '.')}"  # Change the extension from .v to .txt and directory separators to dots
        output_txt_path = os.path.join(output_dir, output_txt_filename)  # Construct the output path

        with open(v_file_path, 'r') as v_file, open(output_txt_path, 'w') as txt_file:
            txt_file.write(v_file.read())

if __name__ == "__main__":
    # Example usage
    projects_dir = '/Users/piercemaloney/Desktop/Thesis/CoqGym/coq_projects'
    output_dir = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/coq_projects_as_txt'

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
        
        process_v_files(project_path, project_output_path)