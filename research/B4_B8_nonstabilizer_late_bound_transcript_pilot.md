# B4/B8 Non-Stabilizer Late-Bound Transcript Pilot v0.1

Last updated: 2026-06-18

Status: **nonstabilizer_late_bound_transcript_pilot_not_soundness_or_advantage**

## Summary

- Source contract: `results/B4_B8_late_bound_private_challenge_contract_gate_v0.json`
- Pilot directory: `results/B4_B8_nonstabilizer_late_bound_transcript_pilot/circuits`
- Circuits: 36
- Non-stabilizer files: 36
- Challenge qubits per circuit: 4
- Deterministic emulator broken count: 36
- Minimum min-entropy bits: 4.000
- Maximum output probability: 0.062500
- Acceptance gates passed / failed: 6 / 2

## Interpretation

This pilot removes the deterministic public-data transcript blocker found in T-B8-003b. It adds a non-stabilizer challenge-basis layer to every public skeleton and records an exact probability ledger. The old deterministic parser can no longer predict one transcript with probability 1.

This is still a small exact-probability pilot. It does not prove cryptographic soundness, sampling hardness, hardware relevance, quantum advantage, or BQP separation.

## Acceptance Gates

- PASS: `public_skeleton_private_material_still_hidden` - Inherited from T-B8-003b public skeleton contract.
- PASS: `nonstabilizer_basis_layer_present` - Each pilot circuit includes H plus T/RZ(pi/4) challenge-basis gates.
- PASS: `deterministic_transcript_blocker_removed` - The old deterministic public-data transcript predictor no longer outputs a single transcript.
- PASS: `minimum_entropy_floor_met` - The analytical probability model gives one bit of entropy per challenged qubit.
- PASS: `exact_probability_ledger_present` - Every pilot circuit has an exact small-state probability ledger.
- FAIL: `hardware_or_backend_execution_present` - No real backend properties or hardware execution are used.
- FAIL: `cryptographic_or_sampling_soundness_proved` - The pilot only removes deterministic predictability; it proves no soundness theorem.
- PASS: `no_forbidden_claims` - The report keeps hardware, hardness, soundness, advantage, and BQP claims false.

## Next Gate

Attack the non-stabilizer late-bound transcripts with stronger learned/generative spoofers, then replace the exact-probability pilot with real backend properties or hardware execution.

## Validation

- Validation errors: 0
