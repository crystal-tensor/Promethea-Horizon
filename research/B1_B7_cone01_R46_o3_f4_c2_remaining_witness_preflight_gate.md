# B1/B7 Cone01 R46 O3-F4 C2 Remaining Witness-Preflight Gate

- Target: `T-B1-004ev/T-B7-014e`
- Upstream target: `T-B1-004eu/T-B7-014d`
- Method: `b1_b7_cone01_r46_o3_f4_c2_remaining_witness_preflight_gate_v0`
- Status: `cone01_r46_o3_f4_c2_remaining_witness_preflight_bound_rejected`
- Fixture hash: `7665b3e23fe6663f2c4335a11b53ef0c9b5bb0bad9716cf0eb200f09274d5cbe`
- Evaluation hash: `f2ab073dad9f63d0d592a3901b38b19d3741225ac25ea5f9b915c7a109cd478b`

## Result

R46 passes 8/8 requirements by binding executable preflights for all 8 rows while keeping C2 rejected.

## Rejection Surface

- Newly bound rows: `7`
- Witness-preflight rows passed: `8`
- Source-backed rows passed: `0`
- Source-backed flag failures: `8`
- C2 accepted: `False`

## Requirement Results

- `S1` PASS: R45 witness-schema gate is validation-clean
- `S2` PASS: R46 binds executable preflights for all 8 rows
- `S3` PASS: R46 preserves source-backed acceptance blocker
- `S4` PASS: All materialized/provenance/schema/distance files remain hash-valid
- `S5` PASS: R46 does not claim source-backed replay or same-unitary acceptance
- `S6` PASS: R46 keeps C2/O3/reroute/B7 zero-credit boundaries
- `S7` PASS: R46 claims no C3-C7 or ledger progress
- `S8` PASS: R46 output is hash-bound

## Claim Boundary

- Supported: R46 adds executable witness-preflight transcripts and command manifests for the 7 rows that lacked them after R45.
- Not supported: R46 does not mark any row source-backed, does not accept C2, does not close O3, and does not permit reroute, B7 credit, STV credit, or resource-saving claims.
- Next gate: Rerun the source-backed discriminator against the all-row provenance/schema/preflight/distance bundle, then replace smoke flags only if real source-backed replay evidence exists.

- validation_error_count: `0`
