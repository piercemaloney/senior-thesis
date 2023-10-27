# 5 shot
generate_prompt = '''
You are assisting with a Coq proof. Given an input of the current proof, generate *two* ideas for ONLY the next line of the proof. Separate them with a comma.

Input:
Lemma add_comm : forall n m : nat, n + m = m + n.
Proof.

Output:
induction n., destruct n.

Input:
Lemma add_assoc : forall n m p : nat, n + (m + p) = (n + m) + p.

Output:
induction n., intros n m p.

Input:
Lemma add_comm : forall n m : nat, n + m = m + n.
Proof.
induction n as [| n' IHn'].

Output:
- (* Base case: n = 0 *), - simpl.

Input:
Lemma add_assoc : forall n m p : nat, n + (m + p) = (n + m) + p.
Proof.
intros n m p.
induction n as [| n' IHn'].

- (* Base case: n = 0 *)
simpl.
reflexivity.

- (* Inductive case: n = S n' *)

Output:
simpl., rewrite IHn'.

Input:
{input}

Output:
'''

vote_prompt = '''You are assisting with a Coq proof. Given an input of the current proof and two separate proposed steps, decide which one is best. Output the number of the best step.

Input:
Lemma add_comm : forall n m : nat, n + m = m + n.
Proof.

Proposed steps:
1) induction n.
2) destruct n.

Output:
1

Input:
Lemma add_assoc : forall n m p : nat, n + (m + p) = (n + m) + p.
Proof.
intros n m p.
induction n as [| n' IHn'].

- (* Base case: n = 0 *)
simpl.
reflexivity.

- (* Inductive case: n = S n' *)

Proposed steps:
2) reflexivity.
1) rewrite IHn'.

Output:
2

Input:
{input}

Proposed steps:
{proposed_steps}

Output:
'''

value_prompt = '''Evaluate if the proposed tactic is correct for the given proof state (sure/maybe/impossible).

Proposed tactic: _
Proof state: _

{input}
'''