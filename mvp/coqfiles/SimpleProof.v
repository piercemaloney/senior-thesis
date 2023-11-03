(* simple_proof.v *)

Lemma my_first_lemma : forall (P Q : Prop), P -> (P -> Q) -> Q.
Proof.
  intros P Q.
  intros H_P H_P_implies_Q.
  apply H_P_implies_Q.
  exact H_P.
Qed.
