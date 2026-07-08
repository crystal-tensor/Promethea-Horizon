# B1/B7 Cone01 R97 Evidence-File Materiality Gate

- Target: `T-B1-004gu/T-B7-016d`
- Upstream target: `T-B1-004gt/T-B7-016c`
- Method: `b1_b7_cone01_r97_evidence_file_materiality_gate_v0`
- Status: `cone01_r97_evidence_file_materiality_rejects_spoof_transcript`
- Model status: `r96_validator_ready_but_file_materiality_required`

## Result

R97 hardens the R96 transcript validator by requiring declared evidence
files to exist and match their SHA-256 claims. It emits materiality rules,
a filled-looking spoof transcript, and a validation verdict that rejects
the spoof because its evidence files are missing and hashes are fake.

## Key Counters

- Base validator gates: `18`
- Materiality gates: `10`
- Evidence file pairs: `6`
- Spoof transcript rejected: `True`
- Materiality validation accepted: `False`
- Review transcript accepted: `False`
- Maintainer verdict accepted: `False`
- Failed materiality gates: `5`
- Counter delta: `0`
- Accepted external reproductions: `0`
- Accepted external falsifications: `0`
- New credit delta: `0`

## Requirements

- `A1` PASS: R97 binds the R96 result, validator rules, empty validation, and blocker queue
- `A2` PASS: R97 emits materiality rules that require evidence file existence and hash matching
- `A3` PASS: R97 emits a filled-looking spoof transcript negative control
- `A4` PASS: R97 rejects the spoof transcript on material evidence gates
- `A5` PASS: R97 keeps maintainer verdict, external counters, and new credit at zero
- `A6` PASS: R97 keeps O3, resource-saving, and physical-layout claims closed
- `A7` PASS: R97 emits blockers for real files, SHA-256 materiality, and nonfake hashes

## Artifacts

- Result JSON: `results/B1_B7_cone01_R97_evidence_file_materiality_gate_v0.json`
- Materiality rules: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R97-G1-evidence-file-materiality-rules.json`
- Spoof transcript: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R97-G1-spoofed-review-transcript.json`
- Spoof validation verdict: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R97-G1-spoofed-review-transcript-materiality.verdict.json`
- Stdout: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R97-G1-evidence-file-materiality.stdout.txt`
- Blocker queue: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R97-G1-post-materiality-blocker-queue.json`

## Claim Boundary

R97 is a materiality hardening gate. It does not accept a transcript yet,
does not accept a maintainer verdict, does not increment reproduction or
falsification counters, does not grant new B7 credit, and does not close
1.25x, O3, physical layout, resource-saving, paper, patent, funding, or
product-readiness claims.
