# B1/B7 Cone_01 Shared-Theta Factory-Amortization Scaffold

Status: `cone01_shared_theta_factory_amortization_scaffold`

This artifact adds CM-05 bookkeeping for the replayed and logically routed shared-theta objects. It compares per-occurrence synthesis pressure against per-shared-object synthesis pressure.

It is not a physical factory schedule, not an error-budget model, not a semantic rewrite certificate, and not a B7 resource-saving claim.

## Summary

- Candidate windows: `35`
- Shared objects: `4`
- Baseline factory compilation count: `35`
- Shared-object factory compilation count: `4`
- Amortized saved compilation count: `31`
- Baseline proxy-T pressure: `700`
- Shared-object proxy-T pressure: `80`
- Gross proxy-T pressure delta: `620`
- Target proxy-T ledger reduction: `600`
- Factory amortization gate passed: `True`
- Physical factory schedule present: `False`
- Shared error budget present: `False`
- Cost model accepted: `False`
- B7 ledger improvement claimed: `False`
- Validation errors: `0`

## Object Amortization

| object | occurrences | shared compiles | saved compiles | gross proxy-T delta | total hops | max hops |
|---|---:|---:|---:|---:|---:|---:|
| cone01_shared_theta_01 | `16` | `1` | `15` | `300` | `63` | `9` |
| cone01_shared_theta_02 | `10` | `1` | `9` | `180` | `41` | `9` |
| cone01_shared_theta_03 | `6` | `1` | `5` | `100` | `24` | `8` |
| cone01_shared_theta_04 | `3` | `1` | `2` | `40` | `11` | `11` |

## Interpretation

The factory-amortization scaffold is strong enough to keep CM-05 open as positive bookkeeping evidence: the same four theta groups account for 31 amortized compile requests and a gross 620 proxy-T pressure difference. It is still not accepted as B7 savings because the project has no shared synthesis-error budget, no independent physical baseline, and no refreshed B7 ledger.
