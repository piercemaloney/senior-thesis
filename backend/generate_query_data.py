"""
This script generates the query data for the tactic lemma generation.
Format:
Import context as commented files
All comments of original file removed
All proofs *kept*
"""

import os
from tqdm import tqdm

from import_context_file_builder import remove_comments_from_file, remove_back_to_back_empty_lines
from generate_data_with_import_context import insert_import_context



def query_file_helper(coq_file_path: str, output_path: str):
    """
    This function takes a Coq file, removes comments and back-to-back empty lines,
    and writes the cleaned text to a new file.
    
    :param coq_file_path: Path to the Coq (.txt) file to be processed.
    :param output_path: Path where the cleaned file will be saved.
    """
    # Remove comments from the Coq file
    cleaned_text = remove_comments_from_file(coq_file_path)
    
    # Remove back-to-back empty lines
    cleaned_text = remove_back_to_back_empty_lines(cleaned_text)
    
    # Write the cleaned text to the output file
    with open(output_path, 'w') as file:
        for line in cleaned_text:
            file.write(f"{line}")
    
def process_files_and_add_import_context(data_dir, import_context_dir, output_dir, instert_import_context=True):
    os.makedirs(output_dir, exist_ok=True)
    for root, _, files in os.walk(data_dir):
        for file in tqdm(files):
            if file.endswith(".txt"):
                data_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(data_file_path, data_dir)
                output_file_path = os.path.join(output_dir, relative_path)
                proj_name = root.split('/')[-1]
                # raise Exception(f"Processing {data_file_path} -> {output_file_path}")
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                insert_import_context(data_file_path, import_context_dir, output_file_path, proj_name)

def clean_text_files(coq_projects_as_text_dir, no_comments_dir):
    for root, _, files in os.walk(coq_projects_as_text_dir):
        proj_name = root.split('/')[-1]
        output_proj_dir = os.path.join(no_comments_dir, proj_name)
        os.makedirs(output_proj_dir, exist_ok=True)
        for file in tqdm(files):
            if file.endswith(".txt"):
                coq_file_path = os.path.join(root, file)
                output_path = os.path.join(output_proj_dir, file)
                query_file_helper(coq_file_path, output_path)
                    

if __name__ == "__main__":
    # Call query file builder to clean the files, output them to directory, then call process_files to add import context
    coq_projects_as_text_dir = './coq_projects_as_txt/'
    import_context_dir = './import_context'
    no_comments_dir = './coq_projects_no_comments'
    clean_text_files(coq_projects_as_text_dir, no_comments_dir)
    query_output_dir = './query_data'
    process_files_and_add_import_context(no_comments_dir, import_context_dir, query_output_dir)
