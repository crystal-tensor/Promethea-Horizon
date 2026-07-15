# B1/B7 Cone01 R69 Source OpenQASM3 Prefill Gate

## Summary

- Status: `cone01_r69_source_openqasm3_export_prefill_refresh_zero_credit`
- Source OpenQASM3: `results/B1_B7_cone01_openqasm3_source_export_gate/gcm_h6_source_openqasm3.qasm`
- Source OpenQASM3 SHA256: `7bef92480635991093b10a23e2aa9b3e1a7f74a1a967c4e1546d70bbdb175312`
- R68 prefilled fields: `24` / 29
- R69 prefilled fields: `26` / 29
- Remaining placeholder fields: `3`
- Accepted exit routes: `0`
- Accepted occurrence removal: `0`
- Accepted proxy-T reduction: `0`
- B7 nonzero retest allowed: `False`
- B7 credit delta: `0`
- R69 blocker queue hash: `28b3f8e5d43a20e9315db4d576f6043547980e05421c14b5112e16f9f9d77292`

R69 fills the source OpenQASM3 path/hash fields in the R1 line1381 prefill. The draft now has 26 of 29 fields filled, but it still lacks machine-check replay command/stdout/hash and still has zero occurrence/proxy-T delta.

## Requirements

- `S1` PASS: source QASM2 exists and is the original gcm_h6 source
- `S2` PASS: source OpenQASM3 export has modern header and declarations
- `S3` PASS: normalized source streams match across QASM2 and QASM3
- `S4` PASS: operation counts are preserved by dialect export
- `S5` PASS: R69 refresh fills exactly the source OpenQASM3 fields from R68
- `S6` PASS: R69 preserves zero-credit claim boundary
- `S7` PASS: remaining blocker queue names replay and positive-delta blockers
- `S8` PASS: R69 artifacts are hash-bound and written

## Remaining Placeholders

- `machine_check_replay_command`
- `machine_check_replay_stdout_path`
- `machine_check_replay_stdout_sha256`

## Claim Boundary

- Supported: R69 exports the original gcm_h6 source to OpenQASM3, verifies a matching normalized instruction stream, and fills the source OpenQASM3 fields in the R1 prefill.
- Not supported: R69 does not provide machine-check replay stdout, positive occurrence/proxy-T deltas, an accepted exit route, O3 closure, reroute permission, or B7 credit.
- Next gate: Add machine-check replay command/stdout/hash, then submit positive occurrence/proxy-T delta evidence.

## Artifacts

- `source_openqasm3`: `results/B1_B7_cone01_openqasm3_source_export_gate/gcm_h6_source_openqasm3.qasm`
- `refreshed_prefill`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R69-R1-line1381-prefill-source-openqasm3.json`
- `blocker_queue`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R69-remaining-exit-route-blocker-queue.json`
