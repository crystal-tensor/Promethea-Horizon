# B4/B8 R158 VF2 Accelerator-Boundary Result

- Status: `vf2_accelerator_boundary_diagnostic_complete`
- Profiles / processes / direct calls: `4` / `4` / `256`
- Classification: `internal_error_map_boundary`
- Fully shared profile outcome: `collapse`
- Aggregate mapping counts: `{'endpoint_4_to_0': 180, 'endpoint_4_to_2': 76, 'other_mapping': 0, 'no_solution': 0}`
- Simulation executions / shots: `0` / `0`
- Conditions passed/failed: `10` / `0`
- Requirements passed/failed: `10` / `0`

## Profile Distributions

| Profile | A | B | Other | No solution | Outcome | DAG/config/map identities |
|---|---:|---:|---:|---:|---|---|
| `python_pass_fresh_dag_fresh_config_internal_error_map` | 46 | 18 | 0 | 0 | `variation` | 64/0/0 |
| `accelerator_fresh_dag_fresh_config_internal_error_map` | 36 | 28 | 0 | 0 | `variation` | 64/64/0 |
| `accelerator_shared_dag_shared_config_internal_error_map` | 34 | 30 | 0 | 0 | `variation` | 1/1/0 |
| `accelerator_shared_dag_shared_config_shared_error_map` | 64 | 0 | 0 | 0 | `collapse` | 1/1/1 |

## Interpretation

The staged boundary classification is internal_error_map_boundary; this localizes a reconstruction layer but does not identify a lower-level mechanism.

## Claim Boundary

This result localizes a call boundary only. It does not identify candidate enumeration, hash-state, iterator order, floating-point accumulation, or last-improvement retention as the mechanism. It does not claim a confirmed Qiskit bug, general compiler determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit.
