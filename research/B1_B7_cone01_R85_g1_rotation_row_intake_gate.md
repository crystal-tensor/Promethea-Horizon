# B1/B7 Cone01 R85 G1 Rotation-Row Intake Gate

- Target: `T-B1-004gi/T-B7-015r`
- Upstream target: `T-B1-004gh/T-B7-015q`
- Method: `b1_b7_cone01_r85_g1_rotation_row_intake_gate_v0`
- Status: `cone01_r85_g1_source_rotation_rows_intake_ready_no_credit`
- Model status: `r84_selected_g1_materialized_as_source_backed_rotation_row_intake`

## Result

R85 materializes the R84-selected G1 route into a source-backed row intake.
It extracts the first 30 `arbitrary_numeric_rotation` components from the
`gcm_h6` QASM under the same B7 classifier that reports 270 arbitrary
numeric rotations. The selected rows give a candidate `600` T-ledger-unit
mapping, but the preflight still rejects any credit because replay stdout,
STV reprice, a filled R83 submission, and downstream B7 replay are missing.

## Key Counters

- B7 classifier arbitrary components: `270`
- Selected G1 source rows: `30`
- Candidate T-ledger reduction: `600`
- Accepted T-ledger reduction: `0`
- Candidate after T-ledger if all rows accepted: `5624`
- No-double-counting screen passed: `True`
- Preflight accepted: `False`
- Accepted B7 credit delta: `0`

## Failed Credit Gates

- `replay_stdout_present`
- `stv_reprice_ledger_present`
- `filled_r83_submission_present`
- `downstream_b7_replay_present`

## Requirements

- `A1` PASS: R84 selects G1 as the upstream route
- `A2` PASS: R85 source QASM matches B7 numeric-structure classifier count
- `A3` PASS: R85 materializes exactly 30 source-backed G1 candidate rows
- `A4` PASS: R85 candidate mapping reaches the 600-unit G1 target without accepted credit
- `A5` PASS: R85 no-double-counting screen has unique selected source components
- `A6` PASS: R85 preflight rejects credit until replay, STV, R83 fill, and B7 replay exist
- `A7` PASS: R85 preserves claim boundaries and emits next blockers

## Artifacts

- Result JSON: `results/B1_B7_cone01_R85_g1_rotation_row_intake_gate_v0.json`
- Source rows: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R85-G1-source-rotation-rows.json`
- Candidate T mapping: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R85-G1-candidate-logical-t-mapping.json`
- No-double-counting screen: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R85-G1-no-double-counting-screen.json`
- Preflight verdict: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R85-G1-row-intake-preflight.verdict.json`
- Blocker queue: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R85-G1-row-intake-blocker-queue.json`
- Stdout: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R85-G1-row-intake.stdout.txt`

## Claim Boundary

R85 is an intake gate, not a rewrite certificate. It does not prove that
the selected rotations can be removed or repriced, does not provide replay
stdout, does not provide a full STV reprice, does not fill every R83 field,
and does not run downstream B7 replay. B7 credit remains zero.
