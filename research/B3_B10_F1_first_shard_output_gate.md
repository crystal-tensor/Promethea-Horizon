# B3/B10 F1 First Shard Output Gate

- Target: `T-B3-026/T-B10-015m`
- Method: `b3_b10_f1_first_shard_output_gate_v0`
- Status: `first_full_covariance_shard_output_recorded_zero_credit`
- Recorded shard: `h2o_symmetric_oh_stretch-full-covariance-shard-001`
- Shard hash: `0294e8bc505c5cca1512513058fda2dad6883fa93d5063bc6888a03cec52a2ad`

## Result

The gate records 1/65 full-covariance shard output. It passes 7/10 requirements and intentionally fails ['P8', 'P9', 'P10'] because the remaining shards, assembled rows, and accepted F1 artifact do not exist yet.

## Shard Summary

- Group count: `512`
- Nonzero covariance pairs: `12389`
- Variance sum: `29.503269119841715`
- Remaining shards: `64`

## Requirement Results

- `P1` PASS: Work-order gate is current and recognizes the worker
- `P2` PASS: Shard output was produced by the full-covariance worker
- `P3` PASS: Shard output matches a work-order contract
- `P4` PASS: Shard covariance hash and group count are stable
- `P5` PASS: Required worker hashes are present
- `P6` PASS: Claim boundary preserves zero credit
- `P7` PASS: Exactly one shard output is recorded by this gate
- `P8` FAIL: All 65 shard outputs have been produced
- `P9` FAIL: LiH/H2O/N2 rows are assembled from all shards
- `P10` FAIL: Four-row F1 artifact is accepted

## Claim Boundary

- Supported: One H2O full-covariance shard output exists and matches its work-order contract.
- Not supported: This is not all shards, not an assembled row, not an accepted F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.
- Next gate: Produce the remaining 64 shard outputs, assemble LiH/H2O/N2 rows, then submit the four-row F1 artifact.

This shard gate does not claim a reaction-dynamics solution, quantum advantage, B3 reopen credit, B10-T1 credit, or BQP separation.

## Validation

- validation_error_count: `0`
