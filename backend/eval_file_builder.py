import sys
import json

# Load JSON Data
def load_json_data(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

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

def get_text_before_first_goal(data, coq_file_path, goal_states_mapping):
    with open(coq_file_path, 'r') as file:
        lines = file.readlines()

    for line_index, line in enumerate(lines):
        for cmd in data['vernac_cmds']:
            if cmd[0].strip() in line.strip():
                hash_code = cmd[2]
                if hash_code in goal_states_mapping:  # Assuming goal_states_mapping is available
                    # Return all lines up until the current one as soon as the first goal is found
                    return lines[:line_index]
    # If no goal is found, return the entire text
    return lines


def main():
    if len(sys.argv) != 4:
        print("Usage: eval_file_builder.py <json_path> <coq_file_path> <destination_dir>")
        sys.exit(1)

    json_path = sys.argv[1]
    coq_file_path = sys.argv[2]
    destination_dir = sys.argv[3]

    data = load_json_data(json_path)
    goal_states_mapping = construct_goal_states_mapping(data)

    text_before_first_goal = get_text_before_first_goal(data, coq_file_path)
    print(''.join(text_before_first_goal))


if __name__ == "__main__":
    main()