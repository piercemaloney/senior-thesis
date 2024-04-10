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
        file_data = json.load(open(filename))
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
        self.cost = 0.0  # The cost of this node in the tree

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def get_path(self):
        path = []
        node = self
        while node is not None:
            fg_goals = node.feedback.get('fg_goals', [])
            path[0:0] = ["(* Goal: %s *) " % goal['type'] for goal in fg_goals]
            # if not fg_goals:
                # bg_goals = node.feedback.get('bg_goals', [])
                # path[0:0] = ["(* Background goal: %s *) " % goal['type'] for goal in bg_goals]
            path.insert(0, node.tactic)
            node = node.parent
        return path

    def __repr__(self):
        if 'error' in self.feedback:
            return f"Tactic: {self.tactic}, Error: {self.feedback['error']}"
        else:
            fg_goal_types = [goal['type'] for goal in self.feedback.get('fg_goals', [])]
            return f"Tactic: {self.tactic}, FG Goal Types: {fg_goal_types}, Children: {len(self.children)}"


class ProofSolver:
    """ For every proof in an eval file, a ProofSolver is created. """
    def __init__(self, json_file_path, import_context_path, proof_env, initial_feedback, model="llemma-base"):
        self.json_file_path = json_file_path
        self.import_context_path = import_context_path
        self.proof_env = proof_env
        root = TreeNode("Proof.", initial_feedback)
        self.root = root
        self.current_node = root
        self.state = 'PROVING'
        self.generate_queries = 0
        self.evaluate_queries = 0
        self.model = model

        # self.tactic_generator = tactic_generator
        # self.state_scorer = state_scorer
        # self.tree_search = tree_search
        self.base_proof_text = self._generate_base_proof_txt(proof_env.proof['name'], root)

    def _generate_base_proof_txt(self, proof_name, root):
        proof_file_txt = ""
        with open(self.import_context_path, 'r') as file:
            found_proof_statement = False
            for line in file:
                proof_file_txt += line
                if proof_name in line:
                    found_proof_statement = True
                if found_proof_statement and '.' in line:
                    break
        return proof_file_txt

    def _return_to_root(self):
        while self.current_node.parent:
            self.proof_env.step("Undo.")
            self.current_node = self.current_node.parent
    
    def _update_costs_from_node(self, node):
        if node.children:
            node.cost = min(child.cost for child in node.children)
        if node.parent:
            self._update_costs_from_node(node.parent)

    def _call_model_generate(self, txt):
        if self.model == "llemma-base":
            server_url = "http://host.docker.internal:8000/generate_tactics_llemma_base"
            response = requests.post(server_url, json={"inputs": txt})
        elif self.model == "gpt-3":
            server_url = "http://host.docker.internal:8000/generate_tactics"
            response = requests.post(server_url, json={"inputs": txt})
        return response
    
    def get_proof_step_eval_txt(self) -> str:
        """ For each proof step, this generates the text before which the next tactic will be generated. """
        proof_file_txt = self.base_proof_text
        proof_file_txt += "\n".join(self.current_node.get_path()) + "\n"
        print('\nCurrently:', self.state, '\n', "\n".join(self.current_node.get_path()) + "\n")
        return proof_file_txt


    def generate_next_tactics(self):
        """ Generates the next tactic to be used in the proof. """
        self.choose_next_node()
        if self.state != 'PROVING':
            return self.state
        
        proof_step_eval_txt = self.get_proof_step_eval_txt()
        
        response = self._call_model_generate(proof_step_eval_txt)
        if response.status_code == 200:
            next_tactics = response.json().get("tactics")
            # next_tactics = ['induction l.']  # TODO testing

            if next_tactics:
                for next_tactic in next_tactics:
                    feedback = proof_env.step(next_tactic)
                    new_node = TreeNode(next_tactic, feedback)
                    new_node.cost = self.current_node.cost + 1
                    if "fg_goals" in feedback:
                        self.current_node.add_child(new_node)
                    if feedback["result"] == "SUCCESS":
                        print("Proof succeeded.")
                        self.state = 'SUCCESS'
                        return 'SUCCESS'
                    elif feedback["result"] == "GIVEN_UP":
                        new_node.cost = float('inf')
                        self.current_node.add_child(new_node)
                        print("Given up.")
                        break  # Exit the loop if proof given up
                    elif feedback["result"] == "ERROR":
                        new_node.cost = float('inf')
                        self.current_node.add_child(new_node)
                        print("An error occurred:", feedback.get("error", "Unknown Error"))
                        continue  # Automatically undoes the last tactic, so no need to undo
                    
                    # Print path to the current node
                    # raise Exception("Path to the new node:", new_node.get_path())
                    # Step back up to the current node
                    undo_feedback = proof_env.step("Undo.")

                self._update_costs_from_node(self.current_node)
                self._return_to_root()
                return 'PROVING'
            else:
                raise Exception("Bad response")

    def choose_next_node(self):
        """ Chooses the next node to be used in the proof and steps to it """
        if not self.root.children:
            return self.root
        
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
            
            if chosen_node is None:
                self.state = 'ERROR'
                return
            
            self.current_node = chosen_node
            self.proof_env.step(chosen_node.tactic)
        
        
        
        
        
        
        



if __name__ == "__main__":
    tactic_selector = None
    state_scorer = None  # Placeholder for a state scorer implementation
    tree_search = None  # Placeholder for a tree search implementation
    import_context_base_path = "/app/import_context/"

    f = "data/StructTact/Assoc.json"
    proj_name = f.split("/")[-2]
    with FileEnv(f, max_num_tactics=50, timeout=600) as file_env:
        for proof_env in file_env:
            # Get import context path
            path_parts = f.split('/')[1:]  # Split after data/
            formatted_path = '.'.join(path_parts).replace('.json', '.txt')
            import_context_path = os.path.join(import_context_base_path, proj_name, formatted_path)

            # Create proof env and tree
            initial_feedback = proof_env.init()

            # Create proof solver
            solver = ProofSolver(f, import_context_path, proof_env, initial_feedback)

            print('***********************')
            print(proof_env.proof['name'])
            print('***********************')
            
            while solver.state == 'PROVING':
                solver.generate_next_tactics()
                if proof_env.success:
                    print("Proof succeeded.")
                    break
                elif proof_env.failure:
                    print("Proof failed.")
                    break
                if proof_env.num_tactics_left <= 0:
                    print("Maximum number of tactics reached.")
                    break
            if solver.state == 'SUCCESS':
                print("Proof succeeded.")
            elif solver.state == 'ERROR':
                print("Proof failed.")
                
                
            


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
