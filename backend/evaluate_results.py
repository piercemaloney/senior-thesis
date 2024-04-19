import os
import json

def get_json_set(directory):
    json_files = set()
    for _, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                json_files.add(file)  # Store only the file name
    return json_files

def evaluate_results(directory, common_files):
    results_summary = {
        'total_generated_tactics': 0,
        'total_errors': 0,
        'total_eval_queries': 0,
        'total_proofs_attempted': 0,
        'total_proofs_completed': 0,
    }

    for subdir, _, files in os.walk(directory):
        for file in files:
            # if file in common_files:  # Check if the file is in the intersection set
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    max_eval_score = count_max_eval_score(data["tree"])
                    errors = count_errors(data["tree"])
                    if max_eval_score <= 0.001 and directory.endswith('a_star'):
                        continue
                    results_summary['total_proofs_attempted'] += 1
                    results_summary['total_generated_tactics'] += count_children(data["tree"])
                    results_summary['total_errors'] += errors
                    if data.get('successful_tactic_path', False):
                        results_summary['total_proofs_completed'] += 1


    # Calculate percentages
    if results_summary['total_proofs_attempted'] > 0:
        proofs_percentage = (results_summary['total_proofs_completed'] / results_summary['total_proofs_attempted']) * 100
    else:
        proofs_percentage = 0
    
    legal_tactics_percentage = ((results_summary['total_generated_tactics'] - results_summary['total_errors']) / results_summary['total_generated_tactics']) * 100
    
    print("-------")
    print(f"Results Summary for {directory}")
    # print(f"Total Generated Tactics: {results_summary['total_generated_tactics']}")
    # print(f"Total Errors: {results_summary['total_errors']}")
    # print(f"Legal Tactics Percentage: {legal_tactics_percentage:.2f}%")
    # print(f"Total Eval Queries: {results_summary['total_eval_queries']}")
    print(f"Total Proofs Attempted: {results_summary['total_proofs_attempted']}")
    print(f"Proofs Completed Successfully: {results_summary['total_proofs_completed']} ({proofs_percentage:.2f}%)")

def count_errors(node):
    """
    Recursively counts the total number of errors in a tree.
    
    :param node: The current node in the tree.
    :return: The total number of errors in the tree.
    """
    if not node.get('children'):  # Base case: no children
        return 1 if node.get('eval_score') < 0 else 0
    
    # Count the errors of the current node
    total_errors = 1 if node.get('eval_score') < 0 else 0
    for child in node['children']:
        total_errors += count_errors(child)
    return total_errors

def count_children(node):
    """
    Recursively counts the total number of children in a tree node.
    
    :param node: The current node in the tree.
    :return: The total number of children in the tree.
    """
    if not node.get('children'):  # Base case: no children
        return 0
    else:
        # Count the children of the current node
        total_children = len(node['children'])
        for child in node['children']:
            total_children += count_children(child)
        return total_children

def count_max_children(node):
    """
    Recursively counts the maximum number of children in a tree node.
    
    :param node: The current node in the tree.
    :return: The maximum number of children in the tree.
    """
    if not node.get('children'):  # Base case: no children
        return 0
    else:
        # Count the children of the current node and recursively find the max in its children
        max_children = len(node['children'])
        for child in node['children']:
            # Compare the current max with the max of its children
            max_children = max(max_children, count_max_children(child))
        return max_children
    
def count_max_eval_score(node):
    """
    Recursively counts the maximum evaluation score in a tree node.
    
    :param node: The current node in the tree.
    :return: The maximum evaluation score in the tree.
    """
    if not node.get('children'):  # Base case: no children
        return node.get('eval_score', 0)
    else:
        # Find the max evaluation score in the current node's children
        max_eval_score = node.get('eval_score', 0)
        for child in node['children']:
            # Compare the current max with the max of its children
            max_eval_score = max(max_eval_score, count_max_eval_score(child))
        return max_eval_score

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

    # Now common_files contains only the names of files present in all subdirectories
    # You can now call evaluate_results for each subdir, passing common_files as an argument
    for subdir in os.listdir(directory):
        if subdir == 'llemma_v3_a_star' or subdir == 'llemma_v5_a_star':
            continue
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            evaluate_results(subdir_path, common_files)



"""
Most recent results
-------
Results Summary for results/llemma_base_a_star
Total Directories Processed: 1
Total Generated Queries: 369
Total Eval Queries: 486
Total Proofs Attempted: 68
Proofs Completed Successfully: 36 (52.94%)
-------
Results Summary for results/llemma_v4_greedy
Total Directories Processed: 1
Total Generated Queries: 1258
Total Eval Queries: 1001
Total Proofs Attempted: 259
Proofs Completed Successfully: 80 (30.89%)
-------
Results Summary for results/llemma_v4_a_star
Total Directories Processed: 1
Total Generated Queries: 842
Total Eval Queries: 824
Total Proofs Attempted: 166
Proofs Completed Successfully: 93 (56.02%)
-------
Results Summary for results/gpt4_a_star
Total Directories Processed: 1
Total Generated Queries: 270
Total Eval Queries: 273
Total Proofs Attempted: 54
Proofs Completed Successfully: 20 (37.04%)
-------
Results Summary for results/llemma_base_greedy
Total Directories Processed: 1
Total Generated Queries: 474
Total Eval Queries: 402
Total Proofs Attempted: 73
Proofs Completed Successfully: 36 (49.32%)
"""
    