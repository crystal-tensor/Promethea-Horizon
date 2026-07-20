# B4/B8/B10 R175 Independent Rust Exact-Score Oracle

- Status: `independent_rust_exact_score_oracle_failed`
- Requirements: `11/12`
- Payload hash: `f5d8954b479743b31b0fe97d1d2c413881d92c5e8ff7cd8d0ab0cd919925ed17`

## Independent Check

A standard-library-only audit validates `26/26` worker hashes and `1600/1600` row hashes. It reproduces `1152/1152` standard outcomes and independently enumerates all `28/28` sub-ULP exact-oracle cells.

It imports neither Qiskit nor the R175 execution module, performs zero Qiskit calls, simulations, routes, or shots, and recomputes the timing and peak-RSS ratios from immutable worker rows.

## Claim Boundary

This strengthens evidence integrity for the frozen R175 matrix. It does not make the experimental patch upstream accepted or production ready, establish a confirmed Qiskit bug, prove broad route-quality improvement or cross-platform overhead, provide hardware evidence, quantum advantage, BQP separation, solve B4/B8/B10, or add credit.
