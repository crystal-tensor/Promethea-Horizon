# B1/B7 Cone01 R73 Mixed-Orientation Cost-Aware Synthesis Gate

- Method: `b1_b7_cone01_r73_mixed_orientation_cost_aware_synthesis_gate_v0`
- Status: `cone01_r73_mixed_orientation_exact_synthesis_cost_boundary`
- Requirements: `8/8`
- Mixed orientation sequences per packet: `15`
- Total optimizer attempts: `720`
- Exact solution count: `608`
- Packets with reduced-CNOT exact solutions: `3`
- Packets with FT-cost improvement: `0`
- Source minus best exact rotation cost: `[-78, -215, -233]`
- Accepted occurrence removal / proxy-T reduction: `0` / `0`
- B7 credit: `0`

## Interpretation

The direction space is broader than R72: every binary CNOT orientation sequence through three reduced CNOTs is tested for all three semantic packets. Exact candidates still do not lower the pinned FT rotation proxy, so reversing CNOT direction does not yet create an accepted B1/B7 resource win.

## Claim Boundary

- This is a finite local numerical search, not a global synthesis lower-bound theorem.
- No full-circuit rewrite, occurrence removal, proxy-T reduction, reroute, or B7 credit is accepted.
