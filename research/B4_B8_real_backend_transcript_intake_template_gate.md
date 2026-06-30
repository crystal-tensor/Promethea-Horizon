# B4/B8 Real-Backend Transcript Intake Template Gate

Status: **real_backend_transcript_intake_template_open_missing_rows**

## Summary

- Method: `b4_b8_real_backend_transcript_intake_template_gate_v0`
- Model status: `hardware_transcript_schema_and_margin_packets_built_no_real_rows`
- Intake requirements passed/failed: 5 / 3
- Failed intake requirement IDs: ['T5', 'T6', 'T7']
- Margin blockers covered: ['M4', 'M5', 'M6']
- Transcript row schema keys: 19
- Production-required row keys: 10
- Template table hash: `ee83ca221aab4bab13b324f458b58efa7ce275cab511bcd0a1c793ba7087f405`
- Holdout rows / real backend rows: 160 / 0
- No-leak budget: <= 16 accepts per 160
- Full-leak budget: <= 40 accepts per 160

## Intake Packets

| Packet | Blocks | Owner | Submitted rows | Accepted rows | Ready |
|---|---|---|---:|---:|---|
| B4B8-M4-leakage-blind-no-leak-retest | M4 | adversary_margin_agent | 0 | 0 | False |
| B4B8-M5-full-leakage-containment-or-exclusion | M5 | protocol_boundary_agent | 0 | 0 | False |
| B4B8-M6-real-backend-transcript-rows | M6 | hardware_execution_agent | 0 | 0 | False |

## Transcript Row Schema

transcript_id, backend_name, backend_properties_hash, job_id_hash, circuit_id, qasm_sha256, refresh_mode, shot_count, private_predicate_bit_count, hidden_predicate_mask_hash, leakage_condition, accepted_count, total_count, acceptance_rate, readout_mitigation_tag, calibration_timestamp_utc, raw_counts_sha256, postprocess_script_sha256, claim_boundary

## Requirement Results

- T1 [PASS]: Real-backend soundness margin gate is present and failed on M4-M6
- T2 [PASS]: Packet scout still preserves the real-backend evidence blockers
- T3 [PASS]: Three margin-failure intake packets are generated
- T4 [PASS]: Transcript row schema is explicit and hashable
- T5 [FAIL]: Submitted real-backend transcript rows are present
- T6 [FAIL]: Accepted real-backend transcript rows cover all margin packets
- T7 [FAIL]: Real-backend margin retest is ready
- T8 [PASS]: Forbidden soundness, advantage, and BQP claims remain false

## Claim Boundary

- Supported: The failed real-backend margin gates M4-M6 have been converted into hashable transcript intake packets with explicit row keys and acceptance budgets.
- Not supported: No real backend rows are submitted or accepted, the margin gate is not ready to rerun, and no protocol soundness, quantum advantage, sampling hardness, or BQP separation is established.
- Next gate: Submit real-backend transcript rows satisfying the 19-key schema, keep leakage-blind no-leak accepts <= 16/160, and either exclude full leakage or keep full-leak accepts <= 40/160.
- protocol_soundness_proved: False
- quantum_advantage_claimed: False
- bqp_separation_claimed: False

## Validation

- validation_error_count: 0
