# B4/B8 R157 VF2 Tie-Isolation Result

- Status: `vf2_tie_isolation_diagnostic_complete`
- Profiles / OS processes / direct replays: `5` / `98` / `160`
- Mapping classes observed: `2`
- Profile collapse / variation: `0` / `5`
- Other mappings / no solutions: `0` / `0`
- Simulation executions / shots: `0` / `0`
- Conditions passed/failed: `10` / `0`
- Requirements passed/failed: `10` / `0`

## Profile Distributions

| Profile | Processes | Replays | Mapping counts | Outcome |
|---|---:|---:|---|---|
| `native_target_independent_process` | 32 | 32 | endpoint_4_to_0=24, endpoint_4_to_2=8, other_mapping=0, no_solution=0 | `variation` |
| `canonical_ascending_independent_process` | 32 | 32 | endpoint_4_to_0=20, endpoint_4_to_2=12, other_mapping=0, no_solution=0 | `variation` |
| `canonical_descending_independent_process` | 32 | 32 | endpoint_4_to_0=19, endpoint_4_to_2=13, other_mapping=0, no_solution=0 | `variation` |
| `fresh_target_same_process` | 1 | 32 | endpoint_4_to_0=19, endpoint_4_to_2=13, other_mapping=0, no_solution=0 | `variation` |
| `shared_target_same_process` | 1 | 32 | endpoint_4_to_0=21, endpoint_4_to_2=11, other_mapping=0, no_solution=0 | `variation` |

## Interpretation

At least one frozen profile retains more than one mapping class; the direct-pass boundary remains profile-variable and requires a smaller enumeration-order reproducer before any mechanism attribution.

## Implementation-Smoke Disclosure

Five unretained implementation-smoke direct-pass invocations occurred after public preregistration and before the retained matrix while validating Qiskit property-set extraction and Target reconstruction. They exposed four endpoint_4_to_0 outcomes and one endpoint_4_to_2 outcome; the latter came from the descending-order Target. They are excluded from the 160-row matrix, no condition or analysis was changed, and R157 is not claimed as blinded confirmation.

The two preregistered mappings retain the exact independently recomputed score `0.45894321220828727`. All new mappings and no-solution rows, if any, remain in the distributions rather than being excluded.

## Claim Boundary

This direct-pass result reports profile associations only. It does not prove a lower-level process, hash, iteration, or Rust mechanism and does not claim a confirmed Qiskit bug, general compiler determinism, simulation or hardware performance, transfer, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.
