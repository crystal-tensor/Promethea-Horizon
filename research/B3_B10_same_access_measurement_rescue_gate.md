# B3/B10 Same-Access Measurement Rescue Gate v0.1

- Status: same_access_measurement_rescue_failed_not_advantage_claim
- Method: b3_b10_same_access_measurement_rescue_gate_v0
- Source target: B10-T1
- Same-access gates passed / failed: 5 / 5
- Failed gate IDs: M5, M6, M7, M8, M9
- Measurement rescue ready: False
- B3 remains demoted: True
- Denominator wins: 0
- Max optimizer-loop shots lower bound: 475043013690000
- Validation errors: []

## Gate Table

| gate | pass | evidence | required next |
|---|---:|---|---|
| M1 Same molecule rows exist across grouped covariance, derivative, pressure, and FCI tables | True | grouped=4; derivative=4; pressure=4; fci=4 | Keep all future rescue attempts row-aligned across B3 and B10 denominator artifacts. |
| M2 Grouped covariance is represented rather than independent-term-only measurement | True | grouped_covariance_included=True; max_reduction=5.58305864065559 | Retain grouped covariance and compare against non-QWC or classical-shadow style alternatives. |
| M3 Derivative-level observable error propagation is included | True | derivative_error_propagation_included=True; max_inflation=10000.0 | Keep derivative error propagation inside every positive-route cost ledger. |
| M4 Compiled-state covariance pilot exists | True | compiled_covariance=True; instances=1 | Extend the compiled-state covariance from one pilot row to all reaction rows. |
| M5 Full cross-molecule compiled-state covariance exists | False | full_compiled_state_covariance_computed=False; sampled_pressure_rows=4 | Compute full compiled-state covariance or a stronger bounded substitute for every molecule. |
| M6 Multi-parameter or converged chemistry ansatz exists | False | ansatz_parameter_count=1; converged_vqe_or_adapt_energy=False | Move beyond the one-parameter UCC double seed and record convergence evidence. |
| M7 Selected-CI/FCI larger-basis denominator is beaten | False | selected_ci_larger_basis_denominator_beaten_count=0 | Produce at least one same-access denominator win after measurement, derivative, and optimizer costs. |
| M8 Optimizer-loop budget is below the positive-route stress ceiling | False | max_optimizer_loop_total_shots_lower_bound=475043013690000; max_optimizer_loop_two_qubit_executions_lower_bound=281225464104480000 | Reduce optimizer-loop shots by at least three orders of magnitude before reopening a positive claim. |
| M9 B10 access contract allows a current B3 sampling bridge | False | sampling_access_bridge_refuted_for_current_evidence=True; b3_demoted=True | Replace the current B3 sampling bridge with a same-access route that B10 no longer rejects. |
| M10 Forbidden claims remain absent | True | B3 grouped/derivative/cross advantage claims=False/False/False; B10 advantage/BQP=False/False | Keep forbidden claims absent until a same-access denominator win and theorem boundary exist. |

## Claim Boundary

- what_is_supported: B3 has row-aligned denominator pressure, grouped covariance, derivative propagation, and a one-row compiled covariance pilot, but the same-access measurement rescue fails.
- what_is_not_supported: This is not a molecular reaction dynamics solution, not a quantum advantage claim, not a BQP separation, and not a positive same-access B3 route.
- quantum_advantage_claimed: False
- bqp_separation_claimed: False
- reaction_dynamics_solution_claimed: False

## Next Required Artifacts

- full cross-molecule compiled-state covariance or stronger measurement estimator
- multi-parameter converged UCC/ADAPT/VQE or alternative chemistry state-prep evidence
- same-access denominator win after derivative and optimizer-loop costs
- B10 access-contract update showing the B3 sampling bridge is no longer refuted
