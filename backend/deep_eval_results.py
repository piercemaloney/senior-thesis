import os
import json
from evaluate_results import get_json_set, count_children, count_max_eval_score

def evaluate_probabilities_at_proof_steps(directory, common_files):
    query_data = {} 
    total_proofs_attempted = 0
    total_successful_proofs = 0

    for subdir, _, files in os.walk(directory):
        for file in files:
            if file in common_files:
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    num_children = count_children(data['tree'])
                    max_eval_score = count_max_eval_score(data["tree"])
                    if max_eval_score <= 0.001 and directory.endswith('a_star'):
                        continue
                    if num_children >= 100:
                        print(file_path)
                    successful = 1 if data.get('successful_tactic_path', False) else 0
                    total_proofs_attempted += 1
                    total_successful_proofs += successful
                    query_data[num_children] = query_data.get(num_children, 0) + successful

    # print("-------")
    # print(f"Results Summary for {directory}")
    # print(f"Total proofs attempted: {total_proofs_attempted}")
    # print(f"Total successful proofs: {total_successful_proofs}")

    # Cumulative sum
    for key in range(1, max(query_data.keys()) + 1):
        if key > 1:
            query_data[key] = query_data.get(key, 0) + query_data.get(key-1, 0)


    # Convert to probabilities
    if total_proofs_attempted > 0:
        for key in query_data:
            query_data[key] = query_data[key] / total_proofs_attempted

    x_values = []
    y_values = []
    for key in sorted(query_data.keys()):
        x_values.append(key)
        y_values.append(round(query_data[key], 3))
    
    print(f"{directory.split('/')[-1]} = {y_values}")

if __name__ == "__main__":
    directory = 'results'
    common_files = set()
    first_iteration = True

    for subdir in os.listdir(directory):
        if subdir == 'llemma_v3_a_star' or subdir == 'llemma_v5_a_star':
            continue
            
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            json_files = get_json_set(subdir_path)
            if first_iteration:
                common_files = json_files
                first_iteration = False
            else:
                common_files = common_files.intersection(json_files)

    # common_files contains only the names of files present in all subdirectories
    for subdir in os.listdir(directory):
        if subdir == 'llemma_v3_a_star' or subdir == 'llemma_v5_a_star':
            continue
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            evaluate_probabilities_at_proof_steps(subdir_path, common_files)