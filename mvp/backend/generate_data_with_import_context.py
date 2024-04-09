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

data_dir = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/data'
import_context_dir = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/import_context'
output_dir = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/data_with_import_context'
txt_file_builder_path = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/txt_file_with_context_builder.py'

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)


def insert_import_context(data_dir, import_context_dir, output_dir):
    # Iterate through the files in the data directory
    for root, dirs, files in os.walk(data_dir):
        proj_name = root.split('/')[-1]
        for file in files:
            if file.endswith(".txt"):
                
                print(f"Processing {file}")
                # Construct the path to the data file
                data_file_path = os.path.join(root, file)
                # Calculate the relative path of the data file
                relative_path = os.path.relpath(data_file_path, data_dir)
                # Construct the output file path based on the relative path
                output_file_path = os.path.join(output_dir, relative_path)
                # Ensure the directory for the output file exists
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

                
                # Open the data file for reading and the output file for writing
                with open(data_file_path, 'r') as data_file, open(output_file_path, 'w') as output_file:
                    # Read each line from the data file              
                    
                    for line in data_file:

                        # Write the line to the output file
                        output_file.write(line)
                        # Check if the line is an import statement
                        if "Require Import" in line:
                            # Split the line into parts after "Require Import"
                            import_statement_parts = line.strip().split()
                            import_names_start_index = import_statement_parts.index("Import") + 1
                            import_names = import_statement_parts[import_names_start_index:]
                            for i, import_name in enumerate(import_names):
                                if import_name.endswith('.'):
                                    import_names[i] = import_name[:-1]
                                    import_names = import_names[:i+1]
                                    break
                            if line.startswith("From"):
                                base_import_name = import_statement_parts[1]
                                import_names = [base_import_name + '.' + name for name in import_names]
                            # print(import_names)
                            
                            for import_name in import_names:
                                # Construct a pattern to match files ending with the import name
                                pattern = f"*{import_name}.txt"
                                # Search for matching files in the import_context_dir
                                for import_context_root, _, import_context_files in os.walk(import_context_dir+'/'+proj_name):
                                    for import_context_file in import_context_files:
                                        if fnmatch.fnmatch(import_context_file, pattern):
                                            import_context_path = os.path.join(import_context_root, import_context_file)
                                            # print(f"Inserting import context from {import_context_path} into {output_file_path}")
                                            with open(import_context_path, 'r') as import_context_file:
                                                import_context_content = import_context_file.read().strip()
                                                output_file.write(f"(* {import_name}:\n{import_context_content} *)\n")


insert_import_context(data_dir, import_context_dir, output_dir)