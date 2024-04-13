# Environment for interacting with Coq theorems during testing
from serapi import SerAPI, CoqExn, CoqTimeout
import re
from copy import deepcopy
from time import time
from collections import OrderedDict
import json
import sexpdata
from utils import update_env
import os
from glob import glob
import pdb
import requests
import queue
import argparse

from eval_env import FileEnv, ProofEnv



def get_proof_and_goals(proof_name, proofs_data):
    ret = ""
    for i, proof in enumerate(proofs_data):
        if proof['proof_name'] == proof_name:
            data = proofs_data.pop(i)  # Pop the proof from proofs_data
            for tactic_and_goals in data['tactics_and_goals']:
                ret += f"{tactic_and_goals['tactic']}\n"
                fg_goals = tactic_and_goals['goals']['fg'][::-1]
                bg_goals = tactic_and_goals['goals']['bg'][::-1]
                if fg_goals:
                    for goal in fg_goals:
                        ret += f"(* Goal: {goal} *)\n"
                elif bg_goals:
                    for goal in bg_goals:
                        ret += f"(* BG Goal: {goal} *)\n"
            break  # Exit the loop once the matching proof_name is found
    return ret


# if __name__ == "__main__":
#     filename = "data/StructTact/Assoc.json"
#     print(f"Processing file: {filename}")

#     output_base_path = "/app/.temp/"
#     import_context_base_path = "/app/import_context/"

#     proj_name = filename.split("/")[1]
    
#     num_proof = 0
#     finished_all_proof_envs = False

#     # Get import context path
#     path_parts = filename.split('/')[1:]  # Split after data/
#     formatted_path = '.'.join(path_parts).replace('.json', '.txt')
#     query_context_path = os.path.join(import_context_base_path, proj_name, formatted_path)
    
#     proofs_data = []  # This will hold the data for all proofs

#     with FileEnv(filename, max_num_tactics=1000, timeout=600) as file_env:
#         for proof_env in file_env:  # Each proof_env is an instance of ProofEnv
#             print(f"Working on proof: {proof_env.proof['name']}")
            
#             proof_dict = {"proof_name": proof_env.proof['name'], "tactics_and_goals": []}
            
#             initial_feedback = proof_env.init()
#             for goal in initial_feedback['fg_goals']:
#                 print(f"Goal Type: {goal['type']}")

#             while not proof_env.success and not proof_env.failure:
#                 if proof_env.num_tactics_left <= 0:
#                     print("Reached maximum number of tactics.")
#                     break

#                 if len(proof_env.proof['steps']) == 0:
#                     print("No more steps available in the proof.")
#                     break

#                 next_step = proof_env.proof['steps'].pop(0)  # Removes the first element and returns it
#                 next_command = next_step['command'][0]  # Fetch the command from the tuple

#                 print(f"Executing command: {next_command}")
#                 feedback = proof_env.step(next_command)

#                 # Collect goals after applying the tactic
#                 fg_goals = [goal['type'] for goal in feedback.get('fg_goals', [])]
#                 bg_goals = [goal['type'] for goal in feedback.get('bg_goals', [])]

#                 # Append the tactic and its resulting goals to the proof_dict
#                 proof_dict["tactics_and_goals"].append({"tactic": next_command, "goals": {"fg": fg_goals, "bg": bg_goals}})

#             if proof_env.success:
#                 print(f"SUCEESFULLY PROVED {proof_env.proof['name']}")
#             elif proof_env.failure:
#                 print(f"FAILED to prove {proof_env.proof['name']}")
#             else:
#                 print(f"Proof for {proof_env.proof['name']} ended prematurely.")
            
#             proofs_data.append(proof_dict)  # Append the proof's data to the list
    

#     proof_file = ""
#     proof_start_keywords = ['Theorem', 'Lemma', 'Corollary', 'Proposition', 'Fact', 'Global Instance', 'Definition', 'Remark', 'Let', "Goal", "Fixpoint"]
    
#     for proof in proofs_data:
#         print(f"Proof Name: {proof['proof_name']}")

#     with open(query_context_path, 'r') as file:
#         found_proof_statement = False
#         for line in file:
#             proof_file += line
#             matched_proof_start_keyword = None  # Variable to store the matched keyword
#             for keyword in proof_start_keywords:
#                 if keyword in line.replace(":", ""):
#                     matched_proof_start_keyword = keyword  # Store the matched keyword
#                     break  # Exit the loop once a match is found

#             if matched_proof_start_keyword is not None:
#                 proof_name = line.split()[1] if matched_proof_start_keyword != 'Global Instance' else line.split()[2]
#                 # print("PROOF NAME: ", proof_name)
#                 proof_name = proof_name.replace(":", "")
#                 found_proof_statement = True
#             if found_proof_statement and '.' in line:
#                 # Add in the lines
#                 proof_file += get_proof_and_goals(proof_name, proofs_data)
#                 # print("PROOF AND GOALS: ", get_proof_and_goals(proof_name, proofs_data))
#                 found_proof_statement = False
    


