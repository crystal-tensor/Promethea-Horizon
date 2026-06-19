# B1/B7 Cone 01 Local-Dressing Search Gate

Status: `cone01_local_dressing_search_not_resource_certificate`

This artifact tests whether each flat-pattern nearest-grid representative can be matched to the original window with arbitrary one-qubit local dressing on both sides. It is a numerical obligation gate, not a circuit rewrite certificate and not a B7 resource claim.

## Summary

- Pattern groups: `3`
- Covered invariant-flat occurrences: `11`
- Local-dressing exact passes: `3`
- Max local-dressing residual: `4.710277376051325e-16`
- Max off-grid dressing parameters per packet: `9`
- Accepted occurrence removal: `0`
- Missing occurrences after this gate: `30`

## Pattern Results

| Pattern | Occurrences | Grid | Same-envelope residual | Dressed residual | Off-grid dressing params | Accepted removal |
|---|---:|---|---:|---:|---:|---:|
| flat_pattern_01 | 8 | `-7*pi/4` | `0.364351623317` | `3.52178773379e-16` | `9` | `0` |
| flat_pattern_02 | 2 | `-7*pi/4` | `0.212536567114` | `4.71027737605e-16` | `9` | `0` |
| flat_pattern_03 | 1 | `-4*pi/4` | `0.327756333139` | `3.92032153735e-16` | `8` | `0` |

## Claim Boundary

- Numeric local dressing exists for the three packets in this bounded search.
- The dressing introduces arbitrary local Euler parameters; those parameters are not free under the B7 occurrence ledger.
- Accepted occurrence removal remains 0 and accepted proxy-T reduction remains 0.
- No KAK theorem, semantic certificate, rewrite certificate, resource saving, or B7 ledger improvement is claimed.

Validation error count: `0`
