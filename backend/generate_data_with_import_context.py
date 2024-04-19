"""
Author: Pierce Maloney
Feb 2024
Description: This script is takes already generated data/ and /import_context dirs and inserts the import context
into the data, outputting to /data_with_import_context.
"""

import os
import subprocess
from tqdm import tqdm
import fnmatch

# Paths to the directories

data_dir = './data'
import_context_dir = './import_context'
output_dir = './data_with_import_context'
# txt_file_builder_path = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/txt_file_with_context_builder.py'


def insert_import_context(data_file_path, import_context_root_dir, output_file_path, proj_name):
    with open(data_file_path, 'r') as data_file, open(output_file_path, 'w') as output_file:
        for line in data_file:
            output_file.write(line)
            if "Require Import" in line or "Require Export" in line:
                import_names = extract_import_names(line)
                for import_name in import_names:
                    pattern = f"*.{import_name}.txt"
                    matching_files = []

                    # Collect all matching files first
                    for import_context_root, _, import_context_files in os.walk(os.path.join(import_context_root_dir, proj_name)):
                        for import_context_file in fnmatch.filter(import_context_files, pattern):
                            matching_files.append(os.path.join(import_context_root, import_context_file))

                    # If there's only one file left after filtering, use it
                    if len(matching_files) == 1:
                        best_match = matching_files[0]
                        with open(best_match, 'r') as import_context_file:
                            import_context_content = import_context_file.read().strip()
                            output_file.write(f"(* {import_name}:\n{import_context_content} *)\n")


def extract_import_names(line):
    import_statement_parts = line.strip().split()
    import_names_start_index = import_statement_parts.index("Import") + 1 if "Import" in import_statement_parts else import_statement_parts.index("Export") + 1
    import_names = import_statement_parts[import_names_start_index:]
    for i, import_name in enumerate(import_names):
        if import_name.endswith('.'):
            import_names[i] = import_name[:-1]
            import_names = import_names[:i+1]
            break
    if line.startswith("From"):
        base_import_name = import_statement_parts[1]
        import_names = [base_import_name + '.' + name for name in import_names]
    return import_names

def process_files(data_dir, import_context_dir, output_dir):
    # Directories to process
    directories_to_process = ['train', 'test']
    
    for directory in directories_to_process:
        current_data_dir = os.path.join(data_dir, directory)
        current_output_dir = os.path.join(output_dir, directory)
        
        # Ensure the output directory exists
        os.makedirs(current_output_dir, exist_ok=True)
        
        # Process each file in the current directory
        for root, dirs, files in os.walk(current_data_dir):
            for file in tqdm(files):
                if file.endswith(".txt"):
                    data_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(data_file_path, current_data_dir)
                    output_file_path = os.path.join(current_output_dir, relative_path.replace('.json', ''))
                    proj_name = output_file_path.split('/')[-1].split('.')[0]
                    # print(f"Processing {data_file_path} -> {output_file_path}")
                    # print(f"Project name: {proj_name}")
                    insert_import_context(data_file_path, import_context_dir, output_file_path, proj_name)

def main():
    process_files(data_dir, import_context_dir, output_dir)

if __name__ == "__main__":
    main()
