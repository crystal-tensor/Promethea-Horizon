# B4/B8 R169 Target-Compatible Complete-Candidate Replay

- Status: `new_input_candidate_replay_complete`
- Classification: `new_input_candidate_replay_complete`
- Profiles / replays: `3` / `192`
- Yielded complete candidates: `576`
- Source-return matches: `192` / `192`
- Payload hash: `038bd7d2ef843dc57b323f57c89a6a23a9c09d9c8c2e210540bb83db2286fea3`

## Research Question

Does a target-compatible OpenQASM 3 interaction graph restore observable candidates while preserving the arithmetic-policy question?

## Method

R169 runs the hash-bound candidate instrumentation on a six-active-qubit target-compatible tree input over FakeNairobiV2. It retains every complete VF2 candidate and replays source binary64, compensated `math.fsum`, exact retained-binary64 leaves, and 1-ULP tie-aware selection without changing the search traversal.

## Result

Across `3` profiles and `192` calls, `576` candidates were yielded, source-return validation matched `192/192`, and policy-change counts were `{'source_f64': 0, 'compensated_fsum': 0, 'exact_binary64_leaf': 0, 'tie_aware_1ulp': 0}`.

## Claim Boundary

This is one target-compatible input candidate-level result. It does not establish cross-input generality, a production mapping change, an alternate search path, a confirmed Qiskit bug, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit.
