# B1/B7 R76 Line-1378 Full-Circuit Replay Gate

- Method: `b1_b7_cone01_r76_line1378_full_circuit_replay_gate_v0`
- Status: `cone01_r76_line1378_full_circuit_replay_and_ft_ledger_passed_pending_b7_acceptance`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- R75 source window: lines `1369-1377` for target packet line `1378`

## Candidate

- QASM2: `results/B1_B7_cone01_R76_line1378_grid_candidate/gcm_h6_line1378_grid_candidate.qasm`
- QASM3: `results/B1_B7_cone01_R76_line1378_grid_candidate/gcm_h6_line1378_grid_candidate_openqasm3.qasm`
- Source/candidate CNOT count: `795` / `792`; delta `3`
- Candidate operation counts without measurements: `{'cx': 792, 'rz': 606, 'u3': 482}`
- QASM2/QASM3 counts preserved: `True`

## Replay

- Cases: `9` full-circuit cases, including `8` seeded product states, plus one QASM3 default-input case
- Replay passed: `True`
- Minimum fidelity / maximum infidelity: `0.9999999999999398` / `6.017408793468348e-14`
- Maximum phase-aligned amplitude / probability delta: `4.973249812319541e-16` / `6.245004513516506e-17`
- Failed cases: `[]`

## FT Ledger

- Source/candidate logical T ledger: `6760` / `6756`
- Source/candidate logical T depth: `1018` / `1018`
- Source-minus-candidate ledger deltas: `{'operation_count_scanned': 4, 'logical_t_count_ledger': 4, 'logical_t_depth_ledger': 0, 'rotation_component_count': -3}`
- Candidate rotation families: `{'arbitrary_numeric_rotation': 289, 'clifford_rotation': 811, 'exact_pi_over_4_rotation': 944, 'exact_pi_over_8_rotation': 8}`

## Claim Boundary

The fixed R75 line-1378 pi/4-grid witness can be emitted into the complete gcm_h6 source circuit, parsed as OpenQASM 2 and 3, and matches the source on the declared full-circuit replay suite to numerical tolerance. The conservative proxy FT ledger delta is reported but not promoted to B7 credit.

- This is not a symbolic full-Hilbert-space unitary proof.
- This is not an accepted B7 occurrence-removal certificate.
- The proxy FT ledger is not a physical fault-tolerant layout result.
- No patent, publication, funding, or product claim follows from this gate.

Accepted full-circuit replay artifact: `1`; accepted occurrence removal, proxy-T reduction, symbolic equivalence, and B7 credit: `0`.
