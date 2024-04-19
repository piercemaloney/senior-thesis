"""
Author: Pierce Maloney
Feb 2024
"""


import json
from pathlib import Path

import sys
sys.path.append('/workspace/CoqGym')


# Load JSON Data
def load_json_data(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def fetch_goal_states(proofs, goals):
    goal_states = {}
    for proof in proofs:
        for step in proof['steps']:
            fg_ids = step['goal_ids']['fg']  # Focused goals
            bg_ids = step['goal_ids']['bg']  # Unfocused goals
            # Fetch the goal states for both focused and unfocused goals
            fg_states = [goals[str(fg_id)] for fg_id in fg_ids]
            bg_states = [goals[str(bg_id)] for bg_id in bg_ids if bg_id in goals]
            # Store the combined goal states for this step
            goal_states[step['command'][2]] = {'fg': fg_states, 'bg': bg_states}
    return goal_states

def construct_goal_states_mapping(data):
    goal_states_mapping = {}
    for proof in data['proofs']:
        for step in proof['steps']:
            goal_ids = step['goal_ids']['fg']  # Focused goals
            # Assuming goal information is directly accessible or can be fetched using another function
            goals = [proof['goals'][str(goal_id)] for goal_id in goal_ids]
            # hypotheses = [hypo for goal_id in goal_ids for hypo in proof['goals'][str(goal_id)]['hypotheses']]
            goal_states_mapping[step['command'][2]] = goals  # Using command hash as key
    return goal_states_mapping


def annotate_coq_file_with_goals(data, goal_states_mapping, coq_file_path):
    enhanced_text = []
    with open(coq_file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        # Find the command hash that matches this line, if any
        for cmd in data['vernac_cmds']:
            if cmd[0].strip() in line.strip():
                hash_code = cmd[2]
                if hash_code in goal_states_mapping:
                    for goal in reversed(goal_states_mapping[hash_code]):
                        # Format and append the goal state
                        enhanced_text.append(f"(* Goal: {goal['type']} *)\n")
                break  # Stop looking after the first match to avoid duplicates
        enhanced_text.append(line)

    return enhanced_text

def write_to_txt_file(enhanced_text, output_path):
    with open(output_path, 'w') as file:
        file.writelines(enhanced_text)



def main():
    if len(sys.argv) != 4:
        print("Usage: txt_file_builder.py <json_path> <coq_file_path> <destination_dir>")
        sys.exit(1)

    json_path = sys.argv[1]
    coq_file_path = sys.argv[2]
    destination_dir = sys.argv[3]

    data = load_json_data(json_path)
    goal_states_mapping = construct_goal_states_mapping(data)
    enhanced_text = annotate_coq_file_with_goals(data, goal_states_mapping, coq_file_path)
    write_to_txt_file(enhanced_text, destination_dir)

if __name__ == "__main__":
    main()