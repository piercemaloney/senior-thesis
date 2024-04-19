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



INSTRUCT_ZERO_TO_ONE_PROMPT = """...
{base_proof_context}
-----
Above is the context for a Coq proof. You are an evaluation model, and you score the proof from 0 to 1, where closer to 0 means it's far from the end of the proof, and closer to 1 means it is on the right track and close to being proven. For example, if the proof seems to not be making progress, give it a low score. Here is the current state of the proof:
---
{proof_statement}
{path}
---
Output, followed by a period and nothing else, the score of this proof from 0 to 1.
"""
# TODO


PERCENTAGE_PROMPT = """
-----
Input: (* Goal: forall (_ : forall _ : forall _ : A, B, C) (_ : B), C *)

Output:
The percentage chance that this proof is possible is 95%.

Input: (* Goal: Rel_of U D bot x *)
(* Goal: forall (x1 x2 : U) (_ : Included U (Couple U x1 x2) (Approximants U D x)), @ex U (fun x3 : U => and (In U (Approximants U D x) x3) (Upper_Bound U D (Couple U x1 x2) x3)) *)

Output:
The percentage chance that this proof is possible is 50%.

Input: (* Goal: forall n m p : nat, @eq nat (Plus n (Plus m p)) (Plus (Plus n m) p) *)

Output:
The percentage chance that this proof is possible is 80%.

Input: {goals}

Output:
With the context from above, the percentage chance that this proof is possible is """


EVAL_SELECTION_PROMPT = """...
{base_proof_context}
-----
Above is the context for a Coq proof. You are an evaluation model, and you select which option is closest to completing the proof. Here are the options:
---
{choices}
Output, followed by a period and nothing else, the number of the option you select. 
"""

GENERATION_INSTRUCT_PROMPT = """...
{proof_file_txt}
-----
Above is the context for a Coq proof. You are a model that generates the next Coq tactic to be used. It is your job to generate two ideas for the next tactic to be used, separated by a comma. An example output is:
intros; clear T.., apply eq_refl.

Output, as discussed, two ideas for the next tactic to use, separated by a comma.
"""



class ProofEnv:
    """
    the interactive environment for proving a theorem
    should be created by FileEnv
    """

    def __init__(self, proof, serapi, max_num_tactics, timeout):
        """
        proof - the data structure for a proof in CoqGym
        serapi - the SerAPI at the beginning of the proof
        max_num_tactics - the maxium number of interactions for proving a theorem
        timeout - the maxium amount of time (in seconds) for each theorem 
        """
        self.proof = proof
        self.serapi = serapi
        self.num_tactics_left = max_num_tactics
        self.timeout = timeout
        self.success = False
        self.failure = False

    def init(self):
        "return the initial goals and the global environment of the theorem"
        fg_goals, bg_goals, shelved_goals, given_up_goals = self.serapi.query_goals()
        assert shelved_goals + given_up_goals == []
        self.start_time = time()
        return self.feedback(
            "PROVING",
            env=self.proof["env"],
            fg_goals=fg_goals,
            bg_goals=bg_goals,
            shelved_goals=shelved_goals,
            given_up_goals=given_up_goals,
        )

    def step(self, command):
        """
        perform a single interaction
        the agent provides a command and get feedback from Coq
        valid commands include:
            tactics
            Admitted - to give up the proof
            Undo - to backtrack one step
            other valid Coq commands
        """
        if self.success:
            return self.feedback("ALREADY_SUCCEEDED")
        if self.failure:
            return self.feedback("ALREADY_FAILED")
        time_left = self.timeout - (time() - self.start_time)
        print("%d: %s: %.02f" % (self.num_tactics_left, command, time_left))
        if time_left <= 0:
            return self.feedback("MAX_TIME_REACHED")

        self.serapi.push()  # save the state before executing the command
        try:
            ast = sexpdata.dumps(self.serapi.query_ast(command))
            if "VernacExtend" in ast:  # is a tactic
                if self.num_tactics_left <= 0:
                    self.serapi.pop()
                    return self.feedback("MAX_NUM_TACTICS_REACHED")
                self.num_tactics_left -= 1
                command = "timeout %d (%s)." % (time_left, command[:-1])
            responses, _ = self.serapi.execute(command)
            states_cnt = self.serapi.pull()  # delete the saved state if no error
        except CoqExn as ex:
            self.serapi.pop()  # restore the state
            return self.feedback("ERROR", error=ex)
        except CoqTimeout as ex:
            self.serapi.shutdown()
            return self.feedback("ERROR", error=ex)

        if "(VernacEndProof Admitted)" in ast:
            self.failure = True
            return self.feedback("GIVEN_UP")

        try:
            (
                fg_goals,
                bg_goals,
                shelved_goals,
                given_up_goals,
            ) = self.serapi.query_goals()
            time_left = self.timeout - (time() - self.start_time)
            if time_left < 0:
                return self.feedback("MAX_TIME_REACHED")
        except CoqTimeout as ex:
            self.serapi.shutdown()
            return self.feedback("ERROR", error=ex)

        if fg_goals + bg_goals + shelved_goals + given_up_goals == []:  # no goals left
            self.success = True
            return self.feedback("SUCCESS")
        elif shelved_goals + given_up_goals != []:
            self.serapi.pop_n(states_cnt)
            return self.feedback("ERROR", error=(shelved_goals, given_up_goals))
        else:
            return self.feedback(
                "PROVING",
                fg_goals=fg_goals,
                bg_goals=bg_goals,
                shelved_goals=shelved_goals,
                given_up_goals=given_up_goals,
            )

    def feedback(self, result, **kwargs):
        obs = {
            "result": result,
            "num_tactics_left": self.num_tactics_left,
            "time_left": self.timeout - (time() - self.start_time),
        }
        for k, v in kwargs.items():
            obs[k] = v
        return obs


