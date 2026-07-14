# B4/B8 R159 ErrorMap Accumulation Trace Protocol

- Status: `error_map_accumulation_trace_protocol_frozen_before_execution`
- Source target: `T-B4-002bz/T-B8-003cd/T-B10-009br`
- Profiles / processes / traced calls: `3` / `3` / `256`
- Base / patched source SHA-256: `267810aaddb8ac9336f4404e7da34c31e07eec725eb1baa4ed6bf32ff7448ca4` / `ab0f531947caee2667d2be3f3cc63701dc925c1cc60b16d32e9c1b1f97dc526f`
- Instrumented binary SHA-256: `b24cf71992cdedc71dd648f6ef758862f253cea8d51274d92d9082b3ed3ec903`
- Patch / build-manifest hashes: `184a11339ebc369fb1500e76ad178672cbc620e9fc58a8eeccac292efa2f5674` / `13ce8844a70a4e3d06d5cff95a5dd3048bae3167e66614d08f08f9454d0e5dbc`
- Contract payload hash: `3a395f09a9894b0820af788e9c7f52d26ebbdb9f5bf708257e5d50aec27e3547`
- Requirements passed/failed: `10` / `0`

## Frozen Matrix

| Profile | Operation order | Process count | Calls |
|---|---|---:|---:|
| `native_hashset_order` | `native` | 1 | 128 |
| `ascending_sorted_order` | `ascending` | 1 | 64 |
| `descending_sorted_order` | `descending` | 1 | 64 |

## Pre-registration Build Disclosure

The exact patch applies cleanly to Qiskit `0fd015a22b84c9082173597a5d2304dc0aaec08c`, passes cargo fmt checking, and produced the hash-bound release accelerator above. Three API-smoke calls used only `GenericBackendV2(num_qubits=3, seed=159)` and a three-operation toy circuit; the frozen R157 input was not loaded.

## Decision Rule

operation_order_f64_path_supported requires native mapping variation, both sorted profiles to collapse, multiple native average-error bit maps, a functional native order-hash to error-bits relation, and a functional error-bits to mapping-class relation. All other preregistered classifications remain admissible.

## Claim Boundary

This protocol freezes an instrumented experiment only. It contains no frozen-input outcome and does not establish a causal mechanism, confirmed Qiskit bug, general compiler theorem, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.
