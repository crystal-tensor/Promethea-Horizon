# B1/B7 cone_01 OpenQASM 3 Qiskit-Loader Composable Patch Lift Support Gate

- Method: `b1_b7_cone01_openqasm3_qiskit_loader_composable_patch_lift_gate_v0`
- Status: `cone01_openqasm3_qiskit_loader_composable_patch_lift_supported_without_b7_credit`
- Model status: `qiskit_loader_openqasm3_candidate_supports_composable_patch_lift_via_finite_span_without_b7_credit`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Supported claim: The OpenQASM 3 composable patch-lift artifact is supported on the Qiskit-loader path by a passing loader parse, global-phase subspace replay, and six-dimensional finite linear-span certificate for the same candidate.

## Evidence Chain

- OpenQASM 3 patch-lift gate: `results/B1_B7_cone01_openqasm3_composable_patch_lift_gate_v0.json`
- Qiskit-loader finite-span gate: `results/B1_B7_cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_gate_v0.json`
- Qiskit-loader global-phase gate: `results/B1_B7_cone01_openqasm3_qiskit_loader_global_phase_subspace_replay_gate_v0.json`
- OpenQASM 3 candidate: `results/B1_B7_cone01_openqasm3_candidate_export_gate/gcm_h6_line268_line1381_candidate_openqasm3.qasm`

## Patch-Lift Evidence

- Normalized stream match / mismatches / length delta: True / 0 / 0
- Selected patches / lines / dropped-overlap lines: 2 / [268, 1381] / [1378]
- Non-overlap / local-unitary certificates: True / True
- Max selected patch residual / entry error: 6.513210005207597e-13 / 4.525273102184799e-13

## Qiskit-Loader Evidence

- Qiskit / qiskit-qasm3-import / openqasm3 versions: 2.4.1 / 0.6.0 / 1.0.1
- Qubits / clbits / depth / ops: 19 / 1 / 1483 / {'cx': 789, 'measure': 1, 'rz': 601, 'u': 487}
- Global-phase subspace replay passed: True
- Linear-span certificate passed: True
- Certified subspace / full input space: 6 / 524288
- Linear-span spectral error / max L2 / max probability delta: 2.7889440543898627e-13 / 2.534056605707275e-13 / 7.771561172376096e-16
- Accepted parse / global-phase / finite-span / patch-lift-support artifacts: 1 / 1 / 1 / 1
- Accepted occurrence / proxy-T reduction / B7 claim: 0 / 0 / False

## Claim Boundary

- This is support for the composable patch lift, not a full-space symbolic unitary proof.
- This is not arbitrary-input or full-Hilbert-space coverage.
- This does not recover the dropped line-1378 overlap delta.
- This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.
- This does not improve the B7 resource ledger.

## Validation

- Qiskit-loader patch-lift support passed: True
- Validation errors: 0
