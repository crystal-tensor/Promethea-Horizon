# B4/B8 R162 VF2 Score-Combination Trace

- Status: `score_trace_diagnostic_complete`
- Classification: `source_score_shadow_divergence_localized`
- Profiles / processes / replays: `3` / `3` / `256`
- Score events / strict comparisons / returned candidates: `44800` / `6912` / `256`
- Shadow classes: `{"no_candidate": 0, "source_differs_from_fsum": 141, "source_equals_fsum_but_exact_binary64_differs": 115, "source_equals_fsum_equals_exact_binary64": 0}`
- Requirements passed/failed: `10` / `0`
- Payload hash: `6d4d8a89101a63226bc669e9b24c65d8db3e9c58d61ed4c8ae74fea3ad5141ed`
- Source f64 total differs from `math.fsum`: `141/256` calls
- Source agrees with `math.fsum` but differs from the exact binary64-leaf sum: `115/256` calls
- Retained strict `Decreasing` comparisons: `6912`

## Research Question

At which retained event does the source-order binary64 score first diverge from compensated or exact-binary64-leaf arithmetic?

## Result

The returned source f64 score differs from the compensated fsum shadow on 141/256 calls; this is the earliest retained candidate-total divergence. Exact-binary64-leaf comparisons remain arithmetic shadows, not a source fix.

## Profile Summary

| Profile | Replays | Mapping counts | Shadow counts | Mean score events | Mean strict compares |
|---|---:|---|---|---:|---:|
| `native_hashset_order` | 128 | `{"endpoint_4_to_0": 79, "endpoint_4_to_2": 49, "no_solution": 0, "other_mapping": 0}` | `{"no_candidate": 0, "source_differs_from_fsum": 77, "source_equals_fsum_but_exact_binary64_differs": 51, "source_equals_fsum_equals_exact_binary64": 0}` | 175.00 | 27.00 |
| `ascending_sorted_order` | 64 | `{"endpoint_4_to_0": 64, "endpoint_4_to_2": 0, "no_solution": 0, "other_mapping": 0}` | `{"no_candidate": 0, "source_differs_from_fsum": 64, "source_equals_fsum_but_exact_binary64_differs": 0, "source_equals_fsum_equals_exact_binary64": 0}` | 175.00 | 27.00 |
| `descending_sorted_order` | 64 | `{"endpoint_4_to_0": 64, "endpoint_4_to_2": 0, "no_solution": 0, "other_mapping": 0}` | `{"no_candidate": 0, "source_differs_from_fsum": 0, "source_equals_fsum_but_exact_binary64_differs": 64, "source_equals_fsum_equals_exact_binary64": 0}` | 175.00 | 27.00 |

## Interpretation

The trace retains source operands and labels; the compensated and exact-binary64-leaf values are arithmetic shadows over those retained leaves. They do not replace Qiskit's source score, establish a bug, or prove a remedy.

## Claim Boundary

This diagnostic does not establish a confirmed Qiskit bug, a numerical fix, cross-platform determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.
