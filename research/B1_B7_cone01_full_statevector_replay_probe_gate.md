# B1/B7 cone_01 Full-Statevector Replay Probe Gate

## Summary

- Method: `b1_b7_cone01_full_statevector_replay_probe_gate_v0`
- Status: `cone01_default_input_statevector_replay_probe_passed_not_symbolic_certificate`
- Source QASM: `results/b1_native_t_resource_optimizer/qasmbench_medium_exact/gcm_h6.qasm`
- Candidate QASM: `results/B1_B7_cone01_qasm2_candidate_rewrite_gate/gcm_h6_line268_line1381_candidate.qasm`
- Qubits / statevector dimension: `19` / `524288`
- Source / candidate operations without measurements: `1884` / `1877`
- Source / candidate CNOT count / delta: `795` / `789` / `6`
- State fidelity / infidelity: `0.9999999999999551` / `4.4853010194856324e-14`
- Max global-phase-aligned amplitude delta: `1.3908205762322243e-13`
- Max probability delta: `5.551115123125783e-16`
- Measured q[4] marginal delta: `5.551115123125783e-16`
- Replay probe passed: `True`
- Accepted full-circuit patch / replay / occurrence / proxy-T reduction: `0` / `0` / `0` / `0`
- Validation errors: `0`

## Claim Boundary

The T-B1-004av QASM2 candidate matches the source circuit on the benchmark default-input 19-qubit statevector after final measurements are removed.

Unsupported claims:

- This is not a symbolic unitary-equivalence proof for arbitrary input states.
- This is not an accepted B7 occurrence-removing certificate.
- This does not recover the dropped line-1378 overlap delta.
- This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.

## Interpretation

This is a stronger replay pressure gate than the structural QASM2 candidate emission: the candidate matches the source on the concrete benchmark initial state to numerical precision. It is still not a symbolic proof for arbitrary inputs and still cannot enter the B7 resource ledger until occurrence and local-U3 pricing obligations are satisfied.
