# B6/B5 Observable Replay-Validation Manifest Gate

Status: `observable_replay_validation_manifest_open_missing_artifact`

## Summary

- Method: `b6_b5_observable_replay_validation_manifest_gate_v0`
- Manifest: `B6B5-O1-monolayer-FeSe-STO-replay-validation-manifest`
- Provenance manifest: `B6B5-O1-monolayer-FeSe-STO-provenance-manifest`
- Priority material: `monolayer_FeSe_STO_2012`
- Provenance manifest hash: `a7ddd0cbd869eadc8c93311a2e52d33b15942580dde01a78057333044f8058fe`
- Manifest hash: `6e3902319b091401031dd158a9c37ccb46bd7143df247b4b60aa0e7b2037e622`
- Requirements passed/failed: `6` / `3`
- Failed requirement IDs: `['P6', 'P7', 'P8']`
- Required key / production key / evidence file count: `15` / `12` / `12`
- Replay scope records/families/negative controls: `56` / `28` / `18`
- Selected variant / negative controls in top-k: `physics_risk_adjusted_v0` / `2`
- Submitted manifest exists: `False`
- Accepted priority DFT/B5 rows: `0` / `0`
- validation_error_count: `0`

## Manifest Packet

- Submission path: `results/B6_B5_observable_replay_validation_manifest_submissions/B6B5-O1-monolayer-FeSe-STO-replay-validation-manifest.json`

Required evidence files:

- accepted_observable_provenance_manifest
- backend_replay_scope_manifest
- structure_reference_manifest
- dft_replay_command
- dft_output_parser_manifest
- effective_model_replay_manifest
- b5_observable_solver_replay
- same_access_cost_ledger
- negative_control_audit
- family_prior_denominator_table
- source_replay_hash_manifest
- claim_boundary_note

Acceptance predicates:

- manifest_id equals B6B5-O1-monolayer-FeSe-STO-replay-validation-manifest
- provenance_manifest_id equals B6B5-O1-monolayer-FeSe-STO-provenance-manifest
- material_id equals monolayer_FeSe_STO_2012
- provenance_manifest_hash matches the accepted observable provenance manifest hash
- backend replay scope preserves 56 records, 28 families, 18 negative controls, 27 post-split rows, and the selected physics_risk_adjusted_v0 replay
- DFT replay, effective-model replay, B5 observable solver replay, same-access cost ledger, negative-control audit, family-prior denominator, and source replay hashes are present
- source_replay_hashes bind source_table_hash, replay_formula_hash, and replay_table_hash
- claim_boundary forbids DFT-observable, B5-observable, material-discovery, mechanism-solved, and solution claims until rows are accepted

## Requirement Results

- P1 [PASS]: Observable provenance manifest gate remains valid and blocked only on P6/P7/P8
- P2 [PASS]: Replay-validation manifest is bound to rank-1 monolayer FeSe/STO
- P3 [PASS]: Manifest packet carries locked replay-validation schema and evidence classes
- P4 [PASS]: Backend replay scope and family-prior denominator remain preserved
- P5 [PASS]: Current state has no accepted DFT/B5 observable row and no discovery claim
- P6 [FAIL]: Replay-validation manifest artifact has been submitted
- P7 [FAIL]: Submitted manifest satisfies the locked replay-validation schema
- P8 [FAIL]: Submitted manifest is source-backed, provenance-bound, replay-bound, and claim-boundary-bound
- P9 [PASS]: Forbidden observable, discovery, mechanism, and solution claims remain false

## Claim Boundary

- Supported: The rank-1 B6/B5 observable route now has a replay-validation manifest packet that must bind the accepted provenance manifest, backend replay scope, DFT replay, B5 observable replay, negative controls, family-prior denominator, same-access cost, and claim boundary before observable rows can count.
- Not supported: No replay-validation manifest, DFT row, or B5-computed observable row has been submitted or accepted; no material discovery, mechanism-solved, observable, or solution claim is supported.
- Next gate: Submit B6B5-O1-monolayer-FeSe-STO-replay-validation-manifest with the accepted provenance manifest hash, backend replay scope, DFT/effective-model/B5 replay hashes, same-access ledger, negative-control audit, family-prior denominator, source replay hashes, and claim boundary.
- dft_observable_claimed: False
- b5_computed_observable_claimed: False
- material_discovery_claimed: False
- mechanism_solved: False
- solution_claimed: False

## Validation

- validation_error_count: 0
