# B1/B7 Cone01 R47 O3-F4 C2 Source-Backed Discriminator Rerun Gate

- Target: `T-B1-004ew/T-B7-014f`
- Upstream target: `T-B1-004ev/T-B7-014e`
- Method: `b1_b7_cone01_r47_o3_f4_c2_source_backed_discriminator_rerun_gate_v0`
- Status: `cone01_r47_o3_f4_c2_source_backed_discriminator_rerun_rejects_flags_only`
- Fixture hash: `7665b3e23fe6663f2c4335a11b53ef0c9b5bb0bad9716cf0eb200f09274d5cbe`
- Discriminator hash: `b4db0ab566bad93fa2baba3d700e7a512a19a2d115bc7c8d35e1aa048faf4e98`

## Result

R47 passes 8/8 requirements by rerunning the source-backed discriminator after R46. All 8 rows now clear the prerequisite evidence layers, but all 8 remain rejected at the final source-backed flag layer.

## Rejection Surface

- Prerequisite-clean rows: `8`
- Source-provenance failures: `0`
- Witness-schema failures: `0`
- Binding mismatch count: `0`
- Source-backed rows passed: `0`
- Source-backed flag failures: `8`
- Flags-only rejection rows: `8`
- C2 accepted: `False`

## Requirement Results

- `S1` PASS: R46 source bundle is validation-clean and all-row preflight complete
- `S2` PASS: R47 reruns the source-backed discriminator on the R46 all-row fixture
- `S3` PASS: All prerequisite evidence classes now pass before the final source-backed flags
- `S4` PASS: Every row is rejected only at the source-backed replay and acceptance flag layer
- `S5` PASS: R47 preserves C2/O3/reroute/B7 zero-credit boundaries
- `S6` PASS: R47 declares the exact evidence needed before any smoke flag can flip
- `S7` PASS: R47 claims no C3-C7, reroute, occurrence-removal, or B7 ledger progress
- `S8` PASS: R47 output is hash-bound

## Claim Boundary

- Supported: R47 reruns the source-backed discriminator on the R46 all-row fixture and shows that materialization, provenance, witness schema, replay distance, binding, and zero-credit boundary checks are now clean for all 8 rows.
- Not supported: R47 still rejects every row because source-backed replay and same-unitary acceptance flags remain false while smoke-only flags remain true. It does not accept C2, close O3, allow reroute, or grant B7/STV credit.
- Next gate: Replace smoke-only flags with externally source-backed replay evidence and real verifier-backed same-unitary certificates for all 8 rows, then rerun this discriminator before C3-C7.

- validation_error_count: `0`
