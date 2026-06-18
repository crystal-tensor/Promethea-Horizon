# B5 Canonical-Environment Smoke Gate v0.1

Status: **canonical_environment_smoke_gate_failed_not_production_dmrg**

## Summary

- Method: b5_canonical_environment_smoke_gate_v0
- Model status: posthoc_two_site_environment_diagnostics_not_canonical_solver
- Source result: results/B5_two_site_dmrg_response_reference_v0.json
- Instances: 9
- Environment ledger rows: 9
- Smoke-passed rows: 0
- Fixed-sector norm passed rows: 3
- Energy-variance passed rows: 3
- Discarded-weight passed rows: 3
- Energy-monotonicity passed rows: 3
- Response-close-to-seeded rows: 0
- Rows beating seeded MPS pressure: 0
- Rows beating variational MPS/ALS: 4
- Mean/max relative response error: 0.0819613 / 0.277103
- Min fixed-sector norm: 0.000434145
- Max relative discarded weight: 0.233708
- Mature canonical DMRG ready: False
- Validation errors: []

## Row Diagnostics

| sites | U/t | sweeps | norm | variance | max discarded | rel error | smoke pass | beats seeded | beats ALS |
|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 4 | 2.0 | 8 | 0.123385 | 3.55271e-15 | 0.0297838 | 5.73266e-09 | False | False | True |
| 4 | 4.0 | 8 | 0.0342578 | 3.02425e-13 | 0.0254724 | 1.21334e-07 | False | False | True |
| 4 | 8.0 | 8 | 0.0998231 | 1.77636e-15 | 0.00859849 | 1.83631e-08 | False | False | True |
| 6 | 2.0 | 8 | 0.00243197 | 0.567506 | 0.233708 | 0.0137544 | False | False | True |
| 6 | 4.0 | 8 | 0.0014649 | 0.547868 | 0.159409 | 0.0528165 | False | False | False |
| 6 | 8.0 | 8 | 0.000526249 | 0.577467 | 0.207116 | 0.166258 | False | False | False |
| 8 | 2.0 | 8 | 0.00142372 | 0.645957 | 0.190941 | 0.0543932 | False | False | False |
| 8 | 4.0 | 8 | 0.000839845 | 0.94463 | 0.116013 | 0.173326 | False | False | False |
| 8 | 8.0 | 8 | 0.000434145 | 1.79825 | 0.125477 | 0.277103 | False | False | False |

## Claim Boundary

- canonical_environment_smoke_diagnostics_built: True
- environment_ledger_from_two_site_prototype_used: True
- canonical_environment_solver_claimed: False
- production_dmrg_claimed: False
- quantum_response_win_claimed: False
- accuracy_per_resource_win_claimed: False
- same_access_positive_route_claimed: False
- what_is_supported: The existing two-site prototype now has a row-level smoke audit for environment ledger coverage, discarded-weight pressure, fixed-sector norms, energy variance, and response closeness.
- what_is_not_supported: This is a post-hoc diagnostic over a prototype, not a mature canonical-environment DMRG solver and not a B10 positive route.

## Next Gate

T-B5-006 must still implement an actual canonical-center finite-system
DMRG/MPS solver with stored left/right environments, orthonormal
residuals, convergence controls, no exact-state seeding, and full
sweep/matvec/memory cost accounting.
