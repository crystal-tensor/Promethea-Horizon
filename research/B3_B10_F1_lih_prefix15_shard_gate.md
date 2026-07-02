# B3/B10 F1 LiH Prefix Shard Gate

- Target: `T-B3-033/T-B10-015t`
- Method: `b3_b10_f1_lih_prefix15_shard_gate_v0`
- Status: `lih_full_covariance_shard_prefix_recorded_zero_credit`
- LiH prefix batch hash: `c2fd3b1e256303a16c5c57a8e2c9bd449cde991ac63e18f331b7215cad282bb1`
- LiH prefix shards: 15/39
- Global shards: 41/65

## Result

The gate records the first 15 LiH shard outputs for the F1 route. It passes 7/10 requirements and intentionally fails ['P8', 'P9', 'P10'] because the rest of LiH, assembled rows, and the accepted four-row F1 artifact do not exist yet.

## LiH Prefix Metrics

- Prefix groups: 7680
- Compiled cover groups: 19645
- Planning proxy groups: 19644
- Nonzero covariance pairs: 74176
- Variance sum: 2.0338114794685707
- Remaining LiH shards: 24
- Remaining global shards: 24

## Requirements

- `P1` PASS: Work-order gate is current and recognizes the worker
- `P2` PASS: All expected LiH prefix shard files exist
- `P3` PASS: Every LiH prefix shard was produced by the full-covariance worker
- `P4` PASS: LiH prefix shards form one contiguous compiled QWC prefix
- `P5` PASS: LiH prefix shard hashes are stable
- `P6` PASS: Required worker hashes are present on every prefix shard
- `P7` PASS: Claim boundaries preserve zero credit
- `P8` FAIL: All 65 global F1 shard outputs have been produced
- `P9` FAIL: LiH/H2O/N2 rows are assembled from all shards
- `P10` FAIL: Four-row F1 artifact is accepted

## Claim Boundary

- Supported: The first 15 LiH compiled-state full-covariance shard outputs exist and form a contiguous compiled QWC prefix.
- Not supported: This is not a complete LiH shard batch, not an assembled F1 row, not a four-row F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.
