# B1/B7 Cone01 R41 O3-F4 C2 Single-Row Witness Preflight Gate

- Target: `T-B1-004eq/T-B7-013z`
- Upstream target: `T-B1-004ep/T-B7-013y`
- Method: `b1_b7_cone01_r41_o3_f4_c2_single_row_witness_preflight_gate_v0`
- Status: `cone01_r41_o3_f4_c2_single_row_witness_preflight_executable_rejected`
- Fixture hash: `93cdfd2c153f052d28c1949e35a44e86a835d4c2ddab9d3859e42e079ff7437a`
- Evaluation hash: `507326bb8120b51b1d4c1ea8a7d8d598178b76f2faddab1c9ce52b1904e008d8`

## Result

R41 passes 8/8 requirements by adding one executable witness preflight while keeping C2 rejected.

## Rejection Surface

- Source-provenance rows passed: `1`
- Witness-schema rows passed: `1`
- Witness-preflight rows passed: `1`
- Witness-preflight failures: `7`
- Source-backed rows passed: `0`
- Source-backed flag failures: `8`
- C2 accepted: `False`

## Requirement Results

- `S1` PASS: R40 witness scaffold gate is validation-clean with one schema row
- `S2` PASS: R41 emits executable preflight transcript and command files for one row
- `S3` PASS: The row keeps source provenance and witness schema intact
- `S4` PASS: All materialized C2 files remain hash-valid
- `S5` PASS: R41 does not claim source-backed replay or same-unitary acceptance
- `S6` PASS: R41 keeps C2/O3/reroute/B7 zero-credit boundaries
- `S7` PASS: R41 claims no C3-C7 or ledger progress
- `S8` PASS: R41 output is hash-bound

## Claim Boundary

- Supported: R41 adds an executable witness preflight transcript and command manifest for one C2 row, reducing witness-preflight failures from 8 to 7 while preserving the R40 witness schema scaffold.
- Not supported: R41 does not compute unitary distance, does not turn the preflight into a same-unitary certificate, does not mark the row source-backed, does not accept C2, does not close O3, and does not permit reroute, B7 credit, STV credit, or resource-saving claims.
- Next gate: Replace the preflight transcript with an actual unitary-distance computation for O3-F4-C01, then replace smoke flags with source-backed replay flags only if that computation passes.

- validation_error_count: `0`
