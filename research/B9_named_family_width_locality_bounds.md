# B9 Named-Family Width/Locality Bound Skeleton v0.1

Last updated: 2026-07-15

Status: **named_family_width_locality_bound_skeleton_checked_interface_not_theorem**

## Summary

- Named family: `cluster_stabilizer_open_uniform_reweight`
- Source method: small_local_hamiltonian_gap_lab_v0
- Rows matched: 3 for qubits [4, 5, 6]
- Scaling factor: 1.35
- Max locality: 3
- Locality bound preserved: True
- Raw gap amplifies: True
- Normalized gap invariant: True
- Certificate rejected: True
- Proof assistant checked: True
- Proof assistant status: passed
- Formal theorem proved: False
- Explicitly not Quantum PCP proof: True
- Global impossibility claimed: False
- Validation errors: 0

## Analytic Bound Statement

- For the open-boundary cluster stabilizer family, every generated term has support size 2 or 3.
- The B9 local_interaction_reweight_v0 transformation multiplies every support>=2 term by 1.35.
- Therefore H'_n = 1.35 * H_n for the generated family rows.
- Positive uniform scaling preserves eigenvectors and scales both spectral gap and spectral width by 1.35.
- The normalized-gap identity is now derived in Lean from the nonzero-scale hypothesis via mul_div_mul_left; the ratio equality is no longer assumed.
- The normalized gap gap(H)/width(H) is invariant, while max locality remains 3.

## Finite Row Checks

- n=4: term_count=4, supports=[2, 3], unique_scales=[1.35], max_support=3
- n=5: term_count=5, supports=[2, 3], unique_scales=[1.35], max_support=3
- n=6: term_count=6, supports=[2, 3], unique_scales=[1.35], max_support=3

## Rejection Reason

Raw spectral gap growth is exactly global positive energy rescaling; spectral width scales by the same factor, so normalized gap does not improve.

## Claim Boundary

- Supported: a named-family analytic skeleton explaining why the B9 v0 cluster-stabilizer local reweight rows are only uniform energy rescaling.
- Supported: finite rows n=4,5,6 match the symbolic locality/width story.
- Supported: the indexed nonzero-scale cancellation and concrete 27/20 nonzero lemmas check in Lean 4.12.0/Lake.
- Not supported: the parameterized all-n family theorem, Quantum PCP proof, NLTS theorem, or global gap-amplification no-go theorem.

## Remaining Steps

- Formalize the parameterized open-boundary cluster stabilizer Hamiltonian in an actual Lean/mathlib project.
- Prove the support-size and uniform-scaling lemmas over all n >= 4.
- Formalize spectral gap and spectral-width scaling for positive scalar multiplication of self-adjoint matrices and connect it to the checked cancellation lemma.
- Connect the finite JSON rows to generated certificates rather than manual inspection.
- Generalize from this rejected uniform-scaling family to nontrivial locality-preserving transformations or prove a narrower no-go theorem.
