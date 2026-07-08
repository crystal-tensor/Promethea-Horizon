# B1/B7 Cone01 R104 External-Origin Attestation Contract Gate

- Target: `T-B1-004hb/T-B7-016k`
- Upstream target: `T-B1-004ha/T-B7-016j`
- Method: `b1_b7_cone01_r104_external_origin_attestation_contract_gate_v0`
- Status: `cone01_r104_external_origin_attestation_contract_ready_no_counter_move`
- Model status: `r103_rejected_counter_packet_until_origin_attestation_and_nonlocal_replay_exist`

## Result

R104 turns the R103 origin blocker into a concrete external-origin
attestation contract. It emits a fillable template and rejects a local
placeholder that reuses R101/R103 local artifacts.

## Key Counters

- Required attestation fields: `20`
- Local placeholder rejected: `True`
- Origin attestation accepted: `False`
- Counter transition accepted: `False`
- Gates passed / failed: `5` / `7`
- Counter delta: `0`
- Accepted external reproductions: `0`
- Accepted external falsifications: `0`
- New credit delta: `0`

## Requirements

- `A1` PASS: R104 binds the R103 audit verdict and blocker queue
- `A2` PASS: R104 emits the external-origin attestation contract and template
- `A3` PASS: R104 rejects the local placeholder origin attestation
- `A4` PASS: R104 keeps counters and new credit at zero
- `A5` PASS: R104 emits blockers for signed origin, nonlocal bundle, and single-counter audit

## Artifacts

- Result JSON: `results/B1_B7_cone01_R104_external_origin_attestation_contract_gate_v0.json`
- Origin contract: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R104-G1-external-origin-attestation-contract.json`
- Attestation template: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R104-G1-external-origin-attestation.template.json`
- Local placeholder: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R104-G1-local-placeholder-origin-attestation.json`
- Preflight verdict: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R104-G1-external-origin-attestation-preflight.verdict.json`
- Blocker queue: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R104-G1-post-origin-attestation-contract-blocker-queue.json`

## Claim Boundary

R104 is an intake-contract gate. It does not prove external origin,
does not accept a counter transition, does not grant new credit, and
does not close B7/O3/resource/layout claims.
