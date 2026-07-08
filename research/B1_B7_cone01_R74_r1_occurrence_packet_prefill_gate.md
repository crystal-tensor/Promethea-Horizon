# B1/B7 Cone01 R74 R1 Occurrence Packet Prefill Gate

## Summary

- Status: `cone01_r74_r1_occurrence_packet_prefill_partial_zero_credit`
- R73-D1 prefilled: `True`
- R73 intake accepted: `False`
- R73 failed gates: `4`
- Source line1381: `cx q[3],q[15];`
- Candidate line1381: `U(0.42054081161117135,pi/4,0) q[14];`
- Structural CNOT delta: `6`
- Accepted exit routes: `0`
- Accepted occurrence removal: `0`
- Accepted proxy-T reduction: `0`
- B7 credit delta: `0`
- Blocker queue hash: `1a0dc6cd363dd0ae3b03c2182c960304d721cfbf55034b2698c0ea3b9bffbc1c`

R74 fills the R73-D1 source-backed occurrence packet shape using the existing source/candidate OpenQASM3 artifacts and a replay verdict. It intentionally leaves R73-D2 proxy-T and R73-D3 line1378 no-double-counting open, so the intake remains rejected and all credit stays zero.

## Remaining Failed Gates

- `all_required_fields_complete`
- `all_hash_bound_artifacts_exist`
- `proxy_t_delta_source_backed`
- `r2_no_double_counting_source_backed`

## Requirements

- `J1` PASS: R74 binds source and candidate OpenQASM3 hashes
- `J2` PASS: source line1381 is a CNOT and candidate same line is not a CNOT
- `J3` PASS: structural CNOT delta remains positive but not accepted credit
- `J4` PASS: R73-D1 packet fields are fully populated and hash-bound
- `J5` PASS: R73 intake still rejects the submission because D2/D3 remain open
- `J6` PASS: R74 keeps all accepted deltas and B7 credit at zero
- `J7` PASS: R74 emits a remaining C2/C3 blocker queue
- `J8` PASS: R74 does not claim O3 closure, reroute, or resource savings

## Claim Boundary

- Supported: R74 fills the R73-D1 R1 occurrence packet with hash-bound source, candidate, replay stdout, and replay verdict artifacts.
- Not supported: R74 does not close R73, does not accept occurrence/proxy-T deltas, does not solve line1378 no-double-counting, and does not grant B7 credit.
- Next gate: Fill R73-D2 proxy-T pricing replay and R73-D3 line1378 no-double-counting or recovery replay, then rerun R73 and R72.

## Artifacts

- `r1_occurrence_artifact`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R74-r1-line1381-occurrence-replay-artifact.json`
- `r1_occurrence_stdout`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R74-r1-line1381-occurrence-replay.stdout.txt`
- `r1_occurrence_verdict`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R74-r1-line1381-occurrence-replay.verdict.json`
- `r73_submission`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R74-r1-occurrence-source-closure-submission.json`
- `r73_intake_verdict`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R74-r1-occurrence-source-closure-intake.verdict.json`
- `blocker_queue`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R74-source-closure-blocker-queue.json`
