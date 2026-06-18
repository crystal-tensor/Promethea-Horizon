# B1/B7 gcm_h6 Cone Feasibility Gate v0.1

Status: **cone_feasibility_gate_candidate_windows_not_rewrite**

This gate checks whether the B1/B7 target-selector cones contain local
windows simple enough for the next exact rewrite/synthesis attempt. It does
not rewrite the circuit and does not claim a resource saving.

## Summary

- Target removed arbitrary occurrences: 30
- Target proxy-T ledger reduction: 600
- Target cone classes evaluated: 3
- Target cone total occurrences: 111
- Strict direct CNOT-rotation-CNOT sandwiches: 4
- Pair-local windows: 106
- Pair-local single-arbitrary windows: 86
- Cone classes meeting target by pair-local single-arbitrary windows: 1
- Leading feasible cone: cone_01
- Leading feasible cone pair-local single-arbitrary windows: 35

## Cone Feasibility Table

| Cone | Occurrences | Direct sandwiches | Pair-local windows | Pair-local single-arb windows | Meets 30? | Certificate? |
|---|---:|---:|---:|---:|---|---|
| cone_01 | 45 | 1 | 43 | 35 | True | False |
| cone_02 | 34 | 1 | 31 | 26 | False | False |
| cone_03 | 32 | 2 | 32 | 25 | False | False |

## Claim Boundary

- No rewrite is claimed.
- No resource saving is claimed.
- No semantic certificate is claimed.
- No physical layout result is claimed.

## Next Gate

`T-B1-004` should now focus on `cone_01`: synthesize or prove a local
two-qubit semantic rewrite for at least 30 of its pair-local single-arbitrary
windows, emit replayable certificates, and only then re-run the B7 FT ledger.
