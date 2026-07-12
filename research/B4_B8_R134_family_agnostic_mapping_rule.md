# B4/B8 R134 Family-Agnostic Deterministic Mapping Rule

## Result

- Candidate mapping rules: `4`
- Design-set compilations: `240`
- Selected rule: `weighted_distance`
- New validation families: `4`
- Validation compilations: `360`
- Route-invariant groups: `12` / `12`
- Exact-QASM-invariant groups: `12` / `12`
- Frozen QASM replay: `120` / `120`
- Wins/ties/losses vs automatic layout: `28/38/54`
- No-loss groups: `6` / `12`
- Automatic-baseline no-loss gate: `False`
- New credit delta: `0`

## Validation Evidence

- `FakeJakartaV2` / `validation_k33_qaoa_n6`: mapping `[0, 2, 6, 1, 3, 5]`; route/QASM classes `1/1`; gain `+0.006146`; wins/ties/losses `6/4/0`.
- `FakeJakartaV2` / `validation_qft_n6`: mapping `[0, 1, 5, 6, 2, 3]`; route/QASM classes `1/1`; gain `-0.055381`; wins/ties/losses `0/0/10`.
- `FakeJakartaV2` / `validation_rxx_cycle_n6`: mapping `[0, 1, 5, 6, 3, 2]`; route/QASM classes `1/1`; gain `-0.002140`; wins/ties/losses `0/0/10`.
- `FakeJakartaV2` / `validation_tree_phase_n6`: mapping `[3, 1, 5, 0, 2, 6]`; route/QASM classes `1/1`; gain `+0.000000`; wins/ties/losses `0/10/0`.
- `FakeLagosV2` / `validation_k33_qaoa_n6`: mapping `[0, 4, 6, 1, 3, 5]`; route/QASM classes `1/1`; gain `-0.001549`; wins/ties/losses `6/0/4`.
- `FakeLagosV2` / `validation_qft_n6`: mapping `[0, 3, 4, 5, 6, 1]`; route/QASM classes `1/1`; gain `-0.025324`; wins/ties/losses `0/0/10`.
- `FakeLagosV2` / `validation_rxx_cycle_n6`: mapping `[0, 1, 5, 4, 6, 3]`; route/QASM classes `1/1`; gain `-0.002218`; wins/ties/losses `0/0/10`.
- `FakeLagosV2` / `validation_tree_phase_n6`: mapping `[3, 5, 1, 4, 6, 0]`; route/QASM classes `1/1`; gain `+0.000000`; wins/ties/losses `0/10/0`.
- `FakeOslo` / `validation_k33_qaoa_n6`: mapping `[0, 2, 4, 1, 3, 5]`; route/QASM classes `1/1`; gain `+0.006841`; wins/ties/losses `6/4/0`.
- `FakeOslo` / `validation_qft_n6`: mapping `[0, 1, 4, 5, 2, 3]`; route/QASM classes `1/1`; gain `-0.120327`; wins/ties/losses `0/0/10`.
- `FakeOslo` / `validation_rxx_cycle_n6`: mapping `[0, 1, 5, 4, 3, 2]`; route/QASM classes `1/1`; gain `+0.001785`; wins/ties/losses `10/0/0`.
- `FakeOslo` / `validation_tree_phase_n6`: mapping `[3, 1, 5, 0, 2, 4]`; route/QASM classes `1/1`; gain `+0.000000`; wins/ties/losses `0/10/0`.

R134 replaces transferred mappings with a generic graph-embedding rule. Every
candidate enumerates all 5,040 six-to-seven-qubit injections and scores only the
source interaction graph, historical coupling distances, path-error pressure,
and readout error. R133 circuits and fresh design seeds select one rule globally.
The selected rule is then frozen before four new circuit families and disjoint
validation seeds are opened.

## Requirements

- `P1` PASS: R133 source is hash-bound
- `P2` PASS: four generic mapping rules enumerate all injections
- `P3` PASS: design selection is isolated from validation
- `P4` PASS: four new validation circuit families are materialized
- `P5` PASS: all 12 validation groups have complete ten-seed ledgers
- `P6` PASS: route and exact-QASM invariance are measured for every group
- `P7` PASS: all 120 constrained circuits replay in a fresh process
- `P8` PASS: automatic-baseline no-loss verdict is evaluated without promotion
- `P9` PASS: verifier acceptance, mitigation, calibration, and hardware remain excluded
- `P10` PASS: no soundness, advantage, BQP, or new credit is claimed

## Claim Boundary

Supported: isolated evidence for or against a deterministic family-agnostic
mapping rule under the historical exposure proxy. Not supported: verifier
acceptance, causal hardware performance, current calibration, mitigation,
protocol soundness, quantum advantage, BQP separation, or new B10 credit.
