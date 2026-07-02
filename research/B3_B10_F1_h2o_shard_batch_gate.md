# B3/B10 F1 H2O Shard Batch Gate

- Target: `T-B3-027/T-B10-015n`
- Method: `b3_b10_f1_h2o_shard_batch_gate_v0`
- Status: `h2o_full_covariance_shard_batch_recorded_zero_credit`
- H2O shard batch hash: `c62e2dc04d15511319ee3f8d805ef70ea24f30a68408b68d6683f88550e723b5`
- H2O shards: 7/7
- Global shards: 7/65

## Result

The gate records a complete H2O shard batch for the F1 route. It passes 7/10 requirements and intentionally fails ['P8', 'P9', 'P10'] because LiH/N2 shards, assembled rows, and the accepted four-row F1 artifact do not exist yet.

## H2O Batch Metrics

- Compiled cover groups: 3130
- Planning proxy groups: 3129
- Nonzero covariance pairs: 15099
- Variance sum: 30.157555924962423
- Remaining global shards: 58

## Requirements

- `P1` PASS: Work-order gate is current and recognizes the worker
- `P2` PASS: All expected H2O shard files exist
- `P3` PASS: Every H2O shard was produced by the full-covariance worker
- `P4` PASS: H2O shards form one contiguous compiled QWC cover
- `P5` PASS: Shard hashes are stable
- `P6` PASS: Required worker hashes are present on every shard
- `P7` PASS: Claim boundaries preserve zero credit
- `P8` FAIL: All 65 global F1 shard outputs have been produced
- `P9` FAIL: LiH/H2O/N2 rows are assembled from all shards
- `P10` FAIL: Four-row F1 artifact is accepted

## Claim Boundary

- Supported: All seven H2O compiled-state full-covariance shard outputs exist and form one contiguous compiled QWC cover.
- Not supported: This is not an assembled F1 row, not a LiH/N2 result, not a four-row F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.
