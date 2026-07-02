# B3/B10 F1 N2 Prefix Shard Gate

- Target: `T-B3-028/T-B10-015o`
- Method: `b3_b10_f1_n2_prefix_shard_gate_v0`
- Status: `n2_full_covariance_shard_prefix_recorded_zero_credit`
- N2 prefix batch hash: `7750a05575f517a8b2a25052baafea37c08ad0290bf84e678911cf05a17862cf`
- N2 prefix shards: 5/19
- Global shards: 12/65

## Result

The gate records the first five N2 shard outputs for the F1 route. It passes 7/10 requirements and intentionally fails ['P8', 'P9', 'P10'] because the rest of N2, all LiH shards, assembled rows, and the accepted four-row F1 artifact do not exist yet.

## N2 Prefix Metrics

- Prefix groups: 2560
- Compiled cover groups: 9476
- Planning proxy groups: 9475
- Nonzero covariance pairs: 29205
- Variance sum: 51.08685050230266
- Remaining global shards: 53

## Requirements

- `P1` PASS: Work-order gate is current and recognizes the worker
- `P2` PASS: All expected N2 prefix shard files exist
- `P3` PASS: Every N2 prefix shard was produced by the full-covariance worker
- `P4` PASS: N2 prefix shards form one contiguous compiled QWC prefix
- `P5` PASS: N2 prefix shard hashes are stable
- `P6` PASS: Required worker hashes are present on every prefix shard
- `P7` PASS: Claim boundaries preserve zero credit
- `P8` FAIL: All 65 global F1 shard outputs have been produced
- `P9` FAIL: LiH/H2O/N2 rows are assembled from all shards
- `P10` FAIL: Four-row F1 artifact is accepted

## Claim Boundary

- Supported: The first five N2 compiled-state full-covariance shard outputs exist and form a contiguous compiled QWC prefix.
- Not supported: This is not a complete N2 shard batch, not an assembled F1 row, not a LiH result, not a four-row F1 artifact, not a denominator win, not B3/B10 credit, and not quantum advantage.
