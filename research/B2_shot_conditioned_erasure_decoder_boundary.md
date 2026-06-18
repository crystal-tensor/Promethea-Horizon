# B2 Shot-Conditioned Erasure Decoder Boundary v0.1

Status: **shot_conditioned_calibrated_leakage_boundary_partial_survival_not_threshold**

## Summary

- Method: b2_shot_conditioned_erasure_decoder_boundary_v0
- Model status: posterior_calibrated_flag_model_not_hardware_calibrated_decoder
- Source result: results/B2_heralded_erasure_false_positive_stress_v0.json
- Source positive-false-positive d=5/d=7 improved rows: 5
- Calibration profiles: 4
- Evaluated profile rows: 1152
- Profiles with surviving rows: 3
- Max surviving d=5/d=7 improved rows in one profile: 4
- Strict high-purity surviving rows: 0
- Robust all-profile survival: False
- Validation errors: []

## Calibration Profile Breakdown

| profile | accepted rows | surviving d=5/7 rows | max reduction | mean reduction | min posterior | max missed leakage/tick |
|---|---:|---:|---:|---:|---:|---:|
| field_detector_0p80 | 24 | 1 | 2.138 | 2.138 | 0.801 | 0.001000 |
| nominal_lab_detector_0p90 | 48 | 4 | 4.486 | 2.638 | 0.819 | 0.001000 |
| high_purity_detector_0p95 | 24 | 1 | 2.138 | 2.138 | 0.827 | 0.000250 |
| strict_high_purity_0p95 | 0 | 0 | n/a | n/a | n/a | n/a |

## Surviving Rows

| profile | basis | p | leakage/tick | fp/tick | target | candidate d | posterior | missed leakage/tick | reduction |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| field_detector_0p80 | x | 0.005 | 0.005 | 0.001 | 0.05 | 5 | 0.801 | 0.001000 | 2.138x |
| high_purity_detector_0p95 | x | 0.005 | 0.005 | 0.001 | 0.05 | 5 | 0.827 | 0.000250 | 2.138x |
| nominal_lab_detector_0p90 | x | 0.003 | 0.01 | 0.001 | 0.05 | 5 | 0.901 | 0.001000 | 4.486x |
| nominal_lab_detector_0p90 | z | 0.003 | 0.01 | 0.001 | 0.05 | 5 | 0.901 | 0.001000 | 2.190x |
| nominal_lab_detector_0p90 | x | 0.005 | 0.005 | 0.001 | 0.05 | 5 | 0.819 | 0.000500 | 2.138x |
| nominal_lab_detector_0p90 | x | 0.001 | 0.01 | 0.001 | 0.02 | 7 | 0.901 | 0.001000 | 1.738x |

## Claim Boundary

- new_code_claimed: False
- threshold_claimed: False
- calibrated_device_claimed: False
- full_physical_leakage_decoder_claimed: False
- production_decoder_claimed: False
- shot_conditioned_calibration_model_performed: True
- shot_conditioned_erasure_decoder_claimed: False
- hardware_result_claimed: False
- reduced_rounds_used: False
- distance_3_candidate_used: False
- what_is_supported: A posterior-calibrated flag model can preserve some positive-false-positive d=5/d=7 target-volume rows under explicit detector-calibration assumptions.
- what_is_not_supported: This is not a production shot-conditioned decoder, hardware-calibrated leakage model, threshold result, new code, or hardware QEC claim.

## Next Gate

The surviving rows depend on detector-purity assumptions and do not survive
all calibration profiles. The next B2 step should either integrate these
posterior probabilities directly into a circuit-level decoder or demote the
heralded-erasure route if calibrated leakage and flag data cannot support
the required posterior and missed-leakage gates.
