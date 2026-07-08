# B1/B7 Cone01 R37 O3-F4 C2 All-Row Materialized Smoke Gate

- Target: `T-B1-004em/T-B7-013v`
- Upstream target: `T-B1-004el/T-B7-013u`
- Method: `b1_b7_cone01_r37_o3_f4_c2_all_rows_materialized_smoke_gate_v0`
- Status: `cone01_r37_o3_f4_c2_all_rows_materialized_smoke_rejected`
- Fixture hash: `17b1a4e3e197ac838d636bcb52ca81a9001651758e1c306b97039b578eff32a6`
- Preflight hash: `4a469eadb38d952eb6168c55aee670c4122301478c44490badb831f1c86f5734`

## Result

R37 passes 8/8 requirements by materializing all 8 smoke rows while rejecting the bundle because 0 rows are source-backed.

## Rejection Surface

- Surface rows passed: `8`
- Materialized rows passed / failed: `8` / `0`
- Missing materialized files: `0`
- Smoke-only rows: `8`
- Source-backed rows passed: `0`
- C2 accepted: `False`

## Requirement Results

- `S1` PASS: R36 source smoke gate is validation-clean with exactly one materialized row
- `S2` PASS: R37 materializes all 8 rows with hash-matched files
- `S3` PASS: All 8 rows pass the metadata surface
- `S4` PASS: All 8 rows remain smoke-only and therefore are not C2 accepted
- `S5` PASS: Fixture and preflight are hash-bound
- `S6` PASS: R37 preserves zero-credit B1/B7 boundaries
- `S7` PASS: R37 does not claim same-unitary or source-backed replay evidence
- `S8` PASS: R37 remains scoped to materialization plumbing and claims no C3-C7 progress

## Claim Boundary

- Supported: R37 materializes all 8 C2 smoke rows with hash-matched files, closing the pure file-existence blocker.
- Not supported: R37 does not accept C2, does not provide source-backed replay outputs or same-unitary certificates, does not close O3, and does not permit reroute, B7 credit, STV credit, or resource-saving claims.
- Next gate: Replace each smoke row with source-backed replay output and same-unitary witness files before rerunning C2/C3-C7.

- validation_error_count: `0`
