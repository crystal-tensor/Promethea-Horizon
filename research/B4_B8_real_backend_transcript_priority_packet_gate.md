# B4/B8 Real-Backend Transcript Priority Packet Gate

Status: **real_backend_transcript_priority_packet_open_missing_artifact**

## Summary

- Method: `b4_b8_real_backend_transcript_priority_packet_gate_v0`
- Model status: `priority_real_backend_transcript_packet_ready_no_rows_submitted`
- Priority packet: `B4B8-M6-real-backend-transcript-rows`
- Packet hash: `e40246c4ddbfa3c31c69069a6551c20694211ceb1a1e71695ae41789d3010e21`
- Requirements passed/failed: 6 / 3
- Failed requirement IDs: ['P6', 'P7', 'P8']
- Transcript row schema keys: 19
- Production-required row keys: 10
- Required evidence file classes: 8
- Holdout rows / real backend rows: 160 / 0
- No-leak budget: <= 16 accepts per 160
- Full-leak budget: <= 40 accepts per 160
- Submitted artifact exists: False
- Accepted priority transcript rows: 0

## Submission Packet

- Submission path: `results/B4_B8_real_backend_transcript_priority_submissions/B4B8-M6-real-backend-transcript-rows.json`
- Blocks margin gate: `M6`
- Owner role: `hardware_execution_agent`

Required evidence files:

- backend_properties_manifest
- hashed_backend_job_metadata
- executed_openqasm3_or_transpiled_circuit_manifest
- hidden_predicate_mask_commitment
- raw_counts_artifact
- readout_mitigation_or_no_mitigation_manifest
- postprocess_script
- calibration_timestamp_source

Acceptance predicates:

- all 19 transcript row keys are present
- all 10 production-required keys are non-null and source-backed
- total_count equals the locked 160-row holdout denominator or declares a reviewed replacement denominator
- accepted_count and acceptance_rate replay from raw_counts_sha256 and postprocess_script_sha256
- the row declares leakage_condition and private_predicate_bit_count before scoring
- claim_boundary forbids protocol soundness, quantum advantage, sampling hardness, and BQP separation claims

## Transcript Row Schema

transcript_id, backend_name, backend_properties_hash, job_id_hash, circuit_id, qasm_sha256, refresh_mode, shot_count, private_predicate_bit_count, hidden_predicate_mask_hash, leakage_condition, accepted_count, total_count, acceptance_rate, readout_mitigation_tag, calibration_timestamp_utc, raw_counts_sha256, postprocess_script_sha256, claim_boundary

## Requirement Results

- P1 [PASS]: Intake template remains valid and open on real-backend transcript rows
- P2 [PASS]: Priority packet is fixed to the first real-backend transcript row blocker
- P3 [PASS]: Transcript packet carries the 19-key schema and 10 production keys
- P4 [PASS]: Packet binds required backend evidence file classes
- P5 [PASS]: Locked margin budgets are preserved for later retest
- P6 [FAIL]: Priority real-backend transcript artifact has been submitted
- P7 [FAIL]: Submitted artifact satisfies the locked 19-key transcript schema
- P8 [FAIL]: Submitted production keys are source-backed and budget-accountable
- P9 [PASS]: Forbidden soundness, advantage, and BQP claims remain false

## Claim Boundary

- Supported: The first B4/B8 real-backend evidence blocker now has a concrete source-backed transcript submission packet for the M6 row requirement.
- Not supported: No real-backend transcript row has been submitted or accepted; the margin gate is not ready to rerun and no protocol soundness, quantum advantage, sampling-hardness, cryptographic-soundness, or BQP-separation claim is supported.
- Next gate: Submit results/B4_B8_real_backend_transcript_priority_submissions/B4B8-M6-real-backend-transcript-rows.json with all 19 transcript keys, all 10 source-backed production keys, raw-count and postprocess hashes, and replayable accepted_count against the locked 160-row margin denominator.
- protocol_soundness_proved: False
- quantum_advantage_claimed: False
- bqp_separation_claimed: False

## Validation

- validation_error_count: 0
