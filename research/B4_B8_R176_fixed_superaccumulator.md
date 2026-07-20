# B4/B8/B10 R176 Integrated Fixed Superaccumulator Replay

- Status: `integrated_fixed_superaccumulator_supported_on_frozen_matrix`
- Classification: `bounded_compiled_comparator_integration_with_performance_ledger`
- Requirements: `16/16`
- Payload hash: `2e956318755c47524ba59909040062719eb230d35a5844a380065d1926ce93cc`

## Research Question

Can a fixed-width exact binary64 superaccumulator preserve the R175 correction while removing its BigUint allocation bottleneck?

## Result

The matrix executes `3024` direct Qiskit calls, including `2400` recorded calls and `624` warmups across `39` isolated processes. Source, BigUint, and fixed policies each match `800/800`, `800/800`, and `800/800` frozen outcomes; BigUint and fixed agree on `800/800` mappings. Fixed exact preserves R169 on `192/192`, repairs R170 on `192/192`, repairs R172 on `192/192`, and repairs the R160 sub-ULP rows on `224/224`.

## Performance

The aggregate BigUint/source ratio is `2.459249`; fixed/source is `1.889304`; fixed/BigUint is `0.768244`. The maximum fixed/source ratio among 37 cells is `2.486844`, and maximum fixed/source process peak-RSS ratio across 13 triplets is `1.016771`. Tested nonzero gaps span `0.03125` to `0.5` ULP.

## Claim Boundary

This is a bounded, source-bound experimental entry point. It is not an upstream-accepted or production Qiskit patch, a confirmed Qiskit bug, a broad route-quality improvement, a cross-platform performance result, hardware evidence, quantum advantage, BQP separation, solved B4/B8/B10, or new credit.
