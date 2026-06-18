# B1/B7 cone_01 Local-Equivalence Invariant Obligation Gate

Status: `cone01_local_invariant_obligation_not_rewrite_certificate`

This artifact asks whether the `RY(theta)` parameter inside each `cone_01` window changes a numerical local-equivalence fingerprint of the two-qubit unitary. The fingerprint is built from magic-basis traces of the det-normalized unitary. It is a diagnostic, not a formal KAK theorem.

## Summary

- Candidate windows: `35`
- Required exact windows for B7 target: `30`
- Target proxy-T ledger reduction: `600`
- Invariant fingerprint: `magic_basis_det_normalized_trace_m_m2`
- Local-equivalence sensitive windows: `24`
- Local-equivalence flat windows: `11`
- Nearest pi/4-grid invariant mismatches: `24`
- Nearest pi/4-grid invariant matches: `11`
- Local-only absorption blocked count: `24`
- Local-only absorption blocked clears B7 target: `False`
- Min / median / max invariant derivative norm: `0.0` / `0.7128046122151909` / `2.006347280726594`
- Min / median / max nearest-grid invariant distance: `0.0` / `0.13555913939041783` / `0.6976885899513073`
- Validation errors: `0`

## Interpretation

For 24 of 35 candidate windows, theta changes a local-equivalence invariant fingerprint. Those windows cannot be dismissed as purely local one-qubit dressing under this diagnostic. However, 24 is below the 30-window B7 target, and the 11 invariant-flat windows remain open. No occurrence-removing certificate or B7 resource saving is claimed.

## Top Sensitive Windows

| line | qubit | partner | derivative norm | nearest-grid distance |
|---:|---:|---:|---:|---:|
| 152 | 10 | 14 | 2.00634728073 | 0.444397382311 |
| 1599 | 15 | 14 | 2.00634728073 | 0.444397382311 |
| 427 | 16 | 14 | 1.54562130099 | 0.697688589951 |
| 474 | 5 | 14 | 1.26213426741 | 0.214455455055 |
| 139 | 2 | 14 | 1.08762520347 | 0.237046508366 |
| 1588 | 4 | 14 | 1.08762520347 | 0.237046508366 |
| 97 | 13 | 14 | 0.799314816072 | 0.363698764462 |
| 255 | 2 | 14 | 0.799314816072 | 0.363698764462 |
| 348 | 10 | 14 | 0.799314816072 | 0.363698764462 |
| 1257 | 10 | 14 | 0.799314816072 | 0.363698764462 |

## Invariant-Flat Window Lines

477, 94, 252, 345, 1254, 1310, 1366, 1422, 1543, 155, 1602
