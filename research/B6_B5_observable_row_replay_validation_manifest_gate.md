# B6/B5 Observable Row Replay-Validation Manifest Gate

Status: `observable_row_replay_validation_manifest_open_missing_artifact`

## Summary

- Method: `b6_b5_observable_row_replay_validation_manifest_gate_v0`
- Manifest: `B6B5-O1-monolayer-FeSe-STO-row-replay-validation-manifest`
- Source replay manifest: `B6B5-O1-monolayer-FeSe-STO-replay-validation-manifest`
- Priority material: `monolayer_FeSe_STO_2012`
- Replay-validation manifest hash: `6e3902319b091401031dd158a9c37ccb46bd7143df247b4b60aa0e7b2037e622`
- Provenance manifest hash: `a7ddd0cbd869eadc8c93311a2e52d33b15942580dde01a78057333044f8058fe`
- Manifest hash: `16fecc141f05a7b641e1d10009b1c0c2bb8e62927aa0a4d01360cef563a2edfb`
- Requirements passed/failed: `6` / `3`
- Failed requirement IDs: `['P6', 'P7', 'P8']`
- Required key / production key / evidence file count: `18` / `15` / `14`
- Replay scope records/families/negative controls: `56` / `28` / `18`
- Template rows / negative controls in top-k: `12` / `2`
- Submitted manifest exists: `False`
- Accepted priority DFT/B5 rows: `0` / `0`
- validation_error_count: `0`

## Row Replay-Validation Manifest Packet

- Submission path: `results/B6_B5_observable_row_replay_validation_manifest_submissions/B6B5-O1-monolayer-FeSe-STO-row-replay-validation-manifest.json`

Required evidence files:

- accepted_observable_replay_validation_manifest
- observable_row_template_table
- dft_row_table
- b5_observable_row_table
- structure_reference_manifest
- dft_input_deck_replay
- dft_output_parser_replay
- effective_model_mapping
- b5_solver_observable_replay
- same_access_cost_ledger
- negative_control_audit
- family_prior_denominator_table
- row_acceptance_ledger
- claim_boundary_note

Acceptance predicates:

- manifest_id equals B6B5-O1-monolayer-FeSe-STO-row-replay-validation-manifest
- source_replay_validation_manifest_id equals B6B5-O1-monolayer-FeSe-STO-replay-validation-manifest
- material_id equals monolayer_FeSe_STO_2012
- replay_validation_manifest_hash, provenance_manifest_hash, and template_table_hash match source gates
- DFT row table, B5 observable row table, structure reference, DFT input/output replay, effective-model mapping, B5 solver replay, same-access ledger, negative-control audit, family-prior denominator, and row-acceptance ledger are hash-bound
- row_acceptance_ledger keeps accepted DFT/B5 rows at 0 until both channels are submitted and audited
- source evidence files are present and source_replay_hashes bind the source table, formula, replay table, replay-validation manifest, provenance manifest, and template table
- claim_boundary forbids DFT-observable, B5-observable, material-discovery, mechanism-solved, and solution claims until rows are accepted

## Requirement Results

- P1 [PASS]: Observable replay-validation manifest gate remains valid and blocked only on P6/P7/P8
- P2 [PASS]: Row replay manifest is bound to rank-1 monolayer FeSe/STO and source replay manifest
- P3 [PASS]: Row replay packet carries locked DFT/B5 schema and evidence classes
- P4 [PASS]: Replay scope, template table, and negative-control denominator remain preserved
- P5 [PASS]: Current state has no accepted DFT/B5 observable rows and no discovery claim
- P6 [FAIL]: Row replay-validation manifest artifact has been submitted
- P7 [FAIL]: Submitted row replay manifest satisfies the locked DFT/B5 replay schema
- P8 [FAIL]: Submitted row replay manifest is source-backed, gate-bound, replay-bound, and claim-boundary-safe
- P9 [PASS]: Forbidden observable, discovery, mechanism, and solution claims remain false

## Claim Boundary

- Supported: The rank-1 B6/B5 observable route now has a row replay-validation manifest packet after the replay manifest and before DFT/B5 observable rows can count.
- Not supported: No row replay-validation manifest, DFT row, or B5-computed observable row has been submitted or accepted; no material discovery, mechanism-solved, observable, or solution claim is supported.
- Next gate: Submit B6B5-O1-monolayer-FeSe-STO-row-replay-validation-manifest with DFT and B5 row tables, structure reference, DFT replay, effective-model mapping, B5 solver replay, same-access cost ledger, negative-control audit, family-prior denominator, row acceptance ledger, and claim boundary.
- accepted_priority_dft_rows: 0
- accepted_priority_b5_rows: 0
- dft_observable_claimed: False
- b5_computed_observable_claimed: False
- material_discovery_claimed: False
- mechanism_solved: False
- solution_claimed: False

## Validation

- validation_error_count: 0
