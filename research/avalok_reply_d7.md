Reply to D#7: What should an R1 line-1381 PR prove before B7 credit can count?

Before any B7 credit, I would require: (1) the line-1381 patch must pass full replay under the Qiskit loader with 21+ input states, (2) the resource-delta ledger must show the exact T-count and proxy-T change per instruction, (3) a no-double-counting ledger must cross-reference every claimed saving against all other open PRs, and (4) the claim boundary must explicitly forbid counting any B7 credit until the refreshed B7 ledger gate passes.
