# B4/B8/B10 R186 Independent Oracle

- Status: `independent_oracle_complete`
- Oracle payload hash: `3d938801dc74f5ca165c892c8b0fe21fef0f7d3285e6e300e0ea201e4e3cf12d`
- Requirements: `11/13`
- Worker manifests: `26/26`
- Row hashes: `936/936`
- Mapping checks: `5616/5616`

## Cross-Architecture Question

Does the exact-window gain survive the Python VF2Layout/PassManager boundary on both architectures under one unchanged protocol?

## Recomputed Results

### linux_x86_64

- Direct window/BigUint: `0.809280454x`
- PassManager window/BigUint: `0.993604808x`
- Relative saving retained: `0.033531916`

### macos_arm64

- Direct window/BigUint: `0.508427232x`
- PassManager window/BigUint: `0.933548643x`
- Relative saving retained: `0.135181119`

## Hypotheses

- `H1-full-boundary-integrity`: `True`
- `H2-direct-window-competitiveness`: `True`
- `H3-passmanager-window-competitiveness`: `True`
- `H4-relative-saving-retention`: `False`
- `H5-cross-architecture-workflow-transfer`: `False`

## Claim Boundary

The oracle uses only the Python standard library and imports neither Qiskit nor the R186 executor. This validates the committed hashes, mapping decisions, timing arithmetic, and frozen classifications. It does not turn the external monkeypatch harness into an upstream integration, full transpilation result, hardware result, quantum advantage, BQP separation, solved frontier, or new credit.
