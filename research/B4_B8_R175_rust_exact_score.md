# B4/B8/B10 R175 Integrated Rust Exact-Score Replay

- Status: `integrated_rust_exact_score_rejected_on_frozen_matrix`
- Classification: `bounded_compiled_comparator_integration_failed`
- Requirements: `13/14`
- Payload hash: `1ff039f6c9ed14831ec2b58e8053da523aa4c01f8d873a96b7f3c39f72439067`

## Research Question

Can exact retained-binary64 score accumulation run inside the compiled Rust VF2 path without breaking ordinary mappings or exceeding frozen local overhead gates?

## Result

The matrix executes `2016` direct Qiskit calls, including `1600` recorded calls and `416` warmups across `26` isolated processes. Source f64 matches all `800/800` committed outcomes. The exact entry preserves R169 on `192/192`, repairs R170 on `192/192`, repairs R172 on `192/192`, and repairs the R160 sub-ULP rows on `224/224` while source reproduces all `224/224` prior wrong winners.

## Performance

The aggregate exact/source median-time ratio is `2.543563`; the maximum among 37 frozen cells is `3.734856`. The maximum exact/source process peak-RSS ratio across 13 worker pairs is `1.018053`. The tested exact nonzero gaps span `0.03125` to `0.5` ULP.

## Claim Boundary

This is a bounded, source-bound experimental entry point. It is not an upstream-accepted or production Qiskit patch, a confirmed Qiskit bug, a broad route-quality improvement, a cross-platform performance result, hardware evidence, quantum advantage, BQP separation, solved B4/B8/B10, or new credit.
