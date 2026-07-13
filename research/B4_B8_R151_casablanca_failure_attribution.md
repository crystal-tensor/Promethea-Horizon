# B4/B8 R151 Casablanca Failure Attribution

- Attribution executions / shots: `576` / `4718592`
- Casablanca R150 / R151 full deltas: `-0.02570231` / `-0.02653462`
- Casablanca gate-only / readout-only deltas: `-0.02895127` / `+0.00008194`
- Dominant isolated channel: `gate_only`
- Casablanca combined / CX / readout exposure deltas: `+0.04757183` / `+0.05333778` / `+0.00000000`
- Casablanca CX-count delta: `+10`
- Candidate / denominator edge-signature diversity: `31` / `17`
- Generated exposure rank among 48: `4`
- Repair candidate generated: `false`

- `FakeCasablancaV2`: full `-0.02653462`, gate-only `-0.02895127`, readout-only `+0.00008194`, exposure delta `+0.04757183`, CX-count delta `+10`.
- `FakeNairobiV2`: full `+0.00828433`, gate-only `+0.00612212`, readout-only `+0.00039603`, exposure delta `+0.04523099`, CX-count delta `+8`.
- `FakePerth`: full `+0.00388316`, gate-only `+0.00353285`, readout-only `+0.00003280`, exposure delta `-0.00503458`, CX-count delta `+2`.

R151 replays both frozen routes under full, gate-only, and readout-only noise
with 32 fresh attribution seeds. It also binds edge-level calibration exposure
and route-diversity ledgers. The result is diagnostic: it can prioritize the
next zero-hidden-row correction, but it is not causal proof and selects no
repair candidate.

No hardware, general route-generation, quantum-advantage, BQP, solved-frontier,
or new-credit claim is made.
