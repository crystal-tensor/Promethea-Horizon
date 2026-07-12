# B4/B8 R127 Calibration-Aware Layout Design

## Summary

- Target: `T-B4-002ab/T-B8-003af/T-B10-009t`
- Upstream target: `T-B4-002aa/T-B8-003ae/T-B10-009s`
- Method: `b4_b8_r127_calibration_aware_layout_design_v0`
- Status: `calibration_aware_layout_design_boundary`
- Enumerated mappings: `30240`
- Selected layouts: `6`
- Compiled exposure improvements: `3` / `6`
- Mean compiled exposure delta: `-0.0050`
- Layout design gate passed: `False`
- Acceptance holdout executed: `False`
- New credit delta: `0`

- `FakeOslo` / `private_bundle_ghz_n6`: mapping `[1, 3, 5, 0, 4, 2]`, static objective `0.1778`, source/candidate compiled exposure `0.1585/0.1732`, delta `-0.0147`, source/candidate CX `11/14`.
- `FakeOslo` / `private_bundle_graph_n6`: mapping `[4, 5, 3, 1, 2, 0]`, static objective `0.1321`, source/candidate compiled exposure `0.1360/0.1321`, delta `0.0039`, source/candidate CX `8/8`.
- `FakeJakartaV2` / `private_bundle_ghz_n6`: mapping `[1, 2, 3, 5, 6, 0]`, static objective `0.2484`, source/candidate compiled exposure `0.2267/0.2476`, delta `-0.0209`, source/candidate CX `11/14`.
- `FakeJakartaV2` / `private_bundle_graph_n6`: mapping `[6, 5, 3, 1, 0, 2]`, static objective `0.2116`, source/candidate compiled exposure `0.2154/0.2116`, delta `0.0037`, source/candidate CX `8/8`.
- `FakeLagosV2` / `private_bundle_ghz_n6`: mapping `[3, 0, 1, 4, 5, 6]`, static objective `0.7525`, source/candidate compiled exposure `0.7290/0.7383`, delta `-0.0093`, source/candidate CX `11/14`.
- `FakeLagosV2` / `private_bundle_graph_n6`: mapping `[6, 5, 4, 3, 1, 0]`, static objective `0.7026`, source/candidate compiled exposure `0.7097/0.7026`, delta `0.0071`, source/candidate CX `8/8`.

R127 enumerates all injective six-logical-to-seven-physical mappings using only
frozen snapshot measurement and CX properties plus each task's logical
two-qubit interaction graph. It then transpiles one all-Z representative per
selected mapping to test whether the static objective predicts lower compiled
exposure than the R125 default layout. No new randomized-measurement holdout is
executed and no mitigation performance claim is made.

## Next Gate

Publicly preregister a disjoint-seed layout/readout ablation using the selected
mappings, calibration rows isolated from evaluation rows, and the unchanged
A1-A5 acceptance conditions.

## Requirements

- `P1` PASS: R125 and R126 source artifacts are hash-bound and consumed
- `P2` PASS: all injective six-to-seven physical mappings are enumerated
- `P3` PASS: the static objective uses only snapshot and task-graph properties
- `P4` PASS: ten ranked mappings are retained per snapshot/task
- `P5` PASS: one selected mapping is transpiled per snapshot/task
- `P6` PASS: selected compiled circuits preserve logical classical-bit order
- `P7` PASS: compiled exposure is compared against every R125 default layout
- `P8` PASS: no acceptance holdout or readout mitigation is executed
- `P9` PASS: historical snapshots remain separate from current and hardware evidence
- `P10` PASS: no soundness, advantage, BQP, or new credit is claimed

## Claim Boundary

Supported: deterministic calibration-aware layout candidates and compiled
exposure comparisons. Not supported: improved verifier completeness, readout
mitigation, current calibration, provider access, hardware execution, protocol
soundness, quantum advantage, BQP separation, or B10 credit.
