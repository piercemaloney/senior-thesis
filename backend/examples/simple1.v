(* First, we require the standard library for natural numbers. *)
Require Import PeanoNat.

(* The theorem statement: for all natural numbers n, 0 + n equals n. *)
Theorem zero_plus_n_equals_n : forall n : nat, 
0 + n = n.
Proof.
  (* We start the proof by introducing variable n, which is a natural number. *)
  intro n.
  (* Now, we simplify the expression 0 + n to n, which is straightforward due to the definition of addition on natural numbers. *)
  simpl.
  (* The goal now matches the hypothesis, so we can conclude the proof. *)
  reflexivity.
Qed.