class FileEnv:
    """
    a generator of the theorems in a Coq file
    the agent iterate through them and interact with each theorem sequentially
    """

    def __init__(
        self, filename, max_num_tactics, timeout, with_hammer=None, hammer_timeout=None
    ):
        """
        filename - the json file in CoqGym
        max_num_tactics - the maxium number of interactions for proving a theorem
        timeout - the maxium amount of time (in seconds) for each theorem
        """
        
        file_data = json.load(open(str(filename)))
        self.vernac_cmds = [cmd[:2] for cmd in file_data["vernac_cmds"]]
        self.proofs = file_data["proofs"]
        self.max_num_tactics = max_num_tactics
        self.timeout = timeout
        self.with_hammer = with_hammer
        self.hammer_timeout = hammer_timeout
        self.serapi = self.initialize_serapi()

    def initialize_serapi(self):
        serapi = SerAPI(timeout=1200)
        if self.with_hammer is not None:
            atp_limit = 29 * self.hammer_timeout // 60
            reconstr_limit = 28 * self.hammer_timeout // 60
            crush_limit = 3 * self.hammer_timeout // 60
            serapi.execute(
                "From Hammer Require Import Hammer. Set Hammer ATPLimit %d. Set Hammer ReconstrLimit %d. Set Hammer CrushLimit %d."
                % (atp_limit, reconstr_limit, crush_limit)
            )
            if self.with_hammer == "Z3":
                serapi.execute(
                    "Unset Hammer Vampire. Unset Hammer Eprover. Unset Hammer CVC4."
                )
            elif self.with_hammer == "Vampire":
                serapi.execute(
                    "Unset Hammer Z3. Unset Hammer Eprover. Unset Hammer CVC4."
                )
            elif self.with_hammer == "Eprover":
                serapi.execute(
                    "Unset Hammer Z3. Unset Hammer Vampire. Unset Hammer CVC4."
                )
            elif self.with_hammer == "CVC4":
                serapi.execute(
                    "Unset Hammer Z3. Unset Hammer Vampire. Unset Hammer Eprover."
                )
            else:
                assert self.with_hammer == "All"
        return serapi

    def __iter__(self):
        self.cmd_idx = 0
        self.next_proof_idx = 0
        self.env = {"constants": [], "inductives": []}
        return self

    def __next__(self):
        if self.next_proof_idx >= len(self.proofs):  # no more theorem
            raise StopIteration

        next_proof = self.proofs[self.next_proof_idx]
        self.env = update_env(self.env, next_proof["env_delta"])
        del next_proof["env_delta"]
        next_proof["env"] = self.env

        if self.serapi.dead:
            self.serapi = self.initialize_serapi()
            self.cmd_idx = 0
        elif self.next_proof_idx > 0:  # rollback to the start of the current proof
            self.serapi.pop()

        if (
            self.next_proof_idx > 0 and self.next_proof_idx % 30 == 0
        ):  # renew the SerAPI to prevent stack overflow
            self.serapi.clean()
            self.serapi = self.initialize_serapi()
            self.cmd_idx = 0

        while self.cmd_idx <= next_proof["line_nb"]:
            cmd, _ = self.vernac_cmds[self.cmd_idx]
            self.serapi.execute(cmd)
            self.cmd_idx += 1

        self.serapi.push()

        self.next_proof_idx += 1
        return ProofEnv(next_proof, self.serapi, self.max_num_tactics, self.timeout)

    def __len__(self):
        return len(self.proofs)

    def test(self):
        assert self.cmd_idx is None
        self.serapi.push()
        for cmd, _ in self.vernac_cmds:
            self.serapi.execute(cmd)
        self.serapi.pop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.serapi.clean()


# if __name__ == "__main__":
#     f = "data/StructTact/Assoc.json"
#     print(f)
#     with FileEnv(f, max_num_tactics=100, timeout=600) as file_env:
#         for proof_env in file_env:
#             print(proof_env.proof["name"])
#             proof_env.init()
#             print(proof_env.step("Admitted."))


class TreeNode:
    def __init__(self, tactic: str, feedback=None):
        self.tactic = tactic
        self.feedback = feedback
        self.children = []
        self.parent = None
        self.eval_score = 0.0  # The score, btwn 0 and 1, assigned to this node by eval model
        self.cost = 0.0  # The cost of reaching this node in the tree
        self.f_score = 0.0  # For A* search
        self.error = None

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def get_tactic_path(self):
        path = []
        node = self
        while node is not None:
            path.insert(0, node.tactic)
            node = node.parent
        return path

    def get_path(self, only_include_last_goals=True):
        path = []
        node = self
        including_goals = True  # flag
        while node is not None:
            if including_goals:
                fg_goals = node.feedback.get('fg_goals', [])
                path[0:0] = ["(* Goal: %s *) " % goal['type'] for goal in reversed(fg_goals)]
                if not fg_goals:
                    bg_goals = node.feedback.get('bg_goals', [])
                    path[0:0] = ["(* Background goal: %s *) " % goal['type'] for goal in bg_goals]
            if only_include_last_goals:
                including_goals = False
            path.insert(0, node.tactic)
            node = node.parent
        return path

    def __lt__(self, other):
        return self.f_score < other.f_score

    def __repr__(self):
        if 'error' in self.feedback:
            return f"Tactic: {self.tactic}, Error: {self.feedback['error']}"
        else:
            fg_goal_types = [goal['type'] for goal in self.feedback.get('fg_goals', [])]
            return f"Tactic: {self.tactic}, FG Goal Types: {fg_goal_types}, Children: {len(self.children)}"


