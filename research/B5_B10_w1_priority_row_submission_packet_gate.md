# B5/B10 W1 Priority Row Submission Packet Gate

Status: **w1_priority_row_submission_packet_open_missing_artifact**

## Summary

- Method: `b5_b10_w1_priority_row_submission_packet_gate_v0`
- Priority row: `D5H_s8_u2_eta0.25_n4x4_obs_density_site_4`
- Packet hash: `0d3620e8c5540bfd419718ab9d7ac5e4044e9f7736e0b23888f51114c13a3b8c`
- Requirements passed/failed: 6 / 3
- Failed requirement IDs: ['P6', 'P7', 'P8']
- Required row keys / production keys: 17 / 8
- Required evidence files: 8
- Submitted artifact exists: False

## Priority Row Packet

- row_id: `D5H_s8_u2_eta0.25_n4x4_obs_density_site_4`
- submission_artifact_path: `results/B5_B10_w1_priority_row_submissions/D5H_s8_u2_eta0.25_n4x4_obs_density_site_4.json`
- template_hash: `5ab7ee67accd826db90f4b3662b4377850f795529fe9d01327725d0dc4ae92e3`
- prototype_trace_hash: `0c5c5b059eafffa41eac3d17754a26440fec114a2c58e40abf9bcc3958d9d547`
- blocking packets: ['W1-E4-env-residuals', 'W1-E5-convergence', 'W1-E7-cost-ledger']

## Required Evidence Files

- canonical_mps_or_dmrg_state_manifest
- left_environment_hash_source
- right_environment_hash_source
- orthonormal_residual_norm_calculation
- discarded_weight_or_truncation_log
- wall_clock_and_peak_memory_log
- sweep_or_matvec_count_log
- same_access_replay_command

## Acceptance Conditions

- all 17 required row keys are present
- all 8 production-required keys are non-null and source-backed
- row_contract_hash equals the locked B5/B10 W1 hash
- canonical environment hashes are derived from submitted state/environment artifacts
- orthonormal residual and discarded weight are numeric and threshold-declared
- wall-clock, memory, and sweep/matvec counts are measured under same-access conditions
- no prototype value is promoted into production evidence

## Requirement Results

- P1 [PASS]: Blocker queue preserves the locked W1 row contract
- P2 [PASS]: Priority row is fixed and matches the queue head
- P3 [PASS]: Submission packet carries the full 17-key row schema and 8 production keys
- P4 [PASS]: Packet binds every required evidence file class before acceptance
- P5 [PASS]: Prototype values are explicitly provenance-only
- P6 [FAIL]: Priority-row production artifact has been submitted
- P7 [FAIL]: Submitted artifact satisfies the locked 17-key schema
- P8 [FAIL]: Submitted production keys are source-backed and non-null
- P9 [PASS]: Forbidden positive-route claims remain false

## Claim Boundary

- Supported: The priority W1 row now has a concrete submission packet and acceptance contract binding all 17 row keys, all 8 production-required keys, and the evidence files needed for environment, convergence, and cost review.
- Not supported: No priority-row artifact has been submitted or accepted; no production DMRG denominator, same-access positive route, quantum advantage, or BQP separation is supported.
- Next gate: Submit results/B5_B10_w1_priority_row_submissions/D5H_s8_u2_eta0.25_n4x4_obs_density_site_4.json with source-backed production keys and same-access cost logs, then rerun this gate before any row acceptance.
- production_dmrg_claimed: False
- same_access_positive_route_claimed: False
- quantum_advantage_claimed: False
- bqp_separation_claimed: False

## Validation

- validation_error_count: 0
