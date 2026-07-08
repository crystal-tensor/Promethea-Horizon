# B1/B7 Cone01 R25 O3-F4 Adversarial Refit Sentinel Gate

- Target: `T-B1-004ea/T-B7-013j`
- Upstream target: `T-B1-004dz/T-B7-013i`
- Method: `b1_b7_cone01_r25_o3_f4_adversarial_refit_sentinel_gate_v0`
- Status: `cone01_r25_o3_f4_adversarial_refit_sentinel_rejected`
- Candidate: `NL-C02`
- Family: `O3-F4`
- Sentinel hash: `96ed0ecf3b9763894fd624c8406bf820e0ab6416affad9d1f2d22ebcc51b380b`
- Fixture hash: `3826f9c90899a4b47add556136aa82648080fe7ac04ca1bd4bc4e05dccb4ed30`
- Preflight hash: `1d984523ff0cb0055f6ab8a5c05394a7e554ab0c96f47cb94fcc215858e82329`

## Result

R25 passes 11/11 requirements. It proves the R24 O3-F4 harness rejects a field-complete adversarial numerical refit overclaim.

## Rejection Profile

- Passed gates: `['F4-A1', 'F4-A3']`
- Failed gates: `['F4-A2', 'F4-A4', 'F4-A5', 'F4-A6', 'F4-A7', 'F4-A8', 'F4-A9']`
- Max unitary replay error: `0.008`
- Unit tolerance: `1e-08`

## Requirement Results

- `Q1` PASS: R24 harness is validation-clean and ready
- `Q2` PASS: Fixture carries all required O3-F4 fields
- `Q3` PASS: Fixture is bound to the R24 harness and challenge packet
- `Q4` PASS: Same-unitary replay failure is detected
- `Q5` PASS: Numerical-only lattice and missing denominator evidence are detected
- `Q6` PASS: Route-A self-assertion and hidden optimizer leakage are detected
- `Q7` PASS: Claim-boundary overreach and missing machine-check binding are detected
- `Q8` PASS: Failed gate set matches the expected adversarial rejection profile
- `Q9` PASS: R25 rejects the fixture without accepting O3-F4, closing O3, or permitting reroute
- `Q10` PASS: R25 preserves zero B7/resource credit claims
- `Q11` PASS: Sentinel packet is internally hash-bound

## Claim Boundary

- Supported: R25 emits a field-complete adversarial O3-F4 numerical refit fixture and proves the R24 harness rejects it on same-unitary replay, Route A self-assertion, numerical-only lattice evidence, denominator omission, optimizer leakage, claim-boundary overreach, and missing machine-check binding.
- Not supported: R25 does not submit or accept a valid O3-F4 refit artifact, does not close O3, and does not permit R5 reroute. No R1 solution, occurrence removal, proxy-T reduction, B7 credit, resource saving, or impossibility theorem is supported.
- Next gate: Submit a valid O3-F4 refit artifact that passes F4-A1..F4-A9, harden the harness against a stronger adversarial fixture, or return to O3-F3 symbolic proof / O3-F5 Route A pressure.

This sentinel gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.

## Validation

- validation_error_count: `0`
