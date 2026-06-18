# B1/B7 Cone_01 Shared-Theta Independent-Baseline Scaffold

Status: `cone01_shared_theta_independent_baseline_scaffold`

This artifact adds CM-07 bookkeeping for the replayed, logically routed, factory-amortized, and error-budgeted shared-theta objects. It compares the baseline occurrence ledger with the shared-object ledger and confirms that the gross cache signal has not been double-counted as accepted occurrence-ledger savings.

It is not an independent physical device baseline, not a semantic rewrite certificate, not a refreshed B7 ledger, and not a resource-saving claim.

## Summary

- Candidate windows: `35`
- Shared objects: `4`
- Baseline occurrences: `35`
- Baseline/shared-object proxy-T pressure: `700` / `80`
- Gross proxy-T pressure delta: `620`
- Occurrence-ledger removed occurrences: `0`
- Occurrence-ledger proxy-T reduction: `0`
- Double-counted occurrences / proxy-T: `0` / `0`
- Independent baseline gate passed: `True`
- Independent physical baseline present: `False`
- Device-calibrated baseline present: `False`
- Refreshed B7 ledger present: `False`
- Cost model accepted: `False`
- B7 ledger improvement claimed: `False`
- Validation errors: `0`

## Independent Baseline Rows

| object | baseline occurrences | shared objects | baseline proxy-T | shared proxy-T | gross delta | double-counted proxy-T |
|---|---:|---:|---:|---:|---:|---:|
| cone01_shared_theta_01 | 16 | 1 | 320 | 20 | 300 | 0 |
| cone01_shared_theta_02 | 10 | 1 | 200 | 20 | 180 | 0 |
| cone01_shared_theta_03 | 6 | 1 | 120 | 20 | 100 | 0 |
| cone01_shared_theta_04 | 3 | 1 | 60 | 20 | 40 | 0 |

## Interpretation

This closes the CM-07 accounting-baseline gap only as a scaffold. The next cost-model blocker is CM-08: a refreshed B7 ledger that actually accepts the model and improves the gcm_h6 minimum row. Until that exists, the accepted B7 ledger reduction remains zero.
