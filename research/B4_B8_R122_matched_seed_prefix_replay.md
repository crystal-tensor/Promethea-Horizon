# B4/B8 R122 Matched-Seed Prefix Replay

## Summary

- Target: `T-B4-002w/T-B8-003aa/T-B10-009o`
- Upstream target: `T-B4-002v/T-B8-003z/T-B10-009n`
- Method: `b4_b8_r122_matched_seed_prefix_replay_v0`
- Status: `matched_seed_prefix_shot_budget_confidence_boundary`
- Profiles: `ideal, light`
- Shot budgets: `512, 1024, 2048, 4096, 8192`
- Trials per profile/task: `30`
- Maximum replay stream: `8192` shots
- Honest completeness floor: `0.8`
- Point-estimate first crossing: `{'ideal': 4096, 'light': 4096}`
- Confidence-qualified first crossing: `{'ideal': 8192, 'light': None}`
- Total fail-to-pass adjacent transitions: `49`
- Total pass-to-fail adjacent transitions: `20`

- `ideal` point estimate: 512: 0.4333, 1024: 0.5333, 2048: 0.6667, 4096: 0.8667, 8192: 0.9667
- `ideal` minimum Wilson lower: 512: 0.2738, 1024: 0.3614, 2048: 0.4878, 4096: 0.7032, 8192: 0.8333
- `light` point estimate: 512: 0.4333, 1024: 0.6667, 2048: 0.5667, 4096: 0.8000, 8192: 0.8667
- `light` minimum Wilson lower: 512: 0.2738, 1024: 0.4878, 2048: 0.3920, 4096: 0.6269, 8192: 0.7032

R122 removes the largest comparability defect in R121. Within each trial, all
five budgets are prefixes of one ordered 8,192-shot record stream and reuse the
same hidden signed-observable bundle. Point estimates and 95% Wilson lower
bounds are reported separately. A point estimate above 0.80 is not promoted to
a confidence-qualified result unless the weakest task's Wilson lower bound also
reaches 0.80.

## Requirements

- `P1` PASS: accepted R121 shot-budget boundary is consumed
- `P2` PASS: all budgets are prefixes of one ordered stream per trial
- `P3` PASS: the hidden bundle is shared across budgets within each trial
- `P4` PASS: thirty paired trials cover every profile and task
- `P5` PASS: point estimates and Wilson intervals are both reported
- `P6` PASS: adjacent paired pass/fail transitions are materialized
- `P7` PASS: all profile circuits are materialized
- `P8` PASS: synthetic profiles are not mislabeled as hardware evidence
- `P9` PASS: B4/B8/B10 advantage and BQP claims remain false
- `P10` PASS: confidence-qualified crossing remains separate from point crossing

## Claim Boundary

Supported: a paired synthetic Aer replay that isolates shot-budget effects more
cleanly than R121. Not supported: a universal monotonic sampling law, calibrated
backend evidence, real hardware execution, protocol or cryptographic soundness,
sampling hardness, quantum advantage, BQP separation, or B10 credit.
