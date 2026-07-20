# B4/B8/B10 R173 First Divergent Combine Protocol

- Status: `preregistered_execution_unopened`
- Protocol payload hash: `aa3e885127b34497624d2dca99b75792226f7f2031b50a41d96e02d31c8ae63d`
- Contract payload hash: `a8e0eb5ba1d622693183e3645934d14bb0e6f4bc30b90ec234139338f384bb39`
- Planned source traces: `6`

## Research Question

At which source-level binary64 combine does each R170/R172 exact-tie candidate branch first diverge from the correctly rounded exact prefix, and can an exact-total policy preserve both true ties and declared non-ties?

## Frozen Analysis

For the source-selected and exact-retained-leaf-selected candidates, R173 reconstructs the source combine chain from the complete event trace. At each prefix it compares the recorded binary64 result with the correctly rounded exact sum of the retained binary64 leaves. The first unequal bit pattern is the declared first divergent combine.

Every recorded combine must also equal native binary64 `left + right`. This separates ordinary accumulation-order sensitivity from malformed arithmetic evidence.

## Policy Guardrail

The candidate policy compares exact retained-leaf fractions and preserves first-seen order only on exact equality. It must pass all six R170/R172 exact-tie traces, all four R160 tie-baseline mode rows, and all 28 R160 unique-minimum non-tie rows.

## Claim Boundary

Execution is unopened. The protocol does not claim a Qiskit bug, source patch, production remedy, route improvement, hardware result, quantum advantage, BQP separation, solved frontier, or new credit.
