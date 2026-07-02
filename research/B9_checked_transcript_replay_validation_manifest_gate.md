# B9 Checked Transcript Replay-Validation Manifest Gate

Status: `checked_transcript_replay_validation_manifest_open_missing_artifact`

## Summary

- Method: `b9_checked_transcript_replay_validation_manifest_gate_v0`
- Manifest: `B9-checked-width-locality-transcript-replay-validation-manifest`
- Provenance manifest: `B9-checked-width-locality-transcript-provenance-manifest`
- Priority packet: `B9-checked-width-locality-transcript`
- Provenance manifest hash: `1b3716b5f1a8ca396557dad26298a99a469349733abcf6d345e9cd4bb467f1d1`
- Manifest hash: `453a3419bd263174f22caa2c22babaa6e90dad0fa12e2d51dac8bd4e2995a281`
- Requirements passed/failed: `6` / `3`
- Failed requirement IDs: `['P6', 'P7', 'P8']`
- Required key / production key / evidence file count: `18` / `14` / `14`
- Blocks acquisition requirements: `['A3', 'A4', 'A6']`
- Submitted manifest exists: `False`
- Checked transcript present: `False`
- Proof assistant checked: `False`
- validation_error_count: `0`

## Replay-Validation Manifest Packet

- Submission path: `results/B9_checked_transcript_replay_validation_manifest_submissions/B9-checked-width-locality-transcript-replay-validation-manifest.json`
- Provenance manifest hash: `1b3716b5f1a8ca396557dad26298a99a469349733abcf6d345e9cd4bb467f1d1`
- Lean module hash at gate time: `d885cfe38990798c8cbd281959ed995a17427b38991968a9f40801c2a3bfa43c`

Required evidence files:

- accepted_checked_transcript_provenance_manifest
- lean_toolchain_replay_file
- lakefile_replay_file
- lean_module_replay_file
- lean_version_stdout_replay
- lake_version_stdout_replay
- lake_env_lean_command_replay
- checked_transcript_stdout
- checked_transcript_stderr
- checked_transcript_file
- returncode_and_elapsed_time_ledger
- offline_bundle_hash_manifest
- reproduction_environment_note
- claim_boundary_note

Acceptance predicates:

- manifest_id equals B9-checked-width-locality-transcript-replay-validation-manifest
- provenance_manifest_id equals B9-checked-width-locality-transcript-provenance-manifest
- packet_id equals B9-checked-width-locality-transcript
- priority_packet_hash and provenance_manifest_hash match the source gates
- Lean toolchain, lakefile, and Lean module replay hashes match gate-time source hashes
- Lean version, Lake version, lake env lean command, stdout, stderr, returncode, and elapsed time are hash-bound
- checked_transcript_sha256 matches the checked transcript file
- source evidence files are present and replay_hashes bind the provenance manifest plus local source hashes
- claim_boundary forbids Quantum PCP, NLTS, formal theorem, and global impossibility claims until a checked run is accepted

## Requirement Results

- P1 [PASS]: Checked transcript provenance manifest gate remains valid and blocked only on P6/P7/P8
- P2 [PASS]: Replay manifest is bound to the checked transcript packet and provenance manifest
- P3 [PASS]: Replay manifest packet carries locked replay schema and evidence classes
- P4 [PASS]: Pinned Lean project source hashes remain stable at the replay gate
- P5 [PASS]: Current state has no checked transcript or theorem claim
- P6 [FAIL]: Replay-validation manifest artifact has been submitted
- P7 [FAIL]: Submitted replay manifest satisfies the locked checked-run replay schema
- P8 [FAIL]: Submitted replay manifest is source-backed, manifest-bound, replay-bound, returncode-zero, and claim-boundary-bound
- P9 [PASS]: Forbidden Quantum PCP, NLTS, formal theorem, and global impossibility claims remain false

## Claim Boundary

- Supported: The B9 checked-transcript route now has a replay-validation manifest packet that must bind Lean/Lake source hashes, version outputs, checked-run stdout/stderr, returncode, elapsed time, transcript hash, offline bundle hash, and claim boundary.
- Not supported: No replay-validation manifest or checked transcript has been submitted or accepted; no proof-assistant checked theorem, Quantum PCP proof, NLTS theorem, or global impossibility theorem is supported.
- Next gate: Submit results/B9_checked_transcript_replay_validation_manifest_submissions/B9-checked-width-locality-transcript-replay-validation-manifest.json with the accepted provenance manifest hash and checked-run replay evidence before the checked transcript priority artifact can count.
- proof_assistant_checked: False
- formal_theorem_proved: False
- explicit_not_quantum_pcp_proof: True
- nlts_theorem_claimed: False
- global_gap_amplification_impossibility_claimed: False

## Validation

- validation_error_count: 0
