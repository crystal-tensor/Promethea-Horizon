# B1/B7 cone_01 OpenQASM 3 Qiskit-Loader Linear-Span Replay Certificate Gate

- Method: `b1_b7_cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_gate_v0`
- Status: `cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_passed`
- Model status: `qiskit_loader_openqasm3_has_six_dimensional_linear_span_certificate_without_b7_credit`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Supported claim: The Qiskit-loaded OpenQASM 3 candidate has a tolerance-bounded six-dimensional finite linear-span replay certificate under the zero-input global phase anchor.

## Inputs

- Project-local linear-span gate: `results/B1_B7_cone01_openqasm3_linear_span_replay_certificate_gate_v0.json`
- Qiskit-loader global-phase gate: `results/B1_B7_cone01_openqasm3_qiskit_loader_global_phase_subspace_replay_gate_v0.json`
- OpenQASM 3 candidate: `results/B1_B7_cone01_openqasm3_candidate_export_gate/gcm_h6_line268_line1381_candidate_openqasm3.qasm`

## Loader Evidence

- Qiskit / qiskit-qasm3-import / openqasm3 versions: 2.4.1 / 0.6.0 / 1.0.1
- Qubits / clbits / depth: 19 / 1 / 1483
- Operation counts: {'cx': 789, 'rz': 601, 'u': 487, 'measure': 1}

## Linear-Span Certificate

- Global phase anchor: `zero` / `-2.4388324596671658` radians
- Certified input subspace dimension: 6 of 524288
- Certified input subspace fraction: 1.1444091796875e-05
- Linear-span spectral / Frobenius error: 2.7889440543898627e-13 / 6.134324404657074e-13
- Max basis L2 / amplitude / probability delta: 2.534056605707275e-13 / 1.3928889642636009e-13 / 7.771561172376096e-16
- Max source-candidate Gram / cross-Gram delta: 1.9984014443252818e-15 / 4.403624367368429e-14
- Source / Qiskit CNOT count / delta: 795 / 789 / 6
- Accepted Qiskit-loader parse / replay / global-anchor / linear-span artifacts: 1 / 1 / 1 / 1
- Accepted occurrence / proxy-T reduction / B7 claim: 0 / 0 / False

## Basis Rows

| Basis anchor | L2 error | Max amplitude delta | Max probability delta |
|---|---:|---:|---:|
| `zero` | `2.530297162857099e-13` | `1.3908205762322243e-13` | `5.551115123125783e-16` |
| `x_q0` | `2.530297162857099e-13` | `1.3908205762322243e-13` | `5.551115123125783e-16` |
| `x_q4` | `2.475576832682269e-13` | `1.3890629129730257e-13` | `4.996003610813204e-16` |
| `x_q14` | `2.534056605707275e-13` | `1.3928889642636009e-13` | `4.996003610813204e-16` |
| `x_q0_q4` | `2.475576832682269e-13` | `1.3890629129730257e-13` | `4.996003610813204e-16` |
| `x_q4_q14` | `2.479258809985556e-13` | `1.3920569169236498e-13` | `7.771561172376096e-16` |

## Claim Boundary

- This is a six-dimensional finite-subspace certificate, not full-space equivalence.
- This is not a symbolic exact full-circuit unitary proof.
- This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.
- This does not recover the dropped line-1378 overlap delta.
- This does not improve the B7 resource ledger.

## Validation

- Qiskit-loader linear-span certificate passed: True
- Validation errors: 0
