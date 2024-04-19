# 5 shot
generate_prompt = '''
You are assisting with a Coq proof. Given an input of the current proof, generate *two* ideas for ONLY the next line of the proof.

Input:
Lemma add_comm : forall n m : nat, n + m = m + n.
Proof.

Output:
1) induction n.
2) destruct n.

Input:
Lemma add_assoc : forall n m p : nat, n + (m + p) = (n + m) + p.

Output:
1) induction n.
2) intros n m p.

Input:
Lemma add_comm : forall n m : nat, n + m = m + n.
Proof.
induction n as [| n' IHn'].

Output:
1) - (* Base case: n = 0 *)
2) - simpl.

Input:
Lemma modus_ponens : forall (P Q : Prop), P -> (P -> Q) -> Q.
Proof.
intros P Q.
intros H_P H_P_implies_Q.
apply H_P_implies_Q.
exact H_P.

Output:
1) Qed.
2) Defined.

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
1) simpl.
2) rewrite IHn'.

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