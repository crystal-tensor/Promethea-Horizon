# B4/B8 R164 Combine-Bound Comparison Shadow Audit

- Status: `comparison_policy_shadow_complete`
- Classification: `source_combine_bound_policy_differences_observed`
- Profiles / replays: `3` / `256`
- Source compare events / reconstructable events: `6912` / `6912`
- Disagreements against source: `{'source_f64': 0, 'compensated_fsum': 49, 'exact_binary64_leaf': 49, 'tie_aware_1ulp': 49}`
- Payload hash: `0462b54c2678102531e5f46ac4b10f220ee547b6d9f04636785a52d6509b70f8`

## Research Question

Can the source combine bit pattern bind every VF2 comparison operand strongly enough to expose policy-sensitive decisions?

## Method

R164 reads only the hash-bound R162 worker artifacts. It binds each compare operand by the pair of its source expression and the exact `combine.result_bits` emitted for that expression, then carries the retained binary64 leaves into four declared policies. No Qiskit call, candidate selection, route change, simulation, or shot is performed.

## Result

The audit bound `6912` of `6912` compare events. Disagreements against the source are `{'source_f64': 0, 'compensated_fsum': 49, 'exact_binary64_leaf': 49, 'tie_aware_1ulp': 49}`. The result is a comparison-level diagnostic only; it does not prove that any mapping would change under a production rerun.

## Profile Summary

| Profile | Replays | Source compares | Reconstructable | Source vs fsum | Source vs exact | Source vs tie-aware | Tie-aware ties |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ascending_sorted_order` | 64 | 1728 | 1728 | 0 | 0 | 0 | 64 |
| `descending_sorted_order` | 64 | 1728 | 1728 | 0 | 0 | 0 | 64 |
| `native_hashset_order` | 128 | 3456 | 3456 | 49 | 49 | 49 | 128 |

## Claim Boundary

This audit does not establish a confirmed Qiskit bug, a numerical fix, a changed mapping, cross-platform determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit. The combine-bound policy shadows are not a production recommendation.
