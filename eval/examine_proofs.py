import json
from tqdm import tqdm
import csv

def load_and_analyze_proofs(files):
    analysis_results = []  # List to store analysis results for each file

    for file_path in tqdm(files):
        with open(file_path, 'r') as file:
            data = json.load(file)

        proofs = data.get('proofs', [])
        
        proof_count = 0
        total_steps_count = 0
        max_steps_count = 0
        for proof in proofs:
            proof_count += 1
            steps = proof.get('steps', [])
            steps_count = sum(step['command'][0].count(';') + 1 for step in steps)
            total_steps_count += steps_count
            if steps_count > max_steps_count:
                max_steps_count = steps_count
        
        if proof_count > 0:  # To avoid division by zero
            average_steps = total_steps_count / proof_count
        else:
            average_steps = 0
        
        # Store the results in the list
        analysis_results.append({
            'file_path': file_path,
            'total_steps': total_steps_count,
            'average_steps_per_proof': average_steps,
            'max_proof_steps': max_steps_count
        })

    # Sort the results by average steps per proof
    sorted_results = sorted(analysis_results, key=lambda x: x['average_steps_per_proof'])

    return sorted_results

def save_results_to_csv(results, filename='analysis_results.csv'):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['File Path', 'Total Steps', 'Average Steps Per Proof', 'Max Steps Per Proof'])
        # Write the data rows
        for result in results:
            writer.writerow([result['file_path'], result['total_steps'], round(result['average_steps_per_proof'], 1), result['max_proof_steps']])

if __name__ == "__main__":
    with open('proofs_split.json', 'r') as file:
        files = json.load(file)['proofs_valid']
        results = load_and_analyze_proofs(files)
    for result in results:
        print(f"File '{result['file_path']}' has {result['total_steps']} steps, avg {round(result['average_steps_per_proof'], 1)}, max {result['max_proof_steps']}.")
    # Save the results to a CSV file
    # save_results_to_csv(results)
    
