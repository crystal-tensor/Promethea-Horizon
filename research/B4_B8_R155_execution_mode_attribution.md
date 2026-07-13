# B4/B8 R155 Execution-Mode Attribution

- Diagnostic completion: **ACCEPT**
- Processes / rows / circuit executions: `8` / `768` / `2304`
- Within-profile comparisons: `4`
- Serial-reference comparisons: `7`
- Stored-R153 comparisons: `8`
- Within-profile component mismatches: `9`
- Serial-reference component mismatches: `15`
- Stored-R153 core-row mismatches: `3`
- Unstable cells: `3`
- R153 transient reproduced / not reproduced: `true` / `false`
- Causal attribution supported: `false`
- Conditions passed / failed: `10` / `0`
- New hidden seeds / new credit: `0` / `0`

## Classification

- Explicit Aer serialization effect detected: `false`
- Thread-environment effect detected: `false`
- Environment x Aer interaction detected: `false`
- Effect classification blocked by unstable cells: `true`
- First observed divergence layer: `automatic_transpilation`
- Aer-sampling-only explanation excluded for observed mismatches: `true`
- Unique within-profile mismatch keys: `[['FakeNairobiV2', 21]]`
- Automatic QASM variants: `2`
- Automatic-fidelity variant delta: `0.000210775927`
- One-row implied portfolio-mean delta: `0.000002195583`
- All processes match the serial reference: `false`
- All processes match stored R153 core rows: `false`

## Acceptance Conditions

- A1 PASS: contract, protocol, R154/R153 evidence, seeds, routes, and sources remain exact; value `True`, threshold `True`.
- A2 PASS: eight processes complete 768 rows and 2304 circuits; value `[8, 768, 2304]`, threshold `[8, 768, 2304]`.
- A3 PASS: all process manifests are complete and independently identified; value `[8, 8]`, threshold `[8, 8]`.
- A4 PASS: four within-profile comparisons are complete; value `4`, threshold `4`.
- A5 PASS: seven serial-reference comparisons are complete; value `7`, threshold `7`.
- A6 PASS: eight stored-R153 core-row comparisons are complete; value `8`, threshold `8`.
- A7 PASS: the R153 code-equivalent cell is explicitly classified; value `True`, threshold `True`.
- A8 PASS: Aer, thread-environment, interaction, and non-reproduction classifications are emitted; value `[True, True, True, True]`, threshold `[True, True, True, True]`.
- A9 PASS: all process artifacts and comparison bindings are complete; value `True`, threshold `True`.
- A10 PASS: new seeds, selection, route changes, and forbidden claims remain false; value `0`, threshold `0`.

## Claim Boundary

Diagnostic completion means the frozen matrix ran and recorded every comparison.
It does not turn a non-reproduced transient into proof that the original event
was impossible, and a single localized pattern would require an expanded
replication block before causal attribution. No new hidden statistical evidence,
temporal or real-device transfer, hardware performance, general route-generation
advantage, quantum advantage, BQP separation, solved frontier, or credit is
claimed.
