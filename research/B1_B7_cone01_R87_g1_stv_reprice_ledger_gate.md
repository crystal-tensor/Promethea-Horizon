# B1/B7 Cone01 R87 G1 STV Reprice Ledger Gate

- Target: `T-B1-004gk/T-B7-015t`
- Upstream target: `T-B1-004gj/T-B7-015s`
- Method: `b1_b7_cone01_r87_g1_stv_reprice_ledger_gate_v0`
- Status: `cone01_r87_g1_stv_reprice_ledger_ready_no_credit`
- Model status: `r86_stv_reprice_gate_closed_without_filled_r83_or_b7_replay`

## Result

R87 closes the STV reprice-ledger blocker for the R86 replay-bound G1 rows.
It produces a candidate T-ledger/STV ledger for all 30 rows, showing a
`600` unit candidate reduction from `6224` to `5624`, which is `8` units
below the `5632` 1.20x target ceiling. The ledger remains candidate-only:
it is not a filled R83 production submission and not downstream B7 replay.

## Key Counters

- Selected G1 source rows: `30`
- Replay-bound rows: `30`
- Before T ledger: `6224`
- Candidate T-ledger reduction: `600`
- Candidate after T ledger: `5624`
- 1.20x target ceiling: `5632`
- Candidate margin to 1.20x target: `8`
- STV reprice ledger present: `True`
- Accepted B7 credit delta: `0`

## Closed Gate

- `stv_reprice_ledger_present`

## Remaining Credit Gates

- `filled_r83_submission_present`
- `downstream_b7_replay_present`

## Requirements

- `A1` PASS: R87 consumes the R86 replay-bound G1 row set
- `A2` PASS: R87 builds a 30-row STV/T-ledger reprice ledger
- `A3` PASS: R87 keeps every reprice row replay-bound
- `A4` PASS: R87 candidate reprice crosses the 1.20x T-ledger target
- `A5` PASS: R87 closes exactly the R86 STV reprice blocker and leaves two credit blockers open
- `A6` PASS: R87 grants no B7, STV, reroute, O3, or resource-saving credit
- `A7` PASS: R87 emits the next two blockers as PR-sized work

## Artifacts

- Result JSON: `results/B1_B7_cone01_R87_g1_stv_reprice_ledger_gate_v0.json`
- STV reprice ledger: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R87-G1-stv-reprice-ledger.json`
- STV reprice stdout: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R87-G1-stv-reprice-ledger.stdout.txt`
- STV-aware preflight: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R87-G1-stv-aware-preflight.verdict.json`
- Blocker queue: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R87-G1-stv-aware-blocker-queue.json`

## Claim Boundary

R87 is a candidate STV reprice ledger gate. It does not fill all R83
production fields, does not run downstream B7 replay, and does not accept
B7 dependency, resource, FT-ledger, or STV credit. B7 credit remains zero.
