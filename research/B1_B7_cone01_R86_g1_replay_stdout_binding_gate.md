# B1/B7 Cone01 R86 G1 Replay-Stdout Binding Gate

- Target: `T-B1-004gj/T-B7-015s`
- Upstream target: `T-B1-004gi/T-B7-015r`
- Method: `b1_b7_cone01_r86_g1_replay_stdout_binding_gate_v0`
- Status: `cone01_r86_g1_replay_stdout_binding_ready_no_credit`
- Model status: `r85_replay_stdout_gate_closed_without_stv_or_b7_credit`

## Result

R86 closes the first R85 blocker by emitting replay stdout for all 30
selected G1 source rows. The replay is deliberately scoped to source-line
and component binding: each row is checked against the `gcm_h6` QASM line
hash and source-component id. It is not a rewrite replay, same-unitary
certificate, STV reprice, filled R83 submission, or downstream B7 replay.

## Key Counters

- Selected G1 source rows: `30`
- Replay events: `30`
- Line hashes verified: `30`
- Source components bound: `30`
- Candidate T-ledger reduction: `600`
- Accepted T-ledger reduction: `0`
- Replay stdout present: `True`
- Preflight accepted: `False`
- Accepted B7 credit delta: `0`

## Closed Gate

- `replay_stdout_present`

## Remaining Credit Gates

- `stv_reprice_ledger_present`
- `filled_r83_submission_present`
- `downstream_b7_replay_present`

## Requirements

- `A1` PASS: R86 consumes the R85 G1 source-row intake without changing its candidate mapping
- `A2` PASS: R86 binds all 30 selected rows back to source QASM line hashes
- `A3` PASS: R86 emits replay stdout that covers every selected row
- `A4` PASS: R86 keeps replay scope below rewrite or same-unitary evidence
- `A5` PASS: R86 closes exactly the R85 replay-stdout blocker and leaves three credit blockers open
- `A6` PASS: R86 grants no B7, STV, reroute, O3, or resource-saving credit
- `A7` PASS: R86 emits the next three blockers as PR-sized work

## Artifacts

- Result JSON: `results/B1_B7_cone01_R86_g1_replay_stdout_binding_gate_v0.json`
- Replay transcript: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R86-G1-source-binding-replay-transcript.json`
- Replay stdout: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R86-G1-source-binding-replay.stdout.txt`
- Replay-aware preflight: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R86-G1-replay-aware-preflight.verdict.json`
- Blocker queue: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R86-G1-replay-aware-blocker-queue.json`

## Claim Boundary

R86 is a replay-stdout binding gate. It does not prove that any selected
rotation can be removed or repriced, does not provide same-unitary proof,
does not produce an STV reprice ledger, does not fill the R83 production
submission, and does not run downstream B7 replay. B7 credit remains zero.
