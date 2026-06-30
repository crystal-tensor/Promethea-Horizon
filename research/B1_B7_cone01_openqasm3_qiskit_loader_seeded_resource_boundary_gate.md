# B1/B7 cone_01 OpenQASM 3 Qiskit-Loader Seeded Resource Boundary Gate

- Method: `b1_b7_cone01_openqasm3_qiskit_loader_seeded_resource_boundary_gate_v0`
- Status: `cone01_openqasm3_qiskit_loader_seeded_resource_boundary_no_b7_credit`
- Model status: `seeded_replay_evidence_does_not_clear_line1381_or_b7_ledger_boundary`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Supported claim: The Qiskit-loader seeded product-state replay evidence is accepted as semantic pressure, but it does not clear line-1381 local-U3 pricing, line-1378 overlap recovery, occurrence removal, or the B7 ledger refresh.

## Inputs

- Seeded product replay gate: `results/B1_B7_cone01_openqasm3_qiskit_loader_seeded_product_replay_gate_v0.json`
- Line-1381 pricing gate: `results/B1_B7_cone01_line1381_local_u3_pricing_gate_v0.json`
- Theta-sharing cost model gate: `results/B1_B7_cone01_theta_sharing_cost_model_gate_v0.json`
- Refreshed B7 ledger gate: `results/B1_B7_cone01_shared_theta_refreshed_b7_ledger_gate_v0.json`

## Decision

- Seeded replay passed / cases: `True` / `16`
- Seeded replay min fidelity / max probability delta: `0.9999999999999389` / `8.020927672047762e-16`
- Line-1381 off-grid local-U3 parameters / proxy-T pressure: `5` / `100`
- Line-1378 delta recovered: `False`
- Theta cost model accepted / pass / fail: `False` / `6` / `2`
- Refreshed B7 ledger accepts theta sharing: `False`
- Missing proxy-T ledger reduction for gcm_h6 1.20x: `600`
- Accepted occurrence / proxy-T reduction: `0` / `0`
- Accepted seeded resource-boundary artifact: `1`

## Resource Blockers

- `RB-01` line1381_off_grid_local_u3_pressure: current `5`, required `0`; passed `False`. Line 1381 still has five off-grid local-U3 parameters.
- `RB-02` line1378_overlap_delta_not_recovered: current `False`, required `True`; passed `False`. The dropped overlap line 1378 delta remains unrecovered.
- `RB-03` accepted_occurrence_removal: current `0`, required `30`; passed `False`. No occurrence-removing certificate is accepted by the B7 ledger.
- `RB-04` theta_cost_model_accepted: current `False`, required `True`; passed `False`. The shared-theta physical cost model is still rejected.
- `RB-05` refreshed_b7_ledger_accepts_theta_sharing: current `False`, required `True`; passed `False`. The explicit B7 ledger refresh rejects theta sharing as counted savings.

## Claim Boundary

- This does not claim arbitrary-input or symbolic equivalence.
- This does not price, eliminate, or absorb the line-1381 local-U3 parameters.
- This does not recover the dropped line-1378 overlap delta.
- This does not accept shared-theta reuse as a physical B7 saving.
- This does not reduce the B7 proxy-T ledger.

## Validation

- Resource boundary passed: `True`
- Validation errors: `0`
