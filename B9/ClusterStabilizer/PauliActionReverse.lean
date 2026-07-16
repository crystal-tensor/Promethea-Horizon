import B9.ClusterStabilizer.PauliActionTermCommutation

namespace B9

open ClusterStabilizer

def PauliTerm.reverse {n : Nat} (term : PauliTerm n) : PauliTerm n :=
  { factors := term.factors.reverse }

theorem basis_action_compose_identity_left
    {n : Nat} (action : BasisAction n) :
    (BasisAction.identity action.state).compose action = action := by
  cases action with
  | mk phase state =>
      cases phase <;> rfl

theorem phase_mul_plus (phase : Phase) : phase.mul .plus = phase := by
  cases phase <;> rfl

theorem pauli_factor_act_self_inverse
    {n : Nat} (factor : PauliFactor n) (state : BasisState n) :
    (factor.act state).compose
        (factor.act (factor.act state).state) =
      BasisAction.identity state := by
  cases factor with
  | mk site axis =>
      cases axis with
      | x =>
          have hFlip : flipAt (flipAt state site) site = state := by
            funext j
            by_cases h : j = site
            · subst j
              simp [flipAt]
            · simp [flipAt, h]
          simp [PauliFactor.act, BasisAction.compose, BasisAction.identity,
            Phase.mul, hFlip]
      | z =>
          cases hBit : state site <;>
            simp [PauliFactor.act, BasisAction.compose, BasisAction.identity,
              Phase.ofBit, Phase.mul, hBit]

theorem pauli_term_basis_action_reverse_compose
    {n : Nat} (term : PauliTerm n) (state : BasisState n) :
    (term.basisAction state).compose
        (term.reverse.basisAction (term.basisAction state).state) =
      BasisAction.identity state := by
  cases term with
  | mk factors =>
      induction factors generalizing state with
      | nil =>
          simp [PauliTerm.basisAction, PauliTerm.reverse,
            BasisAction.compose, BasisAction.identity, Phase.mul]
      | cons head tail ih =>
          have hTail :
              ((PauliTerm.mk tail).basisAction (head.act state).state).compose
                  ((PauliTerm.mk tail.reverse).basisAction
                    ((PauliTerm.mk tail).basisAction (head.act state).state).state) =
                BasisAction.identity (head.act state).state := by
            simpa [PauliTerm.reverse] using ih (state := (head.act state).state)
          have hTailState :
              ((PauliTerm.mk tail.reverse).basisAction
                ((PauliTerm.mk tail).basisAction (head.act state).state).state).state =
                (head.act state).state := by
            simpa [BasisAction.compose] using congrArg BasisAction.state hTail
          rw [pauli_term_basis_action_cons_compose]
          simp only [PauliTerm.reverse, List.reverse_cons]
          calc
            ((head.act state).compose
                ((PauliTerm.mk tail).basisAction (head.act state).state)).compose
                ((PauliTerm.mk (tail.reverse ++ [head])).basisAction
                  ((head.act state).compose
                    ((PauliTerm.mk tail).basisAction (head.act state).state)).state) =
              (head.act state).compose
                (((PauliTerm.mk tail).basisAction (head.act state).state).compose
                  ((PauliTerm.mk (tail.reverse ++ [head])).basisAction
                    ((head.act state).compose
                      ((PauliTerm.mk tail).basisAction (head.act state).state)).state)) := by
              rw [basis_action_compose_assoc]
            _ = (head.act state).compose
                ((BasisAction.identity (head.act state).state).compose
                  (head.act (BasisAction.identity (head.act state).state).state)) := by
              rw [pauli_term_basis_action_append]
              nth_rewrite 2 [← basis_action_compose_assoc]
              have hComposedState :
                  ((head.act state).compose
                    ((PauliTerm.mk tail).basisAction (head.act state).state)).state =
                    ((PauliTerm.mk tail).basisAction (head.act state).state).state := rfl
              rw [hComposedState]
              rw [hTailState]
              rw [hTail]
              cases hFirst : (head.act state).phase <;>
                cases hSecond : (head.act (head.act state).state).phase <;>
                simp [PauliTerm.basisAction, BasisAction.compose,
                  BasisAction.identity, Phase.mul, hFirst, hSecond]
            _ = BasisAction.identity state := by
              simpa [BasisAction.compose, BasisAction.identity, Phase.mul] using
                pauli_factor_act_self_inverse head state

end B9
