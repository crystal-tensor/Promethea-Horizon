# B1/B7 Cone01 R117 Independent NumPy Replay Gate

## Summary

- Target: `T-B1-004ho/T-B7-016x`
- Upstream target: `T-B1-004hn/T-B7-016w`
- Method: `b1_b7_cone01_r117_independent_numpy_replay_gate_v0`
- Status: `cone01_r117_independent_numpy_replay_30_probe_accepted`
- Model status: `independent_numpy_replay_matches_qiskit_finite_probe`
- Source CX count: `762`
- Candidate CX count: `528`
- CX reduction: `30.7087%`
- Independent NumPy probes: `30/30`
- Maximum fidelity deficit: `1.3322676295501878e-15`
- Measurement map preserved: `True`
- B7 credit: `0`

R117 replays the R116 source and candidate with a separate NumPy statevector
engine. It does not call Qiskit for compilation or simulation. The engine
parses the OpenQASM gate stream, applies independent U3/RZ/SX/X/CX kernels,
and checks 30 inputs: zero, 13 computational-basis states, 8 full random
states, and 8 random product states.

This is cross-implementation finite-probe evidence, not a mathematical proof
of arbitrary-input unitary equivalence. No hardware layout, T-resource, or B7
ledger credit is inferred.

## Requirements

- `P1` PASS: accepted R116 artifact is the input
- `P2` PASS: independent NumPy replay engine is used
- `P3` PASS: candidate has a nonzero two-qubit reduction
- `P4` PASS: all independent probes pass
- `P5` PASS: independent replay error stays within tolerance
- `P6` PASS: source measurement map is preserved
- `P7` PASS: source and candidate have the same qubit count
- `P8` PASS: independent probe output is materialized
- `P9` PASS: B7 credit remains zero
- `P10` PASS: claim boundary excludes arbitrary proof and hardware claims

## Claim Boundary

Supported: the R116 terminal-measurement-detached candidate survives an
independent NumPy replay over 30 recorded input states while preserving the
source measurement map and the `762 -> 528` CX reduction. Not supported:
arbitrary-input proof, mid-circuit measurement semantics, hardware layout
improvement, T-resource reduction, or B7 credit.
