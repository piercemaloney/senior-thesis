import os
import re

from coqpyt.coq.structs import TermType
from coqpyt.coq.base_file import CoqFile
from coqpyt.coq.proof_file import ProofFile


# Open Proof file
# with ProofFile(os.path.join(os.getcwd(), "examples/simple1.v")) as proof_file:
#     # Enter proof
#     print(proof_file.exec(nsteps=1))
#     print("In proof:", proof_file.in_proof)
#     # Get current goals
#     print(proof_file.current_goals)

#     # Run remaining file
#     proof_file.run()
#     # Number of proofs in the file
#     print("Number of proofs:", len(proof_file.proofs))
#     print("Proof:", proof_file.proofs[0].text)

#     # Print steps of proof
#     for step in proof_file.proofs[0].steps:
#         print(step.text, end="")
#     print()

#     # NOTE: breaks here

#     # Get the context used in a step
#     print(proof_file.proofs[0].steps[6].context)
#     for i, step in enumerate(proof_file.proofs[0].steps):
#         print(f"Step {i}: {step.text}")
#     # Print the goals in a step
#     print(proof_file.proofs[0].steps[6].goals)

#     # Print number of terms in context
#     print("Number of terms:", len(proof_file.context.terms))
#     # Filter for Notations only
#     print(
#         "Number of notations:",
#         len(
#             list(
#                 filter(
#                     lambda term: term.type == TermType.NOTATION,
#                     proof_file.context.terms.values(),
#                 )
#             )
#         ),
#     )





# Send a command
proof = """
Lemma mult_is_zero : forall n m : nat, n * m = 0 <-> n = 0 \/ m = 0.
Proof.
  intros n m.
  split.
  - (* Forward direction: n * m = 0 implies n = 0 \/ m = 0 *)
    intros H. 
"""

def remove_ansi_escape_sequences(text):
    ansi_escape_pattern = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape_pattern.sub('', text)

def make_data_file(path: str = "examples/leavemult.v"):
    # execute each line of the file one by one and write a text file with the output
    with ProofFile(os.path.join(os.getcwd(), path)) as proof_file:
        with open(path+'.txt', "w") as f:
            # proof_file.run()
            for i in range(20):
                results = proof_file.exec(nsteps=1)
                if results: 
                    step = results[0]
                    goals = proof_file.current_goals.goals
                else:
                    # Handle the case when there are no more steps to execute
                    print("Done.")
                    break  #

                # print(goals.goals, type(goals), dir(goals))
                f.write(step.text)
                if goals:
                    clean_goals = remove_ansi_escape_sequences(str(goals))
                    f.write(f"\n{{{clean_goals}}}\n")


make_data_file()
