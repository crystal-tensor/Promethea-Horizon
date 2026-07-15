# B1/B7 Cone01 R74 Grid Scaffold Pressure Gate

- Method: `b1_b7_cone01_r74_grid_scaffold_pressure_gate_v0`
- Status: `cone01_r74_grid_scaffold_no_exact_candidate_pressure_boundary`
- Requirements: `8/8`
- Grid: `k*pi/4`, k in `[0, 1, 2, 3, 4, 5, 6, 7]`
- Mixed orientation sequences per packet: `15`
- Optimizer attempts: `90`
- Strict exact candidates: `0`
- Best residual by packet: `[0.7803612880646379, 0.6724979699119589, 0.7653668647301796]`
- Best sequence by packet: `['01-01', '01', '10']`
- Accepted occurrence removal / proxy-T reduction: `0` / `0`
- B7 credit: `0`

## Interpretation

The finite grid pressure test found no strict exact reduced-CNOT candidate after replacing arbitrary local-U3 angles with pi/4-grid angles. This does not prove that a Clifford+T circuit cannot exist; it says the tested mixed-direction grid scaffolds did not reveal one under the declared seeds and optimizer budget.

## Claim Boundary

- This is a seeded finite discrete optimization pressure test, not an exhaustive Clifford+T search.
- No full-circuit rewrite, occurrence removal, proxy-T reduction, reroute, or B7 credit is accepted.
