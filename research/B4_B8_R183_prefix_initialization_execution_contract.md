# B4/B8/B10 R183 Execution Contract

- Status: `execution_tooling_bound_unopened`
- Contract payload hash: `85e246e691fe4877bd0ed105cb5cbbe700e9b5eab0015e678a1b101008988576`
- Tool bindings: `6`
- Source bindings: `13`
- Public design commit: `7b98e61d5281a90ecc6721fb86d6a144e0b5207b`
- Public Discussion: https://github.com/crystal-tensor/Prometheus-plan/discussions/276
- Scientific execution: unopened

## Same-Process Pairing

The frozen matrix contains `416` AB/BA pairs in `13` isolated workers. Every pair runs two uninstrumented timing calls and two separate probes; probe time is excluded. Equal `16`/`16` order counts are required in every cell.

## Isolation Boundary

Both arms retain the same 34-limb object width and active-prefix arithmetic. The candidate changes only destination initialization of the unused suffix through a MaybeUninit representation whose initialized-prefix invariant is covered by the frozen Rust test gate.

## Claim Boundary

The patch, runner, oracle, build, bundle, and public workflow are hash-bound. This contract is not a timing result, causal diagnosis, upstream Qiskit remedy, hardware result, quantum advantage, BQP separation, solved frontier, or new credit.
