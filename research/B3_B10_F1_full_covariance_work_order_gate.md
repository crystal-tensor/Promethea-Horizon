# B3/B10 F1 Full Covariance Work Order Gate

- Target: `T-B3-025/T-B10-015l`
- Method: `b3_b10_f1_full_covariance_work_order_gate_v0`
- Status: `f1_full_covariance_work_order_ready_zero_credit`
- Work-order manifest hash: `efa602ce2bc44d7469766c80c3df2befa322f5868776267f47129840620cd980`

## Result

The gate creates 3 work orders and 65 shard contracts for LiH/H2O/N2 full covariance. It passes 8/10 requirements and intentionally fails ['P9', 'P10'] because no worker, shard outputs, or assembled rows exist yet.

## Work Orders

| molecule | full-cover group proxy | shards | compiled random terms |
|---|---:|---:|---:|
| lih_bond_stretch | 19644 | 39 | 77190 |
| h2o_symmetric_oh_stretch | 3129 | 7 | 12430 |
| n2_bond_stretch | 9475 | 19 | 34058 |

## Requirement Results

- `P1` PASS: Remaining-row scout is valid and still blocked on P8/P9/P10
- `P2` PASS: LiH/H2O/N2 work orders are generated
- `P3` PASS: Each work order is split into replayable shards
- `P4` PASS: Worker output contract is explicit for every row
- `P5` PASS: Each work order preserves the blocker reasons from the scout
- `P6` PASS: Work-order and shard contract hashes are reproducible
- `P7` PASS: No B3/B10 credit, denominator win, or accepted row is claimed
- `P8` PASS: Full covariance worker implementation exists
- `P9` FAIL: All shard outputs have been produced
- `P10` FAIL: Remaining rows are assembled and ready for F1 acceptance

## Claim Boundary

- Supported: The three blocked LiH/H2O/N2 rows now have replayable full-covariance work orders and shard contracts.
- Not supported: No full covariance worker, shard outputs, assembled rows, denominator win, B3 reopen, B10-T1 credit, quantum advantage, or BQP separation is supported.
- Next gate: Implement the row worker, produce every shard output, assemble each row, and resubmit the four-row F1 artifact.

This work-order gate does not claim a reaction-dynamics solution, quantum advantage, B3 reopen credit, B10-T1 credit, or BQP separation.

## Validation

- validation_error_count: `0`
