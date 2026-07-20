# B4/B8/B10 R184 Execution Contract

- Status: `execution_tooling_bound_unopened`
- Contract payload hash: `afd219391029c7e39eacffd185d3bf1402147ad713564aaba053e38ee3bc4280`
- Tool bindings: `6`
- Source bindings: `13`
- Public design commit: `84e3d910b7a4fa76f90b0e665027634f4dfd62eb`
- Public Discussion: https://github.com/crystal-tensor/Prometheus-plan/discussions/278
- Scientific execution: unopened

## Same-Process Triplets

The frozen matrix contains `468` BigUint/prefix/window triplets in `13` isolated workers. Every triplet runs three uninstrumented timing calls and one separate window probe; probe time is excluded. All six arm orders occur `6` times per cell.

## Isolation Boundary

The BigUint arm is the exact dynamic denominator, the 34-limb prefix arm is the latest fixed-width reference, and the candidate stores an exact four-limb window plus a global offset. Any wider exact sum falls back to BigUint; no truncation or approximate comparison is allowed.

## Claim Boundary

The patch, runner, oracle, build, bundle, and public workflow are hash-bound. This contract is not a timing result, full-domain performance theorem, upstream Qiskit remedy, hardware result, quantum advantage, BQP separation, solved frontier, or new credit.
