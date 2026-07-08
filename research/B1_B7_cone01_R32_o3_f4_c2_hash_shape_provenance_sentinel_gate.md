# B1/B7 Cone01 R32 O3-F4 C2 Hash-Shape Provenance Sentinel

- Target: `T-B1-004eh/T-B7-013q`
- Upstream target: `T-B1-004eg/T-B7-013p`
- Method: `b1_b7_cone01_r32_o3_f4_c2_hash_shape_provenance_sentinel_gate_v0`
- Status: `cone01_r32_o3_f4_c2_hash_shape_fixture_rejected_unbound_provenance`
- Fixture hash: `7bb2708cedae88328e309bb5a7431f5d916cbbb9f284d532f1a4f532d2e73bc2`
- Fixture row-table hash: `5e7953521c3feb6209183eef6c20002532f2c111075db71e162d0e8dcf884e81`
- Preflight hash: `933d2689f1fb65a27db900da5b078594d18d438a0441012fbd3a09d8a80ffa0c`

## Result

R32 passes 8/8 requirements by rejecting a hash-shaped C2 fixture whose replay provenance is not bound to the rows.

## Sentinel Outcome

- Row count: `8`
- Tolerance pass count: `8`
- Hash shape pass: `True`
- Command shape pass: `True`
- Binding pass: `False`
- Binding mismatch count: `8`
- C2 accepted: `False`

## Requirement Results

- `S1` PASS: R31 source is validation-clean and fixture hash matches
- `S2` PASS: Hash-shape fixture preserves all 8 C2 rows and tolerance-passing errors
- `S3` PASS: All witness/circuit/stdout hashes have valid sha256 shape
- `S4` PASS: Replay commands have executable command shape
- `S5` PASS: Hash shape and command shape are rejected without provenance binding
- `S6` PASS: Fixture keeps C2, O3, reroute, and B7 credit unaccepted
- `S7` PASS: Fixture and preflight are hash-bound
- `S8` PASS: R32 remains scoped to C2 provenance and claims no C3-C7 progress

## Claim Boundary

- Supported: R32 proves sha256-shaped hashes and plausible replay commands are not enough for C2 acceptance unless the row's declared provenance binding hash matches the replay payload.
- Not supported: R32 does not accept C2, does not complete the certificate triad, does not close O3, and does not permit reroute, B7 credit, STV credit, or resource-saving claims.
- Next gate: Submit C2 rows whose provenance binding hashes are recomputable from challenge id, submitted parameters, replay error, circuit hashes, replay command, stdout hash, and verifier version.

- validation_error_count: `0`
