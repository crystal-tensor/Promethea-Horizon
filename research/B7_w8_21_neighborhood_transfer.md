# B7 w8_21 Larger-Neighborhood Parameter Transfer

- Status: `larger_neighborhood_refit_complete_no_resource_reduction`
- Classification: `bounded_same_skeleton_context_refit_boundary`
- Selected w8_21 occurrences: `16`
- Same-target contexts tested: `7`
- Exact five-parameter refits: `0`
- Best objective residual: `2.301426e-01`
- Accepted occurrence removal: `0`
- Accepted proxy-T reduction: `0`
- Validation errors: `0`

## Heuristic question

Can the exact w8_21 invariant absorb an adjacent arbitrary Rz by refitting the same two-CNOT, five-parameter normal form, or does the extra local degree of freedom require a new carrier?

## Experiment

The upstream real-circuit replay found seven selected non-overlapping w8_21 spans immediately followed by the same-target arbitrary rotation `rz(0.28861107553559073)`. For each row, the complete context was formed as `Rz(f) * S(a,b,c,d,e)` and fit to the existing five-parameter two-CNOT normal form using 12 deterministic seeds and a declared least-squares tolerance of `1e-10`.

No exact fit was found in `0/7` contexts. The best residual was `2.301426e-01`. This closes only the declared same-skeleton refit route; it is not a global obstruction theorem.

## Resource boundary

Because no exact source-backed refit exists, the candidate cannot remove the external arbitrary rotation. Accepted occurrence removal, proxy-T reduction, and B7 credit remain zero.

## Next route

The next experiment must carry the external Rz through a commutation-aware scaffold and price every new local parameter before any semantic replay or ledger claim.
