# B4/B8/B10 R186 Full VF2 Workflow: macos_arm64

- Status: `platform_complete_cross_platform_oracle_pending`
- Result payload hash: `2c9b48c458ec2128db83b97b4c17b95590ff64d3e548be7df5e7b874ebf81d85`
- Requirements: `10/10`
- Mapping checks: `2808/2808`
- Measured calls: `2808`
- Warmup calls: `936`

## Heuristic Question

Does the exact-score representation remain faster after Qiskit's Python `VF2Layout` and `PassManager` orchestration is included?

## Ratios

- Direct window/BigUint: `0.508427232x`
- Direct window/prefix: `0.693800621x`
- PassManager window/BigUint: `0.933548643x`
- PassManager window/prefix: `0.976947190x`
- Relative saving retained: `0.135181119`

## Platform Hypotheses

- `H1-full-boundary-integrity`: `True`
- `H2-direct-window-competitiveness`: `True`
- `H3-passmanager-window-competitiveness`: `True`
- `H4-relative-saving-retention`: `True`

## Claim Boundary

This is an external source-faithful Qiskit 2.4.1 monkeypatch harness, not an upstream integration or full transpilation benchmark. It contains zero simulations, zero quantum shots, and zero real-backend rows. Cross-architecture classification remains pending until the standard-library oracle checks both platform results.
