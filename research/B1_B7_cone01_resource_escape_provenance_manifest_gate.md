# B1/B7 Cone_01 Resource-Escape Provenance Manifest Gate

Status: `cone01_resource_escape_provenance_manifest_open_missing_artifact`

## Summary

- Method: `b1_b7_cone01_resource_escape_provenance_manifest_gate_v0`
- Manifest: `B1-B7-cone01-resource-escape-provenance-manifest`
- Priority packet: `B1-B7-cone01-resource-escape`
- Priority packet hash: `1540027cb1e7786e528cb7b018836c9aa688ceeb3a745ee255ec87583463cac7`
- Manifest hash: `618f9a79749f1471da4c373164facba9e89d90b6e57904aa1ba92429e144dd81`
- Requirements passed/failed: `6` / `3`
- Failed requirement IDs: `['P6', 'P7', 'P8']`
- Required key / production key / evidence file count: `14` / `7` / `12`
- Selected lines: `[268, 1381]`
- Dropped overlap line(s): `[1378]`
- line1381 off-grid parameters / unpriced proxy-T pressure: `5` / `100`
- line1378 delta recovered: `False`
- accepted occurrence removal / proxy-T reduction: `0` / `0`
- Submitted manifest exists: `False`
- validation_error_count: `0`

## Manifest Packet

- Submission path: `results/B1_B7_cone01_resource_escape_provenance_manifest_submissions/B1-B7-cone01-resource-escape-provenance-manifest.json`

Required evidence files:

- accepted_resource_escape_priority_packet
- qiskit_loader_claim_boundary_seal_manifest
- physical_synthesis_pricing_manifest
- openqasm3_candidate_source_map
- selected_line_window_manifest
- line1381_resolution_manifest
- line1378_recovery_manifest
- occurrence_certificate_batch_manifest
- b7_refreshed_ledger_replay
- full_replay_or_symbolic_equivalence_certificate
- no_double_counting_ledger
- claim_boundary_note

Acceptance predicates:

- manifest_id equals B1-B7-cone01-resource-escape-provenance-manifest
- priority_packet_id equals B1-B7-cone01-resource-escape
- priority_packet_hash matches the source priority packet gate
- Qiskit-loader claim-boundary seal, physical synthesis pricing, OpenQASM 3 candidate/source map, selected-line window, B7 ledger replay, and claim boundary are hash-bound
- at least one exit route manifest is present: line1381 resolution, line1378 recovery, or occurrence certificate batch
- replay_hashes bind priority_packet_hash and priority_packet_id
- source evidence files are present and hash-bound
- claim_boundary forbids resource-saving, B7-ledger improvement, occurrence-removal, and proxy-T reduction claims until the downstream artifact is accepted

## Requirement Results

- P1 [PASS]: Priority resource-escape packet remains valid and blocked only on P6/P7/P8
- P2 [PASS]: Provenance manifest is bound to the B1/B7 cone_01 resource-escape packet
- P3 [PASS]: Manifest packet carries locked provenance schema and evidence file classes
- P4 [PASS]: Current line-1381, line-1378, and occurrence blockers remain preserved
- P5 [PASS]: B7 ledger credit remains zero before source-backed resource-escape evidence
- P6 [FAIL]: Resource-escape provenance manifest artifact has been submitted
- P7 [FAIL]: Submitted manifest satisfies the locked provenance schema
- P8 [FAIL]: Submitted manifest is source-backed, packet-bound, replay-bound, and claim-boundary-bound
- P9 [PASS]: Forbidden resource-saving and B7-ledger claims remain false

## Claim Boundary

- Supported: The B1/B7 cone_01 resource-escape route now has a provenance manifest packet that must bind the priority packet, Qiskit-loader seal, physical pricing, OpenQASM 3 source map, B7 ledger replay, and claim boundary before any escape artifact can count.
- Not supported: No provenance manifest or escape artifact has been submitted or accepted; line 1381 remains unpriced, line 1378 remains unrecovered, occurrence certificates remain 0, and no B7 resource saving is supported.
- Next gate: Submit B1-B7-cone01-resource-escape-provenance-manifest with the accepted priority packet hash, claim-boundary seal hash, physical-pricing hash, OpenQASM 3 source map, selected-line window, B7 ledger replay, and one source-backed exit-route manifest.
- resource_saving_claimed: False
- b7_ledger_improvement_claimed: False
- occurrence_removal_claimed: False
- proxy_t_reduction_claimed: False

## Validation

- validation_error_count: 0
