# B1/B7 Cone01 R72 Source-Backed Delta Preflight Gate

## Summary

- Status: `cone01_r72_source_backed_delta_preflight_rejects_metadata_positive_row`
- Base R71 accepted metadata-positive row: `True`
- Hardened source-backed accepted: `False`
- Hardened failed gates: `8`
- R1 failed requirements: `['P6', 'P7', 'P8']`
- R2 failed requirements: `['P6', 'P7', 'P8']`
- Accepted exit routes: `0`
- Accepted occurrence removal: `0`
- Accepted proxy-T reduction: `0`
- B7 credit delta: `0`
- Blocker queue hash: `3831fac3389f15a40f3bba857670802c903d808791dec45feffdcf38f2f3b6ac`

R72 fills a metadata-positive candidate row and shows why that is still not enough. The base R71 shape verifier accepts the row, but the hardened source-backed preflight rejects it because the R1 and R2 source packets still fail their P6/P7/P8 closure obligations.

## Hardened Failed Gates

- `r1_packet_requirements_all_pass`
- `r1_submitted_source_backed_artifact_exists`
- `r1_accepted_occurrence_positive`
- `r1_accepted_proxy_t_positive`
- `r2_packet_requirements_all_pass`
- `r2_submitted_source_backed_artifact_exists`
- `r2_no_double_counting_recovery_valid`
- `ledger_positive_values_not_metadata_only`

## Requirements

- `H1` PASS: metadata-positive candidate is fully populated
- `H2` PASS: base R71 shape verifier accepts the metadata-positive row
- `H3` PASS: hardened source-backed verifier rejects the same row
- `H4` PASS: R1 source packet still fails P6/P7/P8
- `H5` PASS: R2 source packet still fails P6/P7/P8
- `H6` PASS: R72 keeps accepted deltas and B7 credit at zero
- `H7` PASS: R72 emits a D1-D3 blocker queue

## Claim Boundary

- Supported: R72 demonstrates that a metadata-positive R71 row can pass shape checks while failing source-backed R1/R2 closure.
- Not supported: R72 does not accept the candidate row, does not accept occurrence or proxy-T deltas, and does not grant B7 credit.
- Next gate: Replace the metadata-positive candidate with real R1/R2 source-backed artifacts that close P6/P7/P8.

## Artifacts

- `candidate`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R72-R1-source-backed-positive-delta-candidate.json`
- `base_r71_verdict`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R72-R1-source-backed-positive-delta.base-r71-verdict.json`
- `hardened_verdict`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R72-R1-source-backed-positive-delta.hardened-verdict.json`
- `blocker_queue`: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R72-source-backed-delta-blocker-queue.json`
