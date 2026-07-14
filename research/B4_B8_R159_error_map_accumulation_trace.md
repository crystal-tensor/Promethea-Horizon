# B4/B8 R159 ErrorMap Accumulation Trace

- Status: `error_map_accumulation_trace_complete`
- Classification: `operation_order_f64_path_supported`
- Profiles / processes / traced calls: `3` / `3` / `256`
- Aggregate mapping counts: `{'endpoint_4_to_0': 199, 'endpoint_4_to_2': 57, 'other_mapping': 0, 'no_solution': 0}`
- Native order/error-bit hashes: `128` / `16`
- Native order->bits / bits->mapping functional: `True` / `True`
- Sorted profiles collapse: `True`
- Simulation executions / shots: `0` / `0`
- Conditions passed/failed: `10` / `0`
- Requirements passed/failed: `10` / `0`

## Profile Summary

| Profile | A | B | Other | No solution | Order hashes | Error-bit hashes | Outcome |
|---|---:|---:|---:|---:|---:|---:|---|
| `native_hashset_order` | 71 | 57 | 0 | 0 | 128 | 16 | `variation` |
| `ascending_sorted_order` | 64 | 0 | 0 | 0 | 1 | 1 | `collapse` |
| `descending_sorted_order` | 64 | 0 | 0 | 0 | 1 | 1 | `collapse` |

## Interpretation

Native HashSet order changes produce multiple average-error bit maps, each bit map predicts one tied mapping, and both sorted controls collapse. This supports the operation-order-to-f64-to-selection path in this instrumented build, without elevating it to a confirmed general bug claim.

The 16 native error-bit maps partition cleanly: 10 map only to
`endpoint_4_to_0` and 6 map only to `endpoint_4_to_2`. Ascending and descending
orders produce different fixed error-bit maps, but both select
`endpoint_4_to_0`. The evidence therefore supports a path through floating-point
accumulation and tie selection; it does not show that every bit-level ErrorMap
change must alter the selected layout.

## Preflight Binding Guard

The first post-registration launch stopped before loading the frozen R157 input
because Python resolved the globally installed accelerator with SHA-256
`a299d48f8d174481d389b30f1fd240a845144922f32ef918925b17243fc5f007`
instead of the preregistered instrumented binary. The accepted launch placed the
instrumented Qiskit source checkout on `PYTHONPATH`; the executor then verified
the preregistered binary SHA-256
`b24cf71992cdedc71dd648f6ef758862f253cea8d51274d92d9082b3ed3ec903`
and size `15497264` before loading the frozen input. No failed-preflight trace is
part of the 256-call matrix.

## Claim Boundary

This source-instrumented diagnostic can support or reject a specific ErrorMap accumulation path. It does not by itself establish a confirmed Qiskit bug, a cross-platform compiler theorem, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.
