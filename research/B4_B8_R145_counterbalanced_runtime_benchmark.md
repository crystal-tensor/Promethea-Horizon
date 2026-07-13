# B4/B8 R145 Counterbalanced Runtime Benchmark

- Preregistered verdict: ACCEPT
- Secret-selected schedule: `BAAB`
- Full repeat seconds: `[66.60863275, 66.715555875]`
- Halving repeat seconds: `[32.587035541, 32.525027459]`
- Pooled runtime reduction: `51.16%`
- Adjacent pair runtime reductions: `51.08%, 51.25%`
- Pair-reduction spread: `0.17%`
- Pooled halving/full per-execution ratio: `1.034204`
- Full / halving selection replay: `24 / 24`, `24 / 24`
- Shared setup / warmup seconds: `6.332279` / `0.297164`
- Conditions passed / failed: `10 / 0`
- New credit delta: `0`

## Acceptance Conditions

- A1 PASS: protocol and source bindings remain exact; value True, threshold True.
- A2 PASS: per-repeat execution counts; value [[1728, 1728], [816, 816]], threshold [[1728, 1728], [816, 816]].
- A3 PASS: two full repeats reproduce R142 selections; value 24, threshold 24.
- A4 PASS: two halving repeats reproduce R143 selections; value 24, threshold 24.
- A5 PASS: pooled execution-loop runtime reduction; value 0.5116260322188029, threshold >= 0.30.
- A6 PASS: each adjacent pair runtime reduction; value [0.5107685866589118, 0.5124821035750682], threshold each >= 0.20.
- A7 PASS: pair runtime-reduction spread; value 0.001713516916156399, threshold <= 0.15.
- A8 PASS: pooled halving/full per-execution runtime ratio; value 1.0342036964778292, threshold 0.5 to 2.0.
- A9 PASS: secret schedule and transcript hashes verify; value BAAB, threshold ABBA or BAAB from committed secret.
- A10 PASS: downstream claims and credit remain false; value 0, threshold 0.

## Claim Boundary

Supported only if accepted: one same-machine counterbalanced repeated-order
execution-loop timing result. Not supported: cross-machine or cross-calibration
transfer, hardware or cloud billing savings, protocol soundness, quantum
advantage, BQP separation, solved B4/B8/B10, or new credit.
