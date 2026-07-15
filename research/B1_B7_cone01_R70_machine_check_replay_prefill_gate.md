# B1/B7 Cone01 R70 Machine-Check Replay Prefill Gate

## Summary

- Status: `cone01_r70_r1_machine_check_replay_prefill_zero_credit`
- R69 prefilled fields: `26` / 29
- R70 prefilled fields: `29` / 29
- Remaining placeholder fields: `0`
- Machine-check replay stdout: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R70-R1-line1381-machine-check-replay.stdout.txt`
- Machine-check replay stdout SHA256: `f1c9b9e76aad54d4f57bc3d75cf12f61fdd8b9d3470cd36e3f2bab775d2d2199`
- Source CNOT count: `795`
- Candidate CNOT count: `789`
- Structural CNOT delta: `6`
- Accepted exit routes: `0`
- Accepted occurrence removal: `0`
- Accepted proxy-T reduction: `0`
- B7 credit delta: `0`
- R70 blocker queue hash: `fb17b4e3685ba02cad242fcb37917f191fc65653a2adcfc57ac566d7391aeb9f`

R70 fills the three machine-check replay fields left open by R69. The R1 line1381 prefill now has 29 of 29 required fields populated, but it remains unaccepted because the positive occurrence/proxy-T delta rule is still unsatisfied.

## Requirements

- `R1` PASS: R69 input has exactly the three machine-check replay placeholders
- `R2` PASS: replay command exits cleanly and emits hash-bound stdout
- `R3` PASS: R70 prefill has no placeholder fields
- `R4` PASS: source and candidate OpenQASM3 artifacts are hash-bound
- `R5` PASS: all referenced evidence files match submitted hashes
- `R6` PASS: R59/R65/R66 evidence chain is complete but zero-credit
- `R7` PASS: structural candidate CNOT reduction is detected but not accepted as a route
- `R8` PASS: positive route deltas and B7 credit remain blocked
- `R9` PASS: remaining blocker queue is positive-delta only
- `R10` PASS: R70 artifacts are written

## Remaining Acceptance Blockers

- Positive occurrence-removal delta accepted by the R67 contract.
- Positive proxy-T delta accepted by the R67 contract.
- Downstream B7 nonzero retest after a positive accepted route.

## Claim Boundary

- Supported: R70 fills the machine-check replay command/stdout/hash fields for the R1 line1381 prefill and binds source/candidate OpenQASM3 plus the R59/R65/R66 evidence chain.
- Not supported: R70 does not accept an exit route, does not provide positive occurrence/proxy-T delta evidence, does not close O3, does not allow reroute, and does not grant B7 credit.
- Next gate: Produce a positive occurrence/proxy-T delta ledger that survives the R67 accepted-exit-route contract.

## Artifacts

- `completed_prefill`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R70-R1-line1381-prefill-machine-check-replay.json`
- `machine_check_replay_stdout`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R70-R1-line1381-machine-check-replay.stdout.txt`
- `machine_check_replay_transcript`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R70-R1-line1381-machine-check-replay-transcript.json`
- `blocker_queue`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R70-positive-delta-blocker-queue.json`
