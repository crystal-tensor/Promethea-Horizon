# B3/B10 Reopen Blocker Queue Gate

Status: **b3_b10_reopen_blocker_queue_open_no_positive_route**

## Summary

- Method: b3_b10_reopen_blocker_queue_gate_v0
- Model status: failed_m5_m9_gates_partitioned_into_reopen_pr_packets
- Source failed gates: M5, M6, M7, M8, M9
- Requirements passed / failed: 5 / 0
- Reopen packet count: 5
- Row-aligned instances: 4
- Compiled pilot instances: 1
- Full compiled-state covariance computed: False
- Ansatz parameter count / converged state prep: 1 / False
- Selected-CI larger-basis denominator wins: 0
- Max optimizer-loop total shots lower bound: 475043013690000
- B10 still refutes current B3 access bridge: True
- B3 reopen ready: False
- Validation errors: []

## Queue Requirements

| Gate | Passed | Label | Acceptance rule |
|---|---:|---|---|
| Q1 | True | Source rescue gate is the current failed B3/B10 same-access gate | Queue must be built from the current M5-M9 failed rescue gate. |
| Q2 | True | Negative boundary note is satisfied and aligned | Negative boundary note must identify the same blocker set. |
| Q3 | True | Every failed M gate has exactly one PR packet | M5-M9 must map one-to-one to B3-R1 through B3-R5. |
| Q4 | True | Current blocker metrics remain negative | Do not reopen B3 while the current evidence still fails M5-M9. |
| Q5 | True | Forbidden claims remain absent | Queue artifact must not promote a demoted route into a positive claim. |

## Reopen Packets

### B3-R1-full-compiled-covariance

- Blocks gate: M5
- Owner role: chemistry_measurement_agent
- Downstream gate: rerun b3_b10_same_access_measurement_rescue_gate_v0
- Acceptance rule: M5 passes only if full_compiled_state_covariance_computed becomes true for all row-aligned molecules.
- Current evidence:
  - current_full_compiled_state_covariance_computed: False
  - current_compiled_pilot_instance_count: 1
  - row_aligned_instance_count: 4
- Required artifacts:
  - compiled-state covariance tables for all four B3 reaction-coordinate rows
  - state-preparation circuit provenance for every row
  - grouped observable variance/covariance ledger
  - derivative-level shot floor after covariance propagation
  - validation rows comparing sampled covariance against exact or high-confidence references

### B3-R2-multiparameter-converged-state-prep

- Blocks gate: M6
- Owner role: chemistry_state_prep_agent
- Downstream gate: rerun b3_b10_same_access_measurement_rescue_gate_v0
- Acceptance rule: M6 passes only if ansatz_parameter_count > 1 and converged_vqe_or_adapt_energy is true.
- Current evidence:
  - current_ansatz_parameter_count: 1
  - current_converged_vqe_or_adapt_energy: False
- Required artifacts:
  - multi-parameter UCCSD, ADAPT, VQE, or alternative ansatz specification
  - energy convergence evidence for each molecule row
  - two-qubit gate and preparation-repetition cost ledger
  - optimizer evaluation count and stopping criterion
  - negative-control comparison against the one-parameter pilot

### B3-R3-same-access-denominator-win

- Blocks gate: M7
- Owner role: baseline_adversary_agent
- Downstream gate: rerun B10 denominator boundary comparison and B3/B10 rescue gate
- Acceptance rule: M7 passes only if selected_ci_larger_basis_denominator_beaten_count is at least 1 under same-access accounting.
- Current evidence:
  - current_selected_ci_larger_basis_denominator_beaten_count: 0
- Required artifacts:
  - selected-CI/FCI or stronger classical denominator at the same active-space access level
  - quantum measurement and state-preparation costs charged on the same rows
  - row-level win/loss table after derivative and optimizer costs
  - independent reproduction script for the denominator comparison
  - explicit non-win rows retained rather than filtered out

### B3-R4-optimizer-loop-cost-collapse

- Blocks gate: M8
- Owner role: measurement_cost_agent
- Downstream gate: rerun b3_b10_same_access_measurement_rescue_gate_v0
- Acceptance rule: M8 passes only if max optimizer-loop shots fall below 1e12 under the same target error.
- Current evidence:
  - current_max_optimizer_loop_total_shots_lower_bound: 475043013690000
  - current_max_optimizer_loop_two_qubit_executions_lower_bound: 281225464104480000
- Required artifacts:
  - new measurement estimator or optimizer protocol reducing total shots
  - same target observable error and derivative propagation
  - optimizer-loop multiplier and evaluation-count evidence
  - two-qubit execution ledger after state-preparation costs
  - stress run proving the reduction is not a row-selection artifact

### B3-R5-b10-access-contract-acceptance

- Blocks gate: M9
- Owner role: theory_access_contract_agent
- Downstream gate: rerun B10 asymptotic access contract and B3/B10 rescue gate
- Acceptance rule: M9 passes only if B10 no longer refutes the B3 sampling/access bridge for current evidence.
- Current evidence:
  - current_b10_sampling_access_bridge_refuted: True
  - current_b3_demoted: True
- Required artifacts:
  - B10 same-access contract update consuming B3-R1 through B3-R4
  - explicit access model for sampling, state preparation, or oracle assumptions
  - proof-obligation note explaining what is and is not separated
  - negative-boundary cases where the access bridge still fails
  - claim-boundary update forbidding BQP or advantage claims without denominator wins

## Claim Boundary

- reopen_queue_built: True
- b3_reopen_ready: False
- positive_same_access_route_claimed: False
- reaction_dynamics_solution_claimed: False
- quantum_advantage_claimed: False
- bqp_separation_claimed: False
- what_is_supported: The B3/B10 failed M5-M9 gates are now partitioned into five PR-sized reopen packets with concrete artifacts and acceptance rules.
- what_is_not_supported: This queue does not add new chemistry evidence, does not reopen B3, and does not claim a reaction-dynamics solution, quantum advantage, or BQP separation.
