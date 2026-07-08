# B1/B7 Cone01 R43 O3-F4 C2 All-Row Unitary-Distance Smoke Gate

- Target: `T-B1-004es/T-B7-014b`
- Upstream target: `T-B1-004er/T-B7-014a`
- Method: `b1_b7_cone01_r43_o3_f4_c2_all_rows_unitary_distance_smoke_gate_v0`
- Status: `cone01_r43_o3_f4_c2_all_rows_unitary_distance_smoke_computed_rejected`
- Fixture hash: `544e83b2ed5c72b6590595bd0925497bf4438a850dcbc841fba100d8763088d5`
- Evaluation hash: `969f78433eb87bbf1bc00d43279bb56035604ff01f27f3f3510a68fa957b6ed5`

## Result

R43 passes 8/8 requirements by computing all 8 smoke-row unitary-distance witnesses while keeping C2 rejected.

## Rejection Surface

- Materialized rows passed: `8`
- Source-provenance rows passed: `1`
- Witness-schema rows passed: `1`
- Witness-preflight rows passed: `1`
- Unitary-distance rows passed: `8`
- Unitary-distance failures: `0`
- Max computed unitary distance: `0.0`
- Source-backed rows passed: `0`
- Source-backed flag failures: `8`
- C2 accepted: `False`

## Requirement Results

- `S1` PASS: R42 single-row unitary-distance gate is validation-clean
- `S2` PASS: R43 computes unitary-distance witnesses for all 8 smoke rows
- `S3` PASS: R43 does not inflate provenance, schema, or preflight readiness
- `S4` PASS: All materialized C2 files remain hash-valid
- `S5` PASS: R43 does not claim source-backed replay or same-unitary acceptance
- `S6` PASS: R43 keeps C2/O3/reroute/B7 zero-credit boundaries
- `S7` PASS: R43 claims no C3-C7 or ledger progress
- `S8` PASS: R43 output is hash-bound

## Claim Boundary

- Supported: R43 computes hash-bound single-qubit RZ operator-norm unitary-distance smoke witnesses for all 8 C2 rows.
- Not supported: R43 does not mark any row source-backed, does not turn smoke distances into same-unitary certificates, does not accept C2, does not close O3, and does not permit reroute, B7 credit, STV credit, or resource-saving claims.
- Next gate: Replace smoke rows with real source-backed replay evidence, then add provenance, witness schema, and preflight packets for rows O3-F4-C02 through O3-F4-C08.

- validation_error_count: `0`
