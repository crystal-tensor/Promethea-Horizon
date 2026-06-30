# B6 Crystallographic Evidence Contract Gate

Status: **crystallographic_evidence_contract_open_not_material_discovery_claim**

## Summary

T-B6-005 converts the failed T-B6-004 crystallographic reproducibility gate into five PR-sized evidence packets. This is a handoff contract, not a material-discovery, solved-mechanism, DFT-observable, B5-observable, or superconductivity-solution claim.

## Contract Metrics

- Source failed requirements: R6, R7, R8, R9, R10
- Records / families / negative controls: 56 / 28 / 18
- Post-split records: 27
- Post-split crystallographic AP / family-prior AP: 0.2476190476190476 / 0.4901360544217687
- Source validation error count: 2
- pymatgen available: False
- Contract requirements passed / failed: 3 / 5
- Contract packets: 5

## Requirements

| ID | Pass | Requirement | Evidence | Missing to promote |
| --- | --- | --- | --- | --- |
| K1 | yes | source reproducibility gate is present and bounded | benchmark_id=B6; method=b6_crystallographic_reproducibility_gate_v0; status=crystallographic_reproducibility_gate_failed_not_material_discovery_claim; failed=['R6', 'R7', 'R8', 'R9', 'R10'] | Keep the contract tied to the failed T-B6-004 gate. |
| K2 | yes | table size and holdout scope are contract-ready | records=56; families=28; negatives=18; post_split=27 | Preserve the same audited B6 crystallographic row scope. |
| K3 | yes | forbidden discovery and mechanism claims are absent | no_forbidden_claims=True | Keep all claims bounded until reproducibility, baselines, and observables pass. |
| K4 | no | reproducible crystallographic backend is available | pymatgen_available=False | Pin pymatgen or an equivalent descriptor backend with deterministic version metadata. |
| K5 | no | source validation blockers are removed | source_validation_error_count=2 | Remove source validation blockers and rerun the crystallographic screen. |
| K6 | no | post-split crystallographic AP beats family prior | post_split_crystallo_ap=0.2476190476190476; post_split_family_prior_ap=0.4901360544217687 | Beat the family-prior denominator on the post-split holdout. |
| K7 | no | DFT observable channel is attached | dft_observable_claimed=False | Attach computed DFT observables or keep the descriptor as non-DFT proxy evidence. |
| K8 | no | B5 computed observable channel is attached | b5_computed_observable_claimed=False | Attach B5-computed response observables or keep B6 disconnected from B5 mechanisms. |

## PR Packets

### B6-R6-reproducible-crystallographic-backend

- Source gate: R6
- Title: Pin a reproducible crystallographic descriptor backend
- Acceptance: record pymatgen or equivalent package version
- Acceptance: rerun descriptor extraction deterministically
- Acceptance: preserve the 56-record / 28-family / 18-negative-control scope
- Claim boundary: Packet evidence may support B6 descriptor reproducibility only after audit; it must not claim material discovery, solved mechanism, complete database, DFT observables, B5 observables, or superconductivity solution unless the corresponding contract gate passes.

### B6-R7-source-validation-cleanup

- Source gate: R7
- Title: Remove source validation blockers
- Acceptance: validation_error_count is 0
- Acceptance: negative controls are not silently excluded from top-k analysis
- Acceptance: family-prior dominance is reported and addressed
- Claim boundary: Packet evidence may support B6 descriptor reproducibility only after audit; it must not claim material discovery, solved mechanism, complete database, DFT observables, B5 observables, or superconductivity solution unless the corresponding contract gate passes.

### B6-R8-family-prior-denominator

- Source gate: R8
- Title: Beat the post-split family-prior denominator
- Acceptance: post_split_crystallo_ap is greater than post_split_family_prior_ap
- Acceptance: same post-2008 holdout rows are used
- Acceptance: no family leakage or post-hoc reranking is introduced
- Claim boundary: Packet evidence may support B6 descriptor reproducibility only after audit; it must not claim material discovery, solved mechanism, complete database, DFT observables, B5 observables, or superconductivity solution unless the corresponding contract gate passes.

### B6-R9-dft-observable-channel

- Source gate: R9
- Title: Attach DFT observables
- Acceptance: DFT feature definitions and units are stored
- Acceptance: source structures are traceable
- Acceptance: claim boundary states whether DFT is computed or absent
- Claim boundary: Packet evidence may support B6 descriptor reproducibility only after audit; it must not claim material discovery, solved mechanism, complete database, DFT observables, B5 observables, or superconductivity solution unless the corresponding contract gate passes.

### B6-R10-b5-observable-channel

- Source gate: R10
- Title: Attach B5-computed observables
- Acceptance: B5 observable source artifact is named
- Acceptance: observable units and row alignment are stored
- Acceptance: B6 ranking does not claim mechanism without B5 support
- Claim boundary: Packet evidence may support B6 descriptor reproducibility only after audit; it must not claim material discovery, solved mechanism, complete database, DFT observables, B5 observables, or superconductivity solution unless the corresponding contract gate passes.

## Claim Boundary

- No material discovery is claimed.
- No high-temperature superconductivity mechanism is claimed solved.
- No complete materials database is claimed.
- No reproducible crystallographic descriptor claim is made yet.
- No DFT or B5-computed observable claim is made yet.
