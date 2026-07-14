# B4/B8 R166 Independent Candidate Verifier

- Status: `independent_reproduction_complete`
- Classification: `independent_reproduction_confirmed_adversarial_tamper_rejected`
- Profiles / replays: `3` / `256`
- Candidate rows verified: `256` / `256`
- Source-return matches recomputed: `256` / `256`
- Payload hash: `2a8160008b14dc6738c179d9921b5a69746c041b97e2ff92ab6bc59b01f4e7c5`

## Research Question

Does an independent implementation recover the R165 candidate-selection result, and does it reject altered candidate evidence?

## Method

R166 reads only the committed R165 result rows and profile manifests. It recomputes binary64, compensated, exact-leaf, and 1-ULP selection using a separate standard-library implementation, then checks row and manifest hashes. It does not call Qiskit or import the R165 executor.

## Result

The independent verifier recovered `256` of `256` source-return matches, `298` complete candidates, and the same policy-change counts `{'source_f64': 0, 'compensated_fsum': 42, 'exact_binary64_leaf': 42, 'tie_aware_1ulp': 42}`. Hash tampering was rejected: `True`; a rehashed but false stored selection was rejected by recomputation: `True`.

## Claim Boundary

This confirms reproducibility of the committed candidate-level evidence and the verifier's rejection behavior. It does not establish a production mapping change, an alternate search path, a confirmed Qiskit bug, cross-platform determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit.
