# B1/B7 Cone01 R114 Qiskit Level Sweep Gate

## Summary

- Target: `T-B1-004hl/T-B7-016u`
- Upstream target: `T-B1-004hk/T-B7-016t`
- Method: `b1_b7_cone01_r114_qiskit_level_sweep_gate_v0`
- Status: `cone01_r114_level_sweep_proves_2q_reduction_unaccepted`
- Model status: `first_nonzero_2q_reduction_fails_exact_equivalence`
- Source workload: `benchmarks/qasmbench_medium_exact/gcm_h6.qasm`
- Accepted level with nonzero 2Q reduction: `None`

## Sweep

- Level `0`: CX `762`, exact `1/0`, fidelity `0.9999999999999996`
- Level `1`: CX `762`, exact `1/0`, fidelity `1.0`
- Level `2`: CX `528`, exact `0/1`, fidelity `0.4999999999999999`
- Level `3`: CX `528`, exact `0/1`, fidelity `0.4999999999999999`

Level 0 and level 1 preserve exact equivalence but keep the source CX count.
Level 2 and level 3 reduce CX from 762 to 528, but both fail exact equivalence
with fidelity 0.5. The first apparent two-qubit win is therefore rejected.

## Requirements

- `P1` PASS: all four optimization levels are materialized
- `P2` PASS: level 0 and level 1 pass exact equivalence without 2Q reduction
- `P3` PASS: level 2 and level 3 show the apparent 2Q reduction
- `P4` PASS: every nonzero 2Q reduction fails exact equivalence
- `P5` PASS: failed candidates keep counters and B7 credit at zero
- `P6` PASS: fidelity and phase-adjusted error are recorded
- `P7` PASS: same workload and denominator are retained across the sweep
- `P8` PASS: claim boundary rejects apparent 2Q progress without semantics

## Claim Boundary

R114 does not claim that every Qiskit optimization is invalid. It records this
workload-specific sweep and rejects every candidate with a nonzero 2Q reduction
until a stronger semantic certificate is supplied. No B7 credit is granted.
