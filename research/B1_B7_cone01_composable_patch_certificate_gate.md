# B1/B7 cone_01 Composable Patch Certificate Gate

- Method: `b1_b7_cone01_composable_patch_certificate_gate_v0`
- Status: `cone01_composable_patch_certificate_passed_without_b7_resource_credit`
- Model status: `nonoverlap_qasm2_candidate_has_tolerance_bounded_semantic_patch_certificate`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Source non-overlap subset: `results/B1_B7_cone01_nonoverlap_patch_subset_gate_v0.json`
- Source QASM2 candidate: `results/B1_B7_cone01_qasm2_candidate_rewrite_gate_v0.json`
- Source linear-span replay: `results/B1_B7_cone01_linear_span_replay_certificate_gate_v0.json`

## Result

- Tolerance-bounded full-circuit semantic certificate passed: `True`
- Selected lines: `[268, 1381]`
- Dropped overlap lines: `[1378]`
- Selected patch count: `2`
- All selected windows non-overlap: `True`
- All local-unitary certificates passed: `True`
- Max selected patch residual norm: `6.513210005207597e-13`
- Max selected patch entry error: `4.525273102184799e-13`
- Source/candidate CNOT count/delta: `795` / `789` / `6`
- Selected candidate CNOT reduction: `6`
- Selected off-grid local-U3 parameters: `5`
- Accepted replay certificate / QASM patch count: `1` / `1`
- Accepted occurrence / proxy-T reduction: `0` / `0`

## Claim Boundary

- This is a tolerance-bounded semantic patch certificate, not a symbolic exact proof.
- B7 resource credit remains 0 because line 1378 is still dropped and line 1381 retains unpriced off-grid local-U3 parameters.
- The next valid gate must recover line 1378, price or remove line-1381 off-grid parameters, or produce a different occurrence-removing route.
