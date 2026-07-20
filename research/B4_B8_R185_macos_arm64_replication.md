# B4/B8/B10 R185 Windowed Exact-Score Experiment

- Status: `macos_arm64_replication_complete_independent_oracle_pending`
- Result payload hash: `09e3f16f0920b7e854d18274cd7f5f8a569859172132627d69584c5100ddd0a3`
- Requirements: `12/13` passed; P10 awaits the independent oracle

## Three-Arm Measurement

R185 completed `468` same-process BigUint/prefix/window triplets across `13` isolated workers and `13` cells. All three timing arms plus the separate window probe preserve the expected mapping on `468/468` triplets.

## Frozen Classifications

- H1: `all_timing_and_probe_mappings_exact`; mapping integrity `True`.
- H2: `compact_path_observed_without_fallback`; maximum compact limbs `2`, object size `40` bytes, fallback transitions `0`, wide combines `0`.
- H3: `window_materially_faster_than_prefix_reference`; paired window/prefix median ratio `0.677482` against the frozen `0.90` threshold.
- H4: `window_competitive_with_biguint`; paired window/BigUint median ratio `0.501213` against the frozen `1.00` threshold; all-order coverage `True`.
- H5: `linux_x86_64_and_macos_arm64_both_support_H1_through_H4`; Linux H1-H4 `True`, macOS H1-H4 `True`, identical patch/workload/thresholds `True/True/True`.

## Claim Boundary

P10 remains pending until the stdlib-only oracle independently recomputes every artifact hash, mapping outcome, counter boundary, paired ratio, workload count, and H1-H5 classification. This experiment does not establish a universal platform theorem, full-domain performance theorem, production Qiskit remedy, hardware behavior, quantum advantage, BQP separation, a solved frontier, or new credit.
