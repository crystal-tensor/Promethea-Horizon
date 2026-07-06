# B1/B7 Cone01 R17 NL-C02 O1 Search-Domain Boundary Gate

- Target: `T-B1-004ds/T-B7-013b`
- Method: `b1_b7_cone01_r17_nlc02_o1_search_domain_boundary_gate_v0`
- Status: `cone01_r17_nlc02_o1_search_domain_boundary_set_not_full_lemma`
- Candidate: `NL-C02`
- Boundary hash: `37b67eecde6903fa68730ad2e68d1671a373f6854efcaa89d9f3c3c8bb627f13`
- Disposition-table hash: `238d2e4450366aee16f279f36249e6d2b2780f93b2507d5b5a1d66d113b4eaf8`

## Result

The R17 O1 boundary gate passes 10/10 requirements. It disposes of O1 by declaring a search-domain boundary, not by proving optimizer completeness.

## Search-Domain Statement

NL-C02 is currently only a search-domain diagnostic: the 31 leave-out rows, R12 tolerance bridge, R13 source binding, and R16 Clifford-frame affine sublemma are accepted as bounded evidence, but optimizer completeness for the full declared parameterization is not proved.

## Disposition Rows

- `O1`: downgraded_to_search_domain_boundary
- `O2`: closed_by_r12_for_current_residual_model
- `O4`: closed_by_r13_for_current_hash_chain
- `O3a`: clifford_frame_affine_sublemma_closed_by_r16
- `O3`: full_general_local_unitary_invariance_still_open

## Decision

- O1 full optimizer completeness proved: `False`
- O1 disposed by search-domain downgrade: `True`
- Search-domain negative diagnostic ready: `True`
- O3 closed: `False`
- Remaining open obligations: `['O3', 'O1_full_optimizer_completeness_if_upgrading']`
- Checked negative lemma present: `False`
- Reroute allowed: `False`

## Requirement Results

- `H1` PASS: R11 proof skeleton is validation-clean and exposes O1
- `H2` PASS: R12 closes O2 for the current residual model
- `H3` PASS: R13 closes O4 for the current hash chain
- `H4` PASS: R16 closes only the Clifford-frame affine O3 sublemma
- `H5` PASS: O1 is explicitly downgraded rather than falsely proved
- `H6` PASS: Search-domain statement preserves all 31 leave-out rows and zero exact passes
- `H7` PASS: Boundary is hash-bound to R11, R12, R13, and R16
- `H8` PASS: Boundary records the exact upgrade evidence required before any full lemma claim
- `H9` PASS: Boundary is not upgraded into a checked negative lemma or reroute
- `H10` PASS: Boundary preserves zero resource and B7 credit claims

## Claim Boundary

- Supported: R17 disposes of O1 only by explicitly downgrading NL-C02 to a search-domain diagnostic. It preserves R11/R12/R13/R16 bounded evidence while preventing any full optimizer-completeness claim.
- Not supported: R17 does not prove optimizer completeness, does not close full O3, and does not make NL-C02 a checked negative lemma. No R5 reroute, R1 solution, occurrence removal, proxy-T reduction, B7 credit, resource saving, or impossibility theorem is supported.
- Next gate: Either supply a real O1 optimizer-completeness proof, expand O3 beyond the closed Clifford-frame affine sublemma, or keep NL-C02 permanently scoped as a search-domain diagnostic.

This boundary gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.

## Validation

- validation_error_count: `0`
