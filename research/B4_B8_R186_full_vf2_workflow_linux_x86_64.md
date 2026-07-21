# B4/B8/B10 R186 Full VF2 Workflow: linux_x86_64

- Status: `platform_complete_cross_platform_oracle_pending`
- Result payload hash: `ee60d245df52889706b6b04ee11da1d0e84736360b8a761241b45e471448a29f`
- Requirements: `9/10`
- Mapping checks: `2808/2808`
- Measured calls: `2808`
- Warmup calls: `936`

## Heuristic Question

Does the exact-score representation remain faster after Qiskit's Python `VF2Layout` and `PassManager` orchestration is included?

## Ratios

- Direct window/BigUint: `0.809280454x`
- Direct window/prefix: `0.786438509x`
- PassManager window/BigUint: `0.993604808x`
- PassManager window/prefix: `0.989606870x`
- Relative saving retained: `0.033531916`

## Platform Hypotheses

- `H1-full-boundary-integrity`: `True`
- `H2-direct-window-competitiveness`: `True`
- `H3-passmanager-window-competitiveness`: `True`
- `H4-relative-saving-retention`: `False`

## Claim Boundary

This is an external source-faithful Qiskit 2.4.1 monkeypatch harness, not an upstream integration or full transpilation benchmark. It contains zero simulations, zero quantum shots, and zero real-backend rows. Cross-architecture classification remains pending until the standard-library oracle checks both platform results.
