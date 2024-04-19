import os
import subprocess
import json


def run_evaluation_on_json(json_file_path):
    # Call my_eval_env.py with the filepath as an argument
    print(f"Running evaluation on {json_file_path}")
    subprocess.run(["python", "my_eval_env.py", json_file_path])

def is_valid_project(file, valid_projects):
    # Check if the file (without extension) is in the list of valid projects
    return os.path.splitext(file)[0] in valid_projects

if __name__ == "__main__":
    data_path = "data"

    # Load validation projects from projs_split.json
    with open('projs_split.json') as f:
        projs_split = json.load(f)
    valid_projects = projs_split['projs_valid']

    # Create a list to hold all the JSON file paths for evaluation
    json_files_for_evaluation = []

    for root, dirs, files in os.walk(data_path):
        path_parts = root.split(os.sep)
        if len(path_parts) > 1:
            proj_name = path_parts[1]
            if proj_name not in valid_projects or proj_name == 'coq':
                continue
        else:
            continue
        for file in files:
            if file.endswith('.json'):
                full_path = os.path.join(root, file)
                print(f"Adding JSON file for evaluation: {full_path}")  # Debug print
                json_files_for_evaluation.append(full_path)

    # Run evaluations sequentially
    for json_file_path in json_files_for_evaluation:
        run_evaluation_on_json(json_file_path)
