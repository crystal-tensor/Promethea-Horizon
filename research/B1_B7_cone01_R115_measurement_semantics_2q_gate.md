# B1/B7 Cone01 R115 Measurement-Semantics 2Q Gate

## Summary

- Target: `T-B1-004hm/T-B7-016v`
- Upstream target: `T-B1-004hl/T-B7-016u`
- Method: `b1_b7_cone01_r115_measurement_semantics_2q_gate_v0`
- Status: `cone01_r115_measurement_semantics_2q_accepted_full_state_rejected`
- Model status: `fixed_initial_state_final_measurement_scope_accepts_2q_reduction`
- Source CX count: `762`
- Candidate CX count: `528`
- CX reduction: `30.7087%`
- Full-state equivalence: `0/1`
- Final measurement-distribution equivalence: `1/0`
- Measurement L1 delta: `3.885780586188048e-15`
- B7 credit: `0`

R115 resolves the R114 ambiguity with two certificates. The level-2 candidate
fails the stronger arbitrary/full-state check with fidelity 0.5, but preserves
the source circuit's final classical measurement distribution to numerical
tolerance. It is accepted only for the explicitly scoped fixed-initial-state,
final-measurement B1 task; it is not an arbitrary-input or B7 result.

## Requirements

- `P1` PASS: candidate has a nonzero two-qubit reduction
- `P2` PASS: full-state equivalence remains rejected
- `P3` PASS: final measurement distribution passes exact numerical tolerance
- `P4` PASS: acceptance is explicitly scoped to fixed initial state and final measurement
- `P5` PASS: B7 credit remains zero despite scoped B1 acceptance
- `P6` PASS: all checker outputs are materialized
- `P7` PASS: measurement error is within 1e-8 tolerance
- `P8` PASS: claim boundary excludes arbitrary-input and hardware claims

## Claim Boundary

Supported: a 30.7087% CX reduction for this workload under the final measurement
distribution model. Not supported: arbitrary-input unitary equivalence,
full-state preservation, mid-circuit measurement semantics, hardware layout
improvement, T-resource reduction, or B7 credit.
