# B4/B8/B10 R182 Protocol Count-Label Amendment

- Status: `public_correction_execution_unopened`
- Amendment payload hash: `747065513098d25f90e977b5d548219ca0d6944dd8b40840f97c17e55c348dfb`
- Amended protocol hash: `c4108dd5cab9d33cfe6a69f7822892f8ae4a151d6d3c4b5f8f41c2bd297dbe03`
- Scientific execution: unopened

## Correction

The v0 workload arithmetic is internally consistent at the cell level but two aggregate field names incorrectly say `exact_policy`. Thirteen cells times 32 measurements equals 416 measurements per policy; across three exact policies the total is 1,248. Thirteen cells times 8 warmups equals 104 warmups per policy; across three policies the total is 312.

## Authoritative Counts

- Cells per policy: `13`
- Measurements per cell: `32`
- Warmups per cell: `8`
- Measurements per policy: `416`
- Warmups per policy: `104`
- Measurements across all policies: `1248`
- Warmups across all policies: `312`

## Claim Boundary

No workload cell, replay count, warmup count, hypothesis, threshold, policy, or acceptance requirement changed. This amendment corrects aggregate labels before any R182 build or measured worker starts. It is not experimental evidence or new credit.