def generate_proof_content(filename):
    """
    Process a single proof file and generate the content to be saved.
    """
    proof_file = ""
    proof_start_keywords = ['Theorem', 'Lemma', 'Corollary', 'Proposition', 'Fact', 'Global Instance', 'Definition', 'Remark', 'Let', "Goal", "Fixpoint"]
    proofs_data = []
    import_context_base_path = "/app/import_context/"
    

    with FileEnv(filename, max_num_tactics=1000, timeout=600) as file_env:
        for proof_env in file_env:  # Each proof_env is an instance of ProofEnv
            print(f"Working on proof: {proof_env.proof['name']}")
            
            proof_dict = {"proof_name": proof_env.proof['name'], "tactics_and_goals": []}
            
            initial_feedback = proof_env.init()
            fg_goals = [goal['type'] for goal in initial_feedback.get('fg_goals', [])]
            bg_goals = [goal['type'] for goal in initial_feedback.get('bg_goals', [])]
            # Append the tactic and its resulting goals to the proof_dict
            proof_dict["tactics_and_goals"].append({"tactic": 'Proof.', "goals": {"fg": fg_goals, "bg": bg_goals}})

            while not proof_env.success and not proof_env.failure:
                if proof_env.num_tactics_left <= 0:
                    break

                if len(proof_env.proof['steps']) == 0:
                    break

                next_step = proof_env.proof['steps'].pop(0)  # Removes the first element and returns it
                next_command = next_step['command'][0]  # Fetch the command from the tuple

                feedback = proof_env.step(next_command)

                # Collect goals after applying the tactic
                fg_goals = [goal['type'] for goal in feedback.get('fg_goals', [])]
                bg_goals = [goal['type'] for goal in feedback.get('bg_goals', [])]

                # Append the tactic and its resulting goals to the proof_dict
                proof_dict["tactics_and_goals"].append({"tactic": next_command, "goals": {"fg": fg_goals, "bg": bg_goals}})

            if proof_env.success:
                print(f"SUCEESFULLY PROVED {proof_env.proof['name']}")
            elif proof_env.failure:
                print(f"FAILED to prove {proof_env.proof['name']}")
            else:
                print(f"Proof for {proof_env.proof['name']} ended prematurely.")
            
            proof_dict["tactics_and_goals"].append({"tactic": 'Qed.', "goals": {"fg": [], "bg": []}})
            proofs_data.append(proof_dict)  # Append the proof's data to the list

    # Get import context path
    path_parts = filename.split('/')[1:]  # Split after data/
    proj_name = path_parts[0]
    formatted_path = '.'.join(path_parts).replace('.json', '.txt')
    import_context_path = os.path.join(import_context_base_path, proj_name, formatted_path)

    with open(import_context_path, 'r') as file:
        found_proof_statement = False
        for line in file:
            proof_file += line
            matched_proof_start_keyword = None  # Variable to store the matched keyword
            for keyword in proof_start_keywords:
                if keyword in line.replace(":", ""):
                    matched_proof_start_keyword = keyword  # Store the matched keyword
                    break  # Exit the loop once a match is found

            if matched_proof_start_keyword is not None:
                proof_name = line.split()[1] if matched_proof_start_keyword != 'Global Instance' else line.split()[2]
                # print("PROOF NAME: ", proof_name)
                proof_name = proof_name.replace(":", "")
                found_proof_statement = True
            if found_proof_statement and '.' in line:
                # Add in the lines
                proof_file += get_proof_and_goals(proof_name, proofs_data)
                # print("PROOF AND GOALS: ", get_proof_and_goals(proof_name, proofs_data))
                found_proof_statement = False

    return proof_file

def process_and_save_proofs(proof_files, output_dir):
    for filename in proof_files:
        proof_file = generate_proof_content(filename)
        output_filename = filename.split("data/")[1].replace("/", ".")
        output_path = os.path.join(output_dir, f"{output_filename}.txt")
        with open(output_path, 'w') as f:
            f.write(proof_file)
        print(f"Saved: {output_path}")

if __name__ == "__main__":
    output_base_path = "/app/.temp/"
    with open('proofs_split.json') as f:
        proofs_split = json.load(f)

    os.makedirs(os.path.join(output_base_path, 'train'), exist_ok=True)
    os.makedirs(os.path.join(output_base_path, 'test'), exist_ok=True)

    train_files = [file for file in proofs_split['proofs_train']]
    process_and_save_proofs(train_files, os.path.join(output_base_path, 'train'))

    test_files = [file for file in proofs_split['proofs_test']]
    process_and_save_proofs(test_files, os.path.join(output_base_path, 'test'))
