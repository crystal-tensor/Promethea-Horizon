# B4/B8/B10 R176 Integrated Fixed Superaccumulator Protocol

- Status: `preregistered_unopened`
- Protocol payload hash: `cc7563feada3d1eb0b1b54338f1eff34a058e4594892c6155e43d6ef7d3443c8`
- Contract payload hash: `152699e5351af0b612f955759e7c7b8cc0c196a48929c9a2c80860cf603c5991`

## Research Question

Can a fixed-width exact binary64 superaccumulator preserve the R175 correction while removing its heap-allocation performance failure?

## Frozen Matrix

- R169 ordinary non-tie: 3 profiles x 64 calls x 3 policies.
- R170 first true-tie graph: 3 profiles x 64 calls x 3 policies.
- R172 second true-tie graph: 3 profiles x 64 calls x 3 policies.
- R157/R160 sub-ULP controls: 4 ErrorMap modes x 7 cases x 8 calls x 3 policies.
- Total recorded calls: 2,400; each policy contributes 800.
- Each of 39 isolated workers performs 16 unrecorded warmups before measurement.

## Frozen Performance Gates

- Every fixed/source median-time ratio must be at most 3.0.
- The aggregate fixed/source median-time ratio must be at most 2.5.
- The aggregate fixed/BigUint median-time ratio must be at most 0.90.
- The maximum fixed/source worker peak-RSS ratio must be at most 1.25.

## Claim Boundary

This is a source-bound experimental Rust entry point built from Qiskit 2.4.1 commit `0fd015a22b84c9082173597a5d2304dc0aaec08c`. It is not an upstream-accepted or production Qiskit patch, a confirmed Qiskit bug, a route-quality result, a hardware result, quantum advantage, BQP separation, a solved frontier, or new credit.
