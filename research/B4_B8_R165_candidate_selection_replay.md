# B4/B8 R165 Complete-Candidate Selection Replay

- Status: `candidate_selection_replay_complete`
- Classification: `candidate_policy_mapping_difference_observed`
- Profiles / replays: `3` / `256`
- Yielded complete candidates: `298`
- Source-return matches: `256` / `256`
- Payload hash: `93b0ed46f52a0267d4977d3aa3ced7380cd1654167ce7420ba570eff264e6e16`

## Research Question

Can arithmetic policy differences change the selected complete VF2 candidate when candidate enumeration, mapping labels, and first-seen tie handling are retained?

## Method

R165 runs the hash-bound R165 accelerator over the frozen R157 input. It records every complete candidate yielded by the VF2 iterator, then replays the declared first-seen selection rule under source binary64, compensated `math.fsum`, exact retained-binary64 leaves, and a 1-ULP tie-aware policy. The replay does not alter or claim an alternate search traversal.

## Result

The source-return validation matched on `256` of `256` calls. Policy-selected mapping differences were `{'source_f64': 0, 'compensated_fsum': 42, 'exact_binary64_leaf': 42, 'tie_aware_1ulp': 42}`. This is candidate-level evidence over the observed iterator output, not a production remedy or a claim that the search path changes.

## Claim Boundary

This result does not establish a confirmed Qiskit bug, a numerical fix, an alternate search path, cross-platform determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit.
