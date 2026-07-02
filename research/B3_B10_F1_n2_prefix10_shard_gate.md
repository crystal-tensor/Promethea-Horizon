# B3/B10 F1 N2 10-Shard Prefix Gate

- Target: `T-B3-029/T-B10-015p`
- Method: `b3_b10_f1_n2_prefix10_shard_gate_v0`
- Status: `n2_full_covariance_ten_shard_prefix_recorded_zero_credit`
- N2 10-prefix batch hash: `9eb2055bf0db8bd889920bcb609f2dbfa4206e026fe87515ab2b2dff7a326555`
- N2 prefix shards: 10/19
- Global shards: 17/65

## Result

The gate records the first ten N2 shard outputs for the F1 route. It passes 7/10 requirements and intentionally fails ['P8', 'P9', 'P10'] because the rest of N2, all LiH shards, assembled rows, and the accepted four-row F1 artifact do not exist yet.

## N2 Prefix Metrics

- Prefix groups: 5120
- Compiled cover groups: 9476
- Planning proxy groups: 9475
- Nonzero covariance pairs: 36132
- Variance sum: 51.56604411639643
- Remaining global shards: 48

## Requirements

- `P1` PASS: Work-order gate is current and recognizes the worker
- `P2` PASS: All expected N2 10-prefix shard files exist
- `P3` PASS: Every N2 prefix shard was produced by the full-covariance worker
- `P4` PASS: N2 prefix shards form one contiguous compiled QWC prefix
- `P5` PASS: N2 10-prefix shard hashes are stable
- `P6` PASS: Required worker hashes are present on every prefix shard
- `P7` PASS: Claim boundaries preserve zero credit
- `P8` FAIL: All 65 global F1 shard outputs have been produced
- `P9` FAIL: LiH/H2O/N2 rows are assembled from all shards
- `P10` FAIL: Four-row F1 artifact is accepted

## Claim Boundary

- Supported: The first ten N2 compiled-state full-covariance shard outputs exist and form a contiguous compiled QWC prefix.
- Not supported: This is not a complete N2 shard batch, not an assembled F1 row, not a LiH result, not a four-row F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.
