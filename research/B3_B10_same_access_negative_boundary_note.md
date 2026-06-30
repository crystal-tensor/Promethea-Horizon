# B3/B10 Same-Access Negative Boundary Note

- Benchmark: `B3_B10`
- Method: `b3_b10_same_access_negative_boundary_note_v0`
- Status: `same_access_negative_boundary_note_not_advantage_claim`
- Source: `results/B3_B10_same_access_measurement_rescue_gate_v0.json`
- Conditions satisfied/unsatisfied: 9 / 0

## Decision

The current B3 measurement-rescue route remains demoted. This note does not claim that molecular reaction dynamics has no quantum route; it says the specific same-access route currently in the repository is not allowed to be promoted until the named blockers are replaced.

## Metrics

- passed_source_gate_count: 5
- failed_source_gate_count: 5
- failed_source_gate_ids: ['M5', 'M6', 'M7', 'M8', 'M9']
- row_aligned_instance_count: 4
- compiled_pilot_instance_count: 1
- cross_molecule_pressure_instance_count: 4
- selected_ci_larger_basis_denominator_beaten_count: 0
- max_optimizer_loop_total_shots_lower_bound: 475043013690000
- max_optimizer_loop_two_qubit_executions_lower_bound: 281225464104480000
- full_compiled_state_covariance_computed: False
- ansatz_parameter_count: 1
- converged_vqe_or_adapt_energy: False
- b10_sampling_access_bridge_refuted_for_current_evidence: True

## Boundary Conditions

| ID | Satisfied | Condition | Evidence | Reopen requirement |
| --- | --- | --- | --- | --- |
| N1 | yes | source rescue gate is the expected failed B3/B10 gate | method=b3_b10_same_access_measurement_rescue_gate_v0; status=same_access_measurement_rescue_failed_not_advantage_claim | Re-run the source gate with a new version if the upstream evidence changes. |
| N2 | yes | same-access rescue is explicitly not ready | same_access_measurement_rescue_ready=False | Set readiness true only after all same-access measurement gates pass. |
| N3 | yes | failed gate set identifies the exact blockers | failed_gate_ids=['M5', 'M6', 'M7', 'M8', 'M9'] | Replace M5-M9 with passing evidence or update the negative note with a new blocker set. |
| N4 | yes | full compiled-state covariance is missing | full_compiled_state_covariance_computed=False | Compute full compiled-state covariance, or a stronger bounded substitute, for every molecule row. |
| N5 | yes | state preparation remains one-parameter and unconverged | ansatz_parameter_count=1; converged_vqe_or_adapt_energy=False | Provide multi-parameter UCCSD/ADAPT/VQE or alternative chemistry state-preparation convergence evidence. |
| N6 | yes | selected-CI/FCI denominator wins are zero | selected_ci_larger_basis_denominator_beaten_count=0 | Produce at least one same-access denominator win after derivative and optimizer-loop costs. |
| N7 | yes | optimizer-loop shot floor is still prohibitive | max_optimizer_loop_total_shots_lower_bound=475043013690000 | Reduce optimizer-loop shot demand below the positive-route stress ceiling under the same target error. |
| N8 | yes | B10 access bridge still rejects the current evidence | b10_sampling_access_bridge_refuted_for_current_evidence=True | Update the B10 same-access contract only after B3 has full covariance, state-prep, denominator, and optimizer evidence. |
| N9 | yes | forbidden claims are all false | reaction_dynamics_solution_claimed=False; quantum_advantage_claimed=False; bqp_separation_claimed=False | Keep forbidden claims false until an independently reproduced same-access positive route exists. |

## Claim Boundary

- No molecular reaction dynamics solution is claimed.
- No quantum advantage is claimed.
- No BQP separation is claimed.
- No positive same-access B3 route is claimed.
- Reopen B3 only with full covariance, multi-parameter/converged state preparation, denominator wins, acceptable optimizer-loop costs, and B10 access-contract acceptance.
