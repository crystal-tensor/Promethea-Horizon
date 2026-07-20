# B4/B8/B10 R183 Prefix-Initialization Micro-Ablation

- Status: `prefix_initialization_ablation_complete_independent_oracle_pending`
- Result payload hash: `ecb901a7375013fdd8f58727227fe7e80d38c89570d646011790ddfa29bd0c84`
- Requirements: `11/12` passed; P10 awaits the independent oracle

## Paired Measurement

R183 completed `416` same-process AB/BA pairs across `13` isolated workers and `13` cells. Both arms preserve the expected mapping on `416/416` pairs, and all five non-initialization counters agree on `416/416` pairs.

## Frozen Classifications

- H1: `isolated_initialization_write_reduction_passed`; initialized-limb write reduction `0.626724`.
- H2: `unused_tail_initialization_rejected_as_dominant_source_bound_cost`; paired candidate/baseline median ratio `0.984288` against the frozen `0.90` threshold.
- H3: `all_cells_and_orders_reported`; candidate is faster in `8/13` cell medians and clears the speed threshold in `0` cells.

## Claim Boundary

P10 remains pending until the stdlib-only oracle independently recomputes every artifact hash, mapping outcome, counter equality, paired ratio, workload count, and frozen classification. This micro-ablation does not establish a production Qiskit remedy, complete causal attribution, hardware behavior, quantum advantage, BQP separation, a solved frontier, or new credit.
