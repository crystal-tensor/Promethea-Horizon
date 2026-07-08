# B1/B7 Cone01 R57 O3-F4 C2 R47 Exact-One-Row Rerun Gate

- Target: `T-B1-004fg/T-B7-014p`
- Upstream target: `T-B1-004ff/T-B7-014o`
- Method: `b1_b7_cone01_r57_o3_f4_c2_r47_exact_one_row_rerun_gate_v0`
- Status: `cone01_r57_o3_f4_c2_r47_accepts_exact_one_row_zero_b7_credit`
- Selected challenge: `O3-F4-C01`
- R57 fixture hash: `d8c11f1daaedf3c6d434f4ebce92687a1795e008b15f76da1fc6139b79ba9936`
- R57 evaluation hash: `33b3749a7991a17ccf8b29697e08f204c145a485e5283c0ffa5d09c926ca4cff`
- R57 discriminator row hash: `c4bab44fe8e9c3499352fc9ed939f291810380a88ff744243f90760d331c711c`

## Result

R57 passes 8/8 requirements by accepting exactly one source-backed row at the R47 discriminator layer. Full C2 all-row closure and B7 credit remain blocked.

## R47 Evidence

- Row count: `1`
- Materialized rows passed: `1`
- Source-backed rows passed: `1`
- Source-backed flag failures: `0`
- Source provenance failures: `0`
- Witness schema failures: `0`
- Binding mismatch count: `0`
- R47 exact-one-row accepted: `True`
- Full contract all-8 accepted: `False`

## Requirement Results

- `S1` PASS: R56 is the upstream preflight gate and accepted exactly one row at R51
- `S2` PASS: R57 fixture is bound to the exact R56/R55 E3 replacement row
- `S3` PASS: R57 reuses the R38/R47 source-backed discriminator contract
- `S4` PASS: R57 row passes materialized files, source provenance, witness schema, binding, replay, and flags
- `S5` PASS: R57 accepts exactly one source-backed row at the R47 layer
- `S6` PASS: R57 does not promote exact-one-row acceptance into full C2/O3/reroute/B7 credit
- `S7` PASS: R57 leaves all-8-row scaling and C3-C7 gates open
- `S8` PASS: R57 fixture and evaluation are hash-bound

## Claim Boundary

- Supported: R57 reruns the R47/R38 discriminator on exactly the R56 preflight-passing C01 row and accepts one source-backed row at the discriminator layer.
- Not supported: R57 does not scale C2 to all 8 rows, does not close O3, does not permit reroute, and does not grant B7/STV/resource/ledger credit.
- Next gate: Scale the same R47 discriminator to all 8 rows before C3-C7 or any B7 ledger retest.

- validation_error_count: `0`
