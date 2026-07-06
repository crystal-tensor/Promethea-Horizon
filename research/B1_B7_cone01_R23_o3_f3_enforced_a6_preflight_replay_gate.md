# B1/B7 Cone01 R23 O3-F3 Enforced A6 Preflight Replay Gate

- Target: `T-B1-004dy/T-B7-013h`
- Upstream target: `T-B1-004dx/T-B7-013g`
- Method: `b1_b7_cone01_r23_o3_f3_enforced_a6_preflight_replay_gate_v0`
- Status: `cone01_r23_o3_f3_enforced_a6_preflight_replay_ready`
- Candidate: `NL-C02`
- Family: `O3-F3`
- Replay hash: `0a9c84e725e45b01e1e42d6cf2f00effede669c02740576953f898657c828379`
- Enforced rule hash: `44be69e5d788aae82a046843648f1186406fbdd43917b6397de51a02810a2ae2`
- Template replay hash: `3333487f013918f9a502e94326c3ffd1f827ca71ee83fd04334f03b40d4c8321`
- Overclaim replay hash: `91367d0b3d90c30aded56d817466b98f83394c49b217b8c926420d2b938a3446`

## Result

R23 passes 9/9 requirements and moves the R22 A6 polarity rule from advisory status into a replayed O3-F3 preflight rule.

## What Changed

- The R20 template boundary still passes A6 polarity, but template markers prevent artifact acceptance.
- The R21 overclaim fixture now fails A6 in addition to its earlier A2/A4/A7/A8 failures.
- The enforced replay therefore rejects the overclaim on `A2/A4/A6/A7/A8`.
- No O3-F3 artifact is accepted, no O3 closure is claimed, and no B7 credit is granted.

## Gate Replay

- Old overclaim failed gates: `['A2', 'A4', 'A7', 'A8']`
- New overclaim failed gates: `['A2', 'A4', 'A6', 'A7', 'A8']`
- A6 newly failed for overclaim: `True`
- Template rejected as submission: `True`

## Requirement Results

- `N1` PASS: R20/R21/R22 source gates are validation-clean and connected
- `N2` PASS: R23 A6 rule is the R22 polarity semantics, not the old lexical mention test
- `N3` PASS: R20 template boundary passes A6 polarity but is not accepted as an artifact
- `N4` PASS: R21 overclaim replay now fails A6 polarity
- `N5` PASS: A6 is newly failed relative to the R21 old preflight
- `N6` PASS: Overclaim remains rejected under the enforced preflight
- `N7` PASS: R23 does not accept O3-F3, close O3, or permit reroute
- `N8` PASS: R23 preserves zero B7/resource credit claims
- `N9` PASS: R23 replay packet is internally hash-bound

## Claim Boundary

- Supported: R23 enforces the R22 A6 claim-boundary polarity rule inside a replayed O3-F3 preflight. The R21 overclaim fixture now fails A6 directly, and the reusable R20 template is kept from being promoted as a submitted artifact.
- Not supported: R23 does not submit or accept a valid O3-F3 artifact, does not close O3, and does not permit R5 reroute. No R1 solution, occurrence removal, proxy-T reduction, B7 credit, resource saving, or impossibility theorem is supported.
- Next gate: Replace the red-team fixture with a real O3-F3 symbolic local-unitary proof, counterexample, or rejection-strengthening artifact that passes the enforced A1-A8 preflight, or move to O3-F4 numerical refit / O3-F5 Route A artifact pressure.

This replay gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.

## Validation

- validation_error_count: `0`
