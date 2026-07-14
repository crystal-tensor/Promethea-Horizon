# B4/B8 R160 Deterministic ErrorMap Remediation Protocol

- Status: `deterministic_error_map_remediation_protocol_frozen_before_execution`
- Target chain: `T-B4-002cb/T-B8-003cf/T-B10-009bt` <- `T-B4-002ca/T-B8-003ce/T-B10-009bs`
- Profiles / processes / cases / direct calls: `4` / `16` / `33` / `1056`
- Operation inventory rows / hash: `19` / `716c841307327f62da7679c77c76bc60cfec5231c26736e328d4594aca67b086`
- Margin protection threshold: `1e-16`
- Requirements passed/failed: `10` / `0`
- Contract payload hash: `8f164e093ae6ee4d9be76884c9e7f1b9c3509822365412b086765962aa5438c3`
- Execution started: `False`

## Research Question

Can a deterministic external ErrorMap stabilize the tied R157 layout while preserving every exact-oracle optimum whose score margin exceeds a frozen threshold?

## Frozen Modes

| Mode | Processes | Cases | Replays per case/process | Calls |
|---|---:|---:|---:|---:|
| `ascending_f64` | 4 | 33 | 2 | 264 |
| `descending_f64` | 4 | 33 | 2 | 264 |
| `math_fsum` | 4 | 33 | 2 | 264 |
| `exact_binary_fraction` | 4 | 33 | 2 | 264 |

The 33 cases comprise one untouched tie baseline plus positive and negative 1, 8, 64, and 512 ULP shifts on each of the four physical directed edges whose endpoint-mapping coefficients differ.

## Exact Oracle

Every mode/case ErrorMap is scored over all `7! = 5040` mappings with exact rational arithmetic over the emitted binary64 values. A VF2 output must belong to that mode/case minimum set. A non-tied row counts as margin-protected only when all four modes have the same unique minimizer and every minimum gap is at least `1e-16`.

## Score-Denominator Boundary

R157 recorded `0.45894321220828727` with a Python concrete-operation-only denominator. R160 does not reuse that numeric score. It reconstructs the actual Rust ErrorMap operation inventory retained by R159, including zero-error global operations in each qargs denominator. The prior value remains evidence that the two endpoint coefficients are symmetric, not the accelerator score oracle for R160.

## Smoke Disclosure

Four pre-registration direct calls exercised the four accumulation methods on an unrelated three-qubit `GenericBackendV2(seed=160)` circuit. All outputs belonged to the toy exact-oracle minimum set, invalid mode rejection passed, and the frozen R157 input was not loaded.

## Decision Rule

deterministic_external_map_remediation_supported requires all four modes to select one stable tied vector, at least one margin-protected non-tied case, zero protected-case failures, and every replay inside its exact rational oracle minimizer set

All five classifications remain admissible before execution.

## Claim Boundary

This protocol contains no frozen-input R160 result. It does not claim an accepted upstream patch, confirmed Qiskit bug, cross-platform theorem, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.
