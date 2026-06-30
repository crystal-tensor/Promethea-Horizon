# B5 W1 Production DMRG/MPS Denominator Engine v0.1

Status: **w1_denominator_engine_v0_failed_not_production_dmrg**

## Summary

- Method: `b5_production_dmrg_mps_denominator_v0`
- Row contract count/hash: 9 / `7ee407e20f51bd0c003d885c8d43282359f84bea9729f0da203b9b2c2970a9fc`
- Requirements passed/failed: 4 / 4
- Failed requirement IDs: ['E4', 'E5', 'E6', 'E7']
- Selected candidate family: variational_mps_als
- Convergence-passed rows: 0
- Rows beating seeded pressure: 0
- Mean candidate / seeded error: 0.0180555 / 0.000441626
- Production DMRG available: False

## Requirement Ledger

| ID | Requirement | Passed | Evidence |
| --- | --- | --- | --- |
| E1 | Locked B5/B10 row contract is preserved | True | row_count=9; row_contract_hash=7ee407e20f51bd0c003d885c8d43282359f84bea9729f0da203b9b2c2970a9fc; source_checks_failed=0 |
| E2 | A non-exact-state-seeded denominator candidate is executed | True | candidate_family=variational_mps_als; exact_state_seeded_rows=0 |
| E3 | All rows have sweep ledgers | True | min_sweep_ledger_rows=24 |
| E4 | Production canonical environments and residuals are present | False | stored_left_right_environments=False; orthonormal_residual_ledger_present=False; canonical_environment_production_dmrg=False |
| E5 | All nine rows pass convergence diagnostics | False | convergence_passed_rows=0; fixed_sector_norm_passed_rows=0; energy_variance_passed_rows=3; energy_monotonicity_passed_rows=6; discarded_weight_ledger_present=False |
| E6 | Candidate beats exact-state-seeded pressure on every row | False | rows_beating_seeded_pressure=0; mean_candidate_error=0.01805548365563228; mean_seeded_pressure_error=0.0004416259745141553 |
| E7 | Same-access production cost ledger is complete | False | wall_clock_costs_present=False; memory_costs_present=False; matvec_or_sweep_costs_complete=False; optimizer_loop_costs_complete=False |
| E8 | Forbidden claims remain false | True | production_dmrg_claimed=False; same_access_positive_route_claimed=False; quantum_advantage_claimed=False; bqp_separation_claimed=False |

## Row Ledger

| row | candidate | rel error | seeded rel error | norm pass | variance pass | monotonic pass | convergence pass | beats seeded |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 4|2 | variational_mps_als | 2.53641e-05 | 2.30892e-13 | False | True | False | False | False |
| 4|4 | variational_mps_als | 2.25111e-05 | 5.62853e-12 | False | True | False | False | False |
| 4|8 | variational_mps_als | 1.21915e-06 | 1.8114e-11 | False | True | False | False | False |
| 6|2 | variational_mps_als | 0.0167952 | 0.000997484 | False | False | True | False | False |
| 6|4 | variational_mps_als | 0.039072 | 0.000144526 | False | False | True | False | False |
| 6|8 | variational_mps_als | 0.032124 | 0.000440152 | False | False | True | False | False |
| 8|2 | variational_mps_als | 0.00475866 | 0.0016954 | False | False | True | False | False |
| 8|4 | variational_mps_als | 0.0359233 | 0.000682394 | False | False | True | False | False |
| 8|8 | variational_mps_als | 0.033777 | 1.46743e-05 | False | False | True | False | False |

## Claim Boundary

- what_is_supported: A first W1 denominator-engine ledger now selects and audits the strongest current non-exact-state-seeded tensor candidate under the locked nine-row B5/B10 contract.
- what_is_not_supported: This is not accepted production DMRG, not a canonical-environment implementation, not a seeded-pressure replacement, not a same-access positive route, not quantum advantage, and not a BQP separation.
- next_gate: Replace the v0 candidate with an actual canonical-environment DMRG/MPS solver that stores environments, passes 9/9 convergence diagnostics, and beats the seeded-pressure ladder.
- production_dmrg_claimed: False
- quantum_advantage_claimed: False
- bqp_separation_claimed: False

## Validation

- validation_error_count: 0
