# B9 Offline Proof Artifact Bundle Gate

Status: **offline_proof_artifact_bundle_open_missing_checked_run**

## Summary

- Method: `b9_offline_proof_artifact_bundle_gate_v0`
- Bundle requirements passed/failed: 5 / 3
- Failed bundle requirement IDs: ['B6', 'B7', 'B8']
- Bundle artifacts present: 8 / 8
- Bundle hash: `a06204258abc9e5b0e8620f542865f504f6997578c039ebb9f106f508cc7bc1f`
- Checked run artifacts: 0

## Bundle Artifacts

| Role | Path | Exists | SHA-256 |
|---|---|---|---|
| pinned Lean toolchain | `lean-toolchain` | True | `e6930c662006db4d6dc76c651d60a608e4f6a18bcfd53e6b0167d70a125285d5` |
| Lake project definition | `lakefile.lean` | True | `4d24f18967fce6e70b985da8aa6d9501297625642bfc945d629780d85b0993bd` |
| Lake module theorem interface | `B9/ClusterStabilizer/WidthLocality.lean` | True | `d885cfe38990798c8cbd281959ed995a17427b38991968a9f40801c2a3bfa43c` |
| research skeleton theorem interface | `research/proof_skeletons/B9_cluster_stabilizer_width_locality_bound.lean` | True | `d3d896c1b5818b26deecc747f3f5fd08cf53da6c76a86c191cd9de39c58e7651` |
| reviewed CI workflow template | `research/ci/b9-lean-proof-scaffold.yml` | True | `c04a7c9539ce0d00f6a01b20cfcfbd0e3f301979e1f0f745d4f93c58cf936314` |
| local exact-rational verifier result | `results/B9_cluster_stabilizer_parametric_certificate_v0.json` | True | `286ff2717f209986698b4402a8776065c7262138a32cb85f88fcd5aec27155e7` |
| scaffold gate result | `results/B9_proof_project_scaffold_gate_v0.json` | True | `c987c28dc5e9e4869f98db89d855ca1c8169f2d1f083e0feb979d49cdd509c2e` |
| CI contract result | `results/B9_toolchain_ci_contract_gate_v0.json` | True | `9505ffbda7606825164ace430ed646d7ca81e47b76708bc8c295bb2289da82de` |

## Required Checked Run Artifacts

- lean --version output showing Lean 4
- lake --version output
- lake env lean B9/ClusterStabilizer/WidthLocality.lean transcript
- hash of checked Lean module and lake manifest used for the run

## Requirement Results

- B1 [PASS]: CI contract is blocked only by workflow activation and remote checked output
- B2 [PASS]: Proof scaffold has non-placeholder theorem interfaces
- B3 [PASS]: Local exact-rational verifier evidence remains checked
- B4 [PASS]: All offline bundle source artifacts exist and are hashable
- B5 [PASS]: Forbidden theorem and Quantum PCP claims remain false
- B6 [FAIL]: Lean/Lake checked run artifact is present
- B7 [FAIL]: Proof assistant checked theorem output is present
- B8 [FAIL]: Active remote CI artifact or equivalent offline attestation is accepted

## Claim Boundary

- Supported: The current B9 Lean scaffold, CI template, and local exact-rational verifier artifacts are bundled with stable hashes for offline proof-run PRs.
- Not supported: No Lean/Lake checked run artifact, proof-assistant checked theorem, Quantum PCP proof, NLTS theorem, or global gap-amplification impossibility theorem is established.
- Next gate: Submit Lean 4/Lake checked output for B9/ClusterStabilizer/WidthLocality.lean or install the reviewed GitHub workflow with a token that has workflow scope.
- proof_assistant_checked: False
- formal_theorem_proved: False
- explicit_not_quantum_pcp_proof: True

## Validation

- validation_error_count: 0
