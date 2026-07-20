# B4/B8/B10 R182 Exact-Score Cost Attribution

- Status: `cost_attribution_complete_independent_oracle_pending`
- Result payload hash: `de7cbb2dacf90e2134764f63ae44355f87ecfe9b4416b8d0af7d2ca662a5e10b`
- Requirements: `11/12` passed; P10 awaits the independent oracle

## Paired Measurement

R182 completed `1248` measurement pairs across `39` isolated workers and `13` cells. Each pair timed an uninstrumented exact-score call, then ran a separate counter probe. Timing/probe/expected mappings agree on `1248/1248` rows.

## Frozen Classifications

- H1: `full_width_initialization_or_common_cost_pressure_consistent_not_causal`; arithmetic-visit reduction `0.521362`, active/fixed timing ratio `0.987547`.
- H2: `biguint_heap_pressure_rejected`; allocation/timing-gap Spearman `-0.796421`.
- H3: `cell_heterogeneity_reported` over `13` cells.

## Claim Boundary

P10 remains pending until the executor-free oracle reproduces every artifact hash, count, mapping outcome, counter vector, rank correlation, and classification. These source-bound counters may support or reject a diagnostic pressure; they do not prove causality, a production Qiskit remedy, hardware behavior, quantum advantage, BQP separation, a solved frontier, or new credit.