class ProofSolver:
    """ For every proof in an eval file, a ProofSolver is created. """
    def __init__(self, json_file_path, query_context_path, proof_env, initial_feedback, model="llemma-base", search_strategy="A_STAR"):
        self.json_file_path = json_file_path
        self.query_context_path = query_context_path
        self.proof_env = proof_env
        root = TreeNode("Proof.", initial_feedback)
        self.root = root
        self.current_node = root
        self.state = 'PROVING'
        self.num_generate_queries = 0
        self.num_evaluate_queries = 0
        self.model = model
        self.eval_model = "gpt-4"
        self.search_strategy = search_strategy
        if search_strategy == "A_STAR":
            self.eval_strategy = "ZERO_TO_ONE_INSTRUCT"
        elif search_strategy == "GREEDY":
            self.eval_strategy = "SELECTION_INSTRUCT"
        self.open_set = queue.PriorityQueue()
        self.successful_tactic_path = None
        self.new_tactics_tried = 0
        # COUNT STEPS
        # self.open_set.put((self.root.f_score, self.root))

        # self.tactic_generator = tactic_generator
        # self.state_scorer = state_scorer
        # self.tree_search = tree_search
        self.base_proof_context, self.proof_statement = self._generate_base_proof_txt(proof_env.proof['name'], root)

    def _generate_base_proof_txt(self, proof_name, root):
        base_proof_context = ""
        proof_statement = ""
        with open(self.query_context_path, 'r') as file:
            found_proof_statement = False
            for line in file:
                if proof_name in line:
                    found_proof_statement = True
                if found_proof_statement:
                    if re.search(r'\.\s|\.$', line):
                        split_line = re.split(r'(\.\s|\.$)', line, 1)
                        proof_statement += split_line[0] + '.\n'
                        break
                    else:
                        proof_statement += line
                else:
                    base_proof_context += line
        # First, replace exactly two '\n's with one '\n'
        base_proof_context = re.sub(r'\n\n', '\n', base_proof_context)
        # Then, replace two or more '\n's with two '\n's
        base_proof_context = re.sub(r'\n{2,}', '\n\n', base_proof_context)
        return base_proof_context, proof_statement

    def _return_to_root(self):
        while self.current_node.parent:
            self.proof_env.step("Undo.")
            self.current_node = self.current_node.parent
    
    def _update_scores_from_node(self, node):
        if self.search_strategy == "A_STAR":
            step_cost = 0.2
            node.cost = node.parent.cost + step_cost if node.parent else 0
            if node.eval_score == float('-inf'):
                node.f_score = float('inf')  # Impossible path
            else:
                node.f_score = node.cost + (1-node.eval_score)

    def _call_model_generate(self, txt):
        self.num_generate_queries += 1
        if self.model == "llemma-base":
            server_url = "http://host.docker.internal:8000/generate_tactics_llemma_base"
            response = requests.post(server_url, json={"inputs": txt})
        elif self.model == "llemma-v3-finetuned":
            server_url = "http://host.docker.internal:8000/generate_tactics_llemma_v3_finetuned"
            response = requests.post(server_url, json={"inputs": txt})
        elif self.model == "llemma-v4-finetuned":
            server_url = "http://host.docker.internal:8000/generate_tactics_llemma_v4_finetuned"
            response = requests.post(server_url, json={"inputs": txt})
        elif self.model == "llemma-v5-finetuned":
            server_url = "http://host.docker.internal:8000/generate_tactics_llemma_v5_finetuned"
            response = requests.post(server_url, json={"inputs": txt})
        elif self.model == "gpt-4":
            server_url = "http://host.docker.internal:8000/generate_tactics_gpt4"
            response = requests.post(server_url, json={"inputs": txt})
        elif self.model == "gpt-3":
            server_url = "http://host.docker.internal:8000/generate_tactics"
            response = requests.post(server_url, json={"inputs": txt})
        return response

    def _call_model_eval(self, txt):
        self.num_evaluate_queries += 1
        if self.eval_model == "llemma-base":
            server_url = "http://host.docker.internal:8000/eval_llemma_base"
            response = requests.post(server_url, json={"inputs": txt})
        elif self.eval_model == "gpt-3":
            server_url = "http://host.docker.internal:8000/eval"
            response = requests.post(server_url, json={"inputs": txt})
        elif self.eval_model == "gpt-4":
            server_url = "http://host.docker.internal:8000/eval_gpt4"
            response = requests.post(server_url, json={"inputs": txt})
        return response

    def _get_all_leaf_nodes(self):
        """ Returns all the leaf nodes in the tree. """
        pass

    def get_proof_step_generate_txt(self) -> str:
        """ For each proof step, this generates the text before which the next tactic will be generated. """
        proof_file_txt = self.base_proof_context
        proof_file_txt += self.proof_statement
        path = "\n".join(self.current_node.get_path())
        proof_file_txt += path
        for child in self.current_node.children:
            if child.error:
                proof_file_txt += f"\n(* Note: cannot use {child.tactic}, failed with error. *)\n"
        proof_file_txt +=  "\n"
        # print('\nCurrently:', self.state, '\n', path)
        # Remove all indentations
        proof_file_txt = re.sub(r'^[ \t]+', '', proof_file_txt, flags=re.MULTILINE)
        if self.model == "gpt-4":
            return GENERATION_INSTRUCT_PROMPT.format(proof_file_txt=proof_file_txt[-2500:])
        return proof_file_txt
    
    def get_proof_step_eval_txt(self, node = None) -> str:
        if not node:
            node = self.current_node
        if self.eval_strategy == "PERCENTAGE":
            proof_file_txt = self.base_proof_context
            proof_file_txt += PERCENTAGE_PROMPT.format(goals='\n'.join(["(* Goal: %s *) " % goal['type'] for goal in reversed(node.feedback.get('fg_goals', []))]))
            # path = "\n".join(self.current_node.get_path()) + "\n"
            # proof_file_txt += path
            return proof_file_txt
        elif self.eval_strategy == "SELECTION_INSTRUCT":
            choice_format = "\n#{option_number}:\n{path}\n---"
            choices_formatted = ""
            for index, (_, node) in enumerate(self.open_set.queue, start=1):
                node_path = "\n".join(node.get_path(only_include_last_goals=True))
                choices_formatted += choice_format.format(option_number=index, path=node_path)
            proof_file_txt = EVAL_SELECTION_PROMPT.format(base_proof_context=self.base_proof_context[-1000:], proof_statement=self.proof_statement, choices=choices_formatted)
            # Remove all indentations
            proof_file_txt = re.sub(r'^[ \t]+', '', proof_file_txt, flags=re.MULTILINE)
            return proof_file_txt
        elif self.eval_strategy == "ZERO_TO_ONE_INSTRUCT":
            proof_file_txt = INSTRUCT_ZERO_TO_ONE_PROMPT.format(base_proof_context=self.base_proof_context[-1000:], proof_statement=self.proof_statement, path='\n'.join(node.get_path(only_include_last_goals=False)))
            # Remove all indentations
            proof_file_txt = re.sub(r'^[ \t]+', '', proof_file_txt, flags=re.MULTILINE)
            return proof_file_txt


    def generate_next_tactics(self):
        """ Generates the next tactic to be used in the proof. """
        if not self.choose_next_node():
            self.state = 'FAILURE'
            return self.state
        if self.state != 'PROVING':
            return self.state
        
        proof_step_generate_txt = self.get_proof_step_generate_txt()
        # print("GENERATING: ", proof_step_generate_txt[-300:])
        # print("^^^")
        
        response = self._call_model_generate(proof_step_generate_txt)
        if response.status_code == 200:
            next_tactics = response.json().get("tactics")

            if next_tactics:
                for next_tactic in next_tactics:
                    feedback = proof_env.step(next_tactic)
                    self.new_tactics_tried += 1
                    new_node = TreeNode(next_tactic, feedback)
                    self.current_node.add_child(new_node)
                    # new_node.cost = self.current_node.cost
                    if feedback["result"] == "SUCCESS":
                        print("Proof succeeded.")
                        new_node.eval_score = float('inf')
                        self.successful_tactic_path = new_node.get_tactic_path()
                        self.state = 'SUCCESS'
                        return 'SUCCESS'
                    elif feedback["result"] == "GIVEN_UP":
                        new_node.eval_score = float('-inf')
                        # new_node.cost = float('inf')
                        print("Given up.")
                        break  # Exit the loop if proof given up
                    elif feedback["result"] == "ERROR":
                        new_node.eval_score = float('-inf')
                        # new_node.cost = float('inf')
                        new_node.error = feedback.get("error", "Unknown Error")
                        print("An error occurred:", feedback.get("error", "Unknown Error"))
                        continue  # Automatically undoes the last tactic, so no need to undo
                    
                    if self.eval_strategy != "SELECTION_INSTRUCT":
                        # Evaluate response
                        eval_response = self._call_model_eval(self.get_proof_step_eval_txt(new_node))
                        if eval_response.status_code == 200:
                            new_node.eval_score = float(eval_response.json().get("eval"))
                        self._update_scores_from_node(new_node)
                    # if self.current_node.tactic == new_node.tactic:
                    #     print("Same tactic")
                    #     # new_node.cost = float('inf')
                    #     print("Current:")
                    #     print([goal['type'] for goal in self.current_node.feedback.get('fg_goals', [])])
                    #     print("New:")
                    #     print([goal['type'] for goal in new_node.feedback.get('fg_goals', [])])
                    #     print('---')
                    #     current_goals = [goal['type'] for goal in self.current_node.feedback.get('fg_goals', [])]
                    #     new_goals = [goal['type'] for goal in new_node.feedback.get('fg_goals', [])]
                    #     if current_goals == new_goals[:len(current_goals)]:
                    #         # No progress
                    #         new_node.cost = float('inf')
                    # print(new_node.get_path())
                    if self.search_strategy == "A_STAR":
                        self.open_set.put((new_node.f_score, new_node))
                    else:
                        # new_node.eval_score will be 0 unless changed
                        self.open_set.put((new_node.eval_score, new_node))
                    
                    # Step back up to the current node
                    
                    undo_feedback = proof_env.step("Undo.")

                self._return_to_root()
                return 'PROVING'
            else:
                raise Exception("Bad response")

    def _step_to_node(self, node, count_tactics=False):
        self._return_to_root()
        tactics = node.get_tactic_path()
        for tactic in tactics:
            self.proof_env.step(tactic)

    def choose_next_node(self):
        """ Chooses the next node to be used in the proof and steps to it """
        if not self.root.children:
            self.current_node = self.root
            return True
        

        if self.search_strategy == "A_STAR":
            if self.open_set.empty():
                return False  # No path to goal
            _, next_node = self.open_set.get()
            self._step_to_node(next_node)
            self.current_node = next_node
            return True
        if self.eval_strategy == "SELECTION_INSTRUCT":
            if self.open_set.empty():
                return False # No path to goal
            eval_response = self._call_model_eval(self.get_proof_step_eval_txt(self.current_node))
            if eval_response.status_code == 200:
                # Get the node choice # from the response
                node_choice = int(re.sub("[^0-9]", "", eval_response.json().get("eval")))
                chosen_node = None
                new_queue = queue.PriorityQueue()
                for index, (_, node) in enumerate(list(self.open_set.queue), start=1):
                    if index == node_choice:
                        chosen_node = node
                        continue  # Skip adding this node back to the queue
                    new_queue.put((node.f_score, node))  # Re-add other nodes back to the queue
                self.open_set = new_queue  # Replace the old queue with the new one
                if chosen_node is not None:
                    self._step_to_node(chosen_node)
                    self.current_node = chosen_node
            return True

            
        
        # Traverse through the tree, choosing each subsequent child with the smallest cost until that node has no children
        # Also steps self.proof_env to the chosen node
        while self.current_node.children:
            for child in self.current_node.children:
                print(f"Tactic: {child.tactic}, Cost: {child.cost}")
            
            min_cost = float('inf')
            chosen_node = None
            for child in self.current_node.children:
                if child.cost < min_cost:
                    min_cost = child.cost
                    chosen_node = child
            
            if chosen_node is None or chosen_node.cost > self.current_node.cost:
                return False
            
            self.current_node = chosen_node
            self.proof_env.step(chosen_node.tactic)
        return True
    

    def to_json(self):
        """Serializes the ProofSolver object and its tree to a JSON string."""

        def node_to_dict(node):
            """Recursively converts a TreeNode into a dictionary."""
            return {
                'tactic': node.tactic,
                'fg_goals': [goal['type'] for goal in node.feedback.get('fg_goals', [])][::-1],
                'bg_goals': [goal['type'] for goal in node.feedback.get('bg_goals', [])][::-1],
                'eval_score': node.eval_score,
                'cost': node.cost,
                'f_score': node.f_score,
                # 'error': node.error,
                'children': [node_to_dict(child) for child in node.children]
            }

        # Serialize the tree starting from the root
        tree_dict = node_to_dict(self.root)

        # Serialize the ProofSolver attributes
        solver_dict = {
            'json_file_path': str(self.json_file_path),
            'query_context_path': str(self.query_context_path),
            'state': self.state,
            'model': self.model,
            'eval_model': self.eval_model,
            'eval_strategy': self.eval_strategy,
            'search_strategy': self.search_strategy,
            'num_generate_queries': self.num_generate_queries,
            'num_evaluate_queries': self.num_evaluate_queries,
            'tree': tree_dict,
            'successful_tactic_path': self.successful_tactic_path
        }

        # Convert the entire structure to a JSON string
        return json.dumps(solver_dict, indent=4)
        
        
        
        
        
        



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a Coq file.')
    parser.add_argument('filepath',
                        type=str,
                        default='data/StructTact/Assoc.json',
                        help='The path to the Coq file to process. Defaults to data/StructTact/Assoc.json')
    parser.add_argument('--output_dir',
                        type=str,
                        default='/app/results/',
                        help='The path where the output JSON will be saved. Defaults to app/results/')
    parser.add_argument('--search_strategy',
                        type=str,
                        default='A_STAR',
                        choices=['GREEDY', 'A_STAR'],
                        help='The search strategy to use. Defaults to GREEDY.')
    parser.add_argument('--model',
                        type=str,
                        default='llemma-v4-finetuned',
                        choices=['llemma-base', 'llemma-v3-finetuned', 'llemma-v4-finetuned', 'llemma-v5-finetuned', 'gpt-4', 'gpt-3'],
                        help='The model to use for generating tactics. Defaults to llemma-base.')
    parser.add_argument('--query_context_base_path',
                        type=str,
                        default='/app/query_data/',
                        help='The base path for query context data. Defaults to /app/query_data/')
    

    args = parser.parse_args()

    search_strategy = args.search_strategy
    model = args.model
    query_context_base_path = args.query_context_base_path
    output_dir = args.output_dir
    # state_scorer = None  # Placeholder for a state scorer implementation

    max_num_new_tactics = 24


    proverbot_benchmark_dict = {'data/CompCert/x86/SelectOpproof.json': ['eval_addrstack', 'eval_mulhs', 'eval_mulhu', 'eval_negf', 'eval_absf', 'eval_negfs', 'eval_absfs', 'eval_compf', 'eval_compfs', 'eval_singleoffloat', 'eval_floatofsingle', 'eval_intoffloat', 'eval_intofsingle'], 'data/CompCert/backend/Locations.json': ['typesize_pos', 'typealign_pos', 'typealign_typesize', 'same_not_diff', 'Loc.diff_sym', 'Loc.disjoint_cons_left', 'IndexedTyp.index_inj', 'IndexedSlot.index_inj', 'OrderedLoc.eq_sym', 'OrderedLoc.eq_trans', 'OrderedLoc.lt_trans'], 'data/CompCert/cfrontend/Cop.json': ['ArithConv.typeconv_integer_promotion']}
    BENCHMARK = True

    f = args.filepath
    if BENCHMARK:
        output_dir = '/app/results/llemma_v4_a_star_benchmark'
    # f = "data/demos/Demo_tauto.json"
    proj_name = f.split("/")[1]
    
    num_proof = 0
    finished_all_proof_envs = False

    # Get query context path
    path_parts = f.split('/')[1:]  # Split after data/
    formatted_path = '.'.join(path_parts).replace('.json', '.txt')
    query_context_base_path = os.path.join(query_context_base_path, proj_name, formatted_path)


    while not finished_all_proof_envs:
        with FileEnv(f, max_num_tactics=150, timeout=600) as file_env:
            total_proofs = len(file_env)
            for i, proof_env in enumerate(file_env):
                if i < num_proof:  # Skip the first i proof_envs
                    continue
                if BENCHMARK:
                    if proof_env.proof['name'] not in proverbot_benchmark_dict[f]:
                        print(f"Skipping {proof_env.proof['name']} because it's not in the benchmark dict.")
                        continue

                # Check if the proof has already been solved
                proof_name = proof_env.proof['name']
                output_path = os.path.join(output_dir, f"{formatted_path}.{proof_name}.json")
                if os.path.exists(output_path):
                    print(f"Skipping {output_path} because it has already been solved.")
                    break

                # Create proof env and tree
                initial_feedback = proof_env.init()

                # Create proof solver
                solver = ProofSolver(f, query_context_base_path, proof_env, initial_feedback, search_strategy=search_strategy, model=model)


                print('***********************')
                print(proof_name)
                print('***********************')
                
                # Try to solve the proof
                try:
                    while solver.state == 'PROVING':
                        solver.generate_next_tactics()
                        if proof_env.success:
                            print("Proof succeeded.")
                            solver.state = 'SUCCESS'
                            break
                        elif proof_env.failure:
                            print("Proof failed.")
                            solver.state = 'FAILURE'
                            break
                        if solver.new_tactics_tried >= max_num_new_tactics:
                            print("Maximum number of tactics reached.")
                            solver.state = 'TIMEOUT'
                            break
                    if solver.state == 'SUCCESS':
                        print("Proof succeeded.")
                    elif solver.state == 'ERROR':
                        print("Proof failed.")
                except Exception as e:
                    print(f"An error occurred: {e}")
                
                # Save the proof to the output directory
                with open(output_path, "w") as temp_file:
                    temp_file.write(solver.to_json())
            num_proof += 1
            print(f'Finished {num_proof} out of {total_proofs} proofs.')
        # Check if all proofs have been processed
        if num_proof >= total_proofs:
            finished_all_proof_envs = True
                
                
            


