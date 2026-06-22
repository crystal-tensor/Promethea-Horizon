# B1/B7 cone_01 Union-Region Three-CNOT Pricing Screen Gate

- Method: `b1_b7_cone01_union_region_three_cnot_pricing_screen_gate_v0`
- Status: `cone01_union_region_three_cnot_pricing_screen_rejected`
- Model status: `three_cnot_union_candidates_do_not_price_better_than_current_boundary`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Union window: `[1369, 1379]`
- Support qubits: `[4, 8]`
- Orientation sequences: `['01-01-01', '01-01-10', '01-10-01', '01-10-10', '10-01-01', '10-01-10', '10-10-01', '10-10-10']`
- Three-CNOT exact sequences: `8`
- Best residual: `5.810128819011275e-13` on `10-01-10`
- Best exact sequence: `10-10-01`
- Best exact off-grid local-U3 parameters: `18`
- Best exact proxy-T pressure: `360`
- Current line-1381 proxy-T pressure: `100`
- Structurally dominates current line-1381 2-CNOT replacement: `False`
- Prices below current line-1381 boundary: `False`
- B7 ledger improvement claimed: `False`

## Claim Boundary

Within the tested all-direction 3-CNOT local-U3 scaffold family, this gate screens whether any local exact candidate prices below the current line-1381 5-parameter / 100-proxy-T boundary while also structurally dominating the current 2-CNOT replacement.

Unsupported claims:
- This is not a global CNOT/local-U3 lower-bound theorem.
- A local exact 3-CNOT candidate is not a full-circuit replay certificate.
- A 3-CNOT union candidate does not recover extra CNOT delta over the current 2-CNOT line-1381 replacement.
- This does not accept occurrence removal, proxy-T reduction, or a B7 ledger improvement.

## Sequence Rows

- `01-01-01`: exact `True`, residual `5.856738063205188e-13`, off-grid `20`, proxy-T `400`
- `01-01-10`: exact `True`, residual `5.823683977172051e-13`, off-grid `24`, proxy-T `480`
- `01-10-01`: exact `True`, residual `5.816283362553614e-13`, off-grid `19`, proxy-T `380`
- `01-10-10`: exact `True`, residual `5.832725183129295e-13`, off-grid `19`, proxy-T `380`
- `10-01-01`: exact `True`, residual `5.87678767233426e-13`, off-grid `20`, proxy-T `400`
- `10-01-10`: exact `True`, residual `5.810128819011275e-13`, off-grid `24`, proxy-T `480`
- `10-10-01`: exact `True`, residual `6.047584909121987e-13`, off-grid `18`, proxy-T `360`
- `10-10-10`: exact `True`, residual `5.832750206655702e-13`, off-grid `20`, proxy-T `400`
