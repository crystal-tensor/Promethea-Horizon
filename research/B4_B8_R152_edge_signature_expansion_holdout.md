# B4/B8 R152 Edge-Signature Expansion Holdout

- Preregistered verdict: ACCEPT
- Groups / trial rows / executions: `3` / `24` / `72`
- Portfolio repaired-automatic mean / bootstrap lower: `+0.02626896` / `+0.01927970`
- Portfolio repaired-denominator mean / bootstrap lower: `+0.00488735` / `+0.00183043`
- Groups above -0.02 versus denominator: `3 / 3`
- Severe rows below -0.05: `0`
- Semantic passes: `6 / 6`
- Conditions passed / failed: `10` / `0`
- New credit delta: `0`

## Backend Evidence

- `FakeCasablancaV2`: repaired-denominator `-0.00336195`, repaired-auto `+0.01998196`, minimum `-0.00936479`, severe rows `0`.
- `FakeNairobiV2`: repaired-denominator `+0.00927928`, repaired-auto `+0.03440341`, minimum `-0.00068877`, severe rows `0`.
- `FakePerth`: repaired-denominator `+0.00874473`, repaired-auto `+0.02442152`, minimum `-0.00119276`, severe rows `0`.

## Acceptance Conditions

- A1 PASS: contract, protocol, routes, denominators, and bindings remain exact; value True, threshold True.
- A2 PASS: groups, rows, executions, and same-seed arms; value [3, 24, 72], threshold [3, 24, 72].
- A3 PASS: all repaired and denominator routes retain semantics; value [6, 0.9999999999999956], threshold [6, 0.9999999999].
- A4 PASS: portfolio repaired versus automatic noninferiority; value [0.02626896343338125, 0.01927970211882911], threshold [-0.005, -0.01].
- A5 PASS: portfolio repaired versus strong denominator noninferiority; value [0.004887350805534725, 0.001830429968175647], threshold [-0.005, -0.015].
- A6 PASS: all groups above negative 0.02 versus denominator; value 3, threshold 3.
- A7 PASS: severe row regressions below negative 0.05; value 0, threshold 0.
- A8 PASS: Casablanca repaired mean clears negative 0.02; value -0.003361950101780184, threshold -0.02.
- A9 PASS: commitment, hidden rows, reveal, and transcript; value True, threshold True.
- A10 PASS: forbidden claims and credit remain false; value 0, threshold 0.

## Claim Boundary

Supported only if accepted: one preregistered finite dense-XY simulated-noise
verdict for a novel Casablanca edge signature with two preserved control
routes. Not supported: causal repair, temporal transfer, real-device transfer,
hardware performance, general route-generation advantage, quantum advantage,
BQP separation, solved B4/B8/B10, or new credit.