# tactics = ["Proof.", "induction l; intros; simpl; repeat (break_match; simpl); subst; congruence."]

# if __name__ == "__main__":
#     f = "data/StructTact/Assoc.json"
#     print(f)
#     with FileEnv(f, max_num_tactics=20, timeout=600) as file_env:
#         for proof_env in file_env:
#             print(proof_env.proof['name'])
#             initial_feedback = proof_env.init()
            
#             root = TreeNode("Proof.", initial_feedback)
#             current_node = root
#             for goal in initial_feedback['fg_goals']:
#                 print("Goal Type:", goal["type"])
#             while not proof_env.success and not proof_env.failure:
#                 # Server expects a JSON with the current state and returns a tactic
#                 server_url = "http://host.docker.internal:8000/generate_tactics"
#                 current_state = {"fg_goals": [goal['type'] for goal in initial_feedback['fg_goals']]}
#                 response = requests.post(server_url, json=current_state)
#                 if response.status_code == 200:
#                     next_tactics = response.json().get("tactics")
#                     if next_tactics:
#                         for next_tactic in next_tactics:
#                             feedback = proof_env.step(next_tactic)
#                             new_node = TreeNode(next_tactic, feedback)
#                             current_node.add_child(new_node)
#                             if "fg_goals" in feedback:
#                                 print("Foreground Goals:")
#                                 for goal in feedback["fg_goals"]:
#                                     print("Goal Type:", goal["type"])
#                             if feedback["result"] == "SUCCESS":
#                                 print("Proof succeeded.")
#                                 break  # Exit the loop if proof succeeded
#                             elif feedback["result"] == "GIVEN_UP":
#                                 print("Proof given up.")
#                                 break  # Exit the loop if proof given up
#                             elif feedback["result"] == "ERROR":
#                                 print("An error occurred:", feedback.get("error", "Unknown Error"))
#                                 continue  # Automatically undoes the last tactic, TODO Confirm this
                            
#                             # Step back up to the current node
#                             undo_feedback = proof_env.step("Undo.")
                        
#                         raise Exception("\n".join(current_node.children[0].get_path()))
                                
#                     else:
#                         print("Server did not return a tactic.")
#                         break
#                 else:
#                     print(f"Failed to get tactic from server. Status code: {response.status_code}")
#                     break


