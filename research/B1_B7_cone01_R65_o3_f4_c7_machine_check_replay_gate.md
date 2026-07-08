# B1/B7 Cone01 R65 O3-F4 C7 Machine-Check Replay Gate

- Target: `T-B1-004fo/T-B7-014x`
- Upstream target: `T-B1-004fn/T-B7-014w`
- Method: `b1_b7_cone01_r65_o3_f4_c7_machine_check_replay_gate_v0`
- Status: `cone01_r65_c7_machine_check_replay_passed_zero_b7_credit`
- R65 bundle hash: `76544060858cd8f926c5823f2d2e30132935a1f855595316bafa1e19e29b2a39`

## Result

R65 passes 8/8 requirements by rerunning the same-access denominator verifier for all 8 accepted R63/R64 rows and comparing stable semantic replay digests. C7 is now complete for this row set, while O3, reroute, B7, STV, and resource-ledger promotion remain blocked or 0/false.

## Evidence

- Verdict count: `8`
- Passed verdicts: `8`
- Failed verdicts: `0`
- Replay commands exit zero: `True`
- Semantic digests match: `True`
- File hashes match: `True`
- Denominator distances zero: `True`
- Negative controls rejected: `True`
- Forbidden inputs unused: `True`
- C4/C5 complete: `True`
- C6 complete: `True`
- C7 complete: `True`
- B7 credit delta: `0`

## Requirement Results

- `M1` PASS: R64 upstream completed C6 and preserved zero B7 credit
- `M2` PASS: R65 reruns one verifier command per accepted R64 trace
- `M3` PASS: R65 replay semantic digests match the original R63 transcripts
- `M4` PASS: R65 replay file hashes bind R63 rows, R64 traces, transcripts, and implementation
- `M5` PASS: R65 replay keeps denominator distances at zero and rejects negative controls
- `M6` PASS: R65 replay uses no forbidden inputs
- `M7` PASS: R65 completes C7 after C4/C5 and C6
- `M8` PASS: R65 preserves O3/reroute/B7 zero-credit boundaries

## Claim Boundary

- Supported: R65 reruns the same-access denominator verifier for all 8 accepted R63/R64 rows and confirms stable semantic replay digests, file hash bindings, zero denominator distances, rejected negative controls, and no forbidden input usage.
- Not supported: R65 does not close O3, prove a general circuit optimization theorem, allow reroute, or grant B7/STV/resource-ledger promotion.
- Next gate: Run a zero-credit B7 ledger retest boundary before any promotion.

## Remaining Open Obligations

- `B7_ledger_retest_after_C7`

- validation_error_count: `0`
