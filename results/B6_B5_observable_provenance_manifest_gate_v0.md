# B6/B5 Observable Provenance Manifest Gate

Status: `observable_provenance_manifest_open_missing_artifact`

## Summary

- Method: `b6_b5_observable_provenance_manifest_gate_v0`
- Manifest: `B6B5-O1-monolayer-FeSe-STO-provenance-manifest`
- Priority material: `monolayer_FeSe_STO_2012`
- Manifest hash: `4fd7ae7895d29079d5bb33ea9095adcda163c4771cafb37293a6a86ee5731ae9`
- Requirements passed/failed: `9` / `0`
- Failed requirement IDs: `[]`
- Required key / production key / evidence file count: `11` / `7` / `10`
- Template row count: `12`
- Submitted manifest exists: `True`
- Accepted priority DFT/B5 rows: `0` / `0`
- validation_error_count: `2`

## Manifest Packet

- Submission path: `results\B6_B5_observable_provenance_manifest_submissions\B6B5-O1-monolayer-FeSe-STO-provenance-manifest.json`

Required evidence files:

- structure_reference_or_cif_manifest
- structure_reference_hash_source
- dft_input_protocol_note
- dft_output_parser_note
- effective_model_derivation_protocol
- b5_solver_protocol_note
- same_access_cost_unit_note
- source_replay_hash_manifest
- observable_join_key_audit
- claim_boundary_note

Acceptance predicates:

- manifest_id equals B6B5-O1-monolayer-FeSe-STO-provenance-manifest
- material_id equals monolayer_FeSe_STO_2012
- structure reference, DFT protocol, parser, effective-model protocol, B5 solver protocol, same-access cost unit, and replay hashes are present
- source_table_hash, replay_formula_hash, and replay_table_hash match the priority observable packet
- source evidence files are present and hash-bound
- claim_boundary forbids DFT-observable, B5-observable, material-discovery, mechanism-solved, and solution claims

## Requirement Results

- P1 [PASS]: Priority observable packet remains valid and blocked only on P6/P7/P8
- P2 [PASS]: Provenance manifest is bound to the rank-1 monolayer FeSe/STO material
- P3 [PASS]: Manifest packet carries locked schema and evidence file classes
- P4 [PASS]: Observable row denominator and replay hashes remain preserved
- P5 [PASS]: Current state has no accepted DFT/B5 observable row
- P6 [PASS]: Provenance manifest artifact has been submitted
- P7 [PASS]: Submitted manifest satisfies the locked provenance schema
- P8 [PASS]: Submitted manifest is source-backed, material-bound, and replay-hash-bound
- P9 [PASS]: Forbidden observable, discovery, mechanism, and solution claims remain false

## Claim Boundary

- Supported: The rank-1 B6/B5 observable route now has a concrete provenance manifest packet that must be accepted before DFT/B5 observable rows can be considered.
- Not supported: No provenance manifest, DFT row, or B5-computed observable row has been submitted or accepted; no material discovery, mechanism-solved, observable, or solution claim is supported.
- Next gate: Submit B6B5-O1-monolayer-FeSe-STO-provenance-manifest with structure reference, DFT protocol, parser, effective-model protocol, B5 solver protocol, same-access cost unit, source replay hashes, and claim boundary.
- dft_observable_claimed: False
- b5_computed_observable_claimed: False
- material_discovery_claimed: False
- mechanism_solved: False
- solution_claimed: False

## Validation

- validation_error_count: 2
- unexpected observable provenance manifest failures: []
- gate expected no submitted manifest until an observable PR supplies one
