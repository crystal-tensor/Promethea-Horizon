# B1/B7 Cone01 R106 Remote-Origin Materiality Gate

- Target: `T-B1-004hd/T-B7-016m`
- Upstream target: `T-B1-004hc/T-B7-016l`
- Method: `b1_b7_cone01_r106_remote_origin_materiality_gate_v0`
- Status: `cone01_r106_remote_looking_origin_spoof_rejected_no_signature_materiality`
- Model status: `r105_surface_verifier_ready_but_remote_looking_spoof_needs_materiality_gate`

## Result

R106 creates a remote-looking origin packet that passes the R105 surface
verifier, then rejects it on materiality because reviewer-key, detached
signature, third-party CI, and remote-fetch evidence are absent.

## Key Counters

- R105 surface origin accepted: `True`
- Surface gates passed / failed: `16` / `0`
- Remote-looking spoof rejected: `True`
- Material origin accepted: `False`
- Materiality gates passed / failed: `1` / `7`
- Counter transition accepted: `False`
- Counter delta: `0`
- Accepted external reproductions: `0`
- Accepted external falsifications: `0`
- New credit delta: `0`

## Requirements

- `A1` PASS: R106 binds the R105 verifier result, rules, and blocker queue
- `A2` PASS: R106 emits a remote-looking packet that passes R105 surface verification
- `A3` PASS: R106 rejects the packet on materiality gates
- `A4` PASS: R106 keeps counters and new credit at zero
- `A5` PASS: R106 emits blockers for signature, CI, fetch transcript, and single-counter audit

## Artifacts

- Result JSON: `results/B1_B7_cone01_R106_remote_origin_materiality_gate_v0.json`
- Remote-looking packet: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R106-G1-remote-looking-origin-spoof/remote-looking-origin-packet.json`
- R105 surface validation: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R106-G1-remote-looking-origin-spoof/r105-surface-validation.verdict.json`
- Materiality audit: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R106-G1-remote-looking-origin-spoof/remote-origin-materiality-audit.verdict.json`
- Blocker queue: `results/B1_B7_cone01_o3_f4_exit_route_submissions/R106-G1-post-remote-origin-materiality-blocker-queue.json`

## Claim Boundary

R106 is a materiality sentinel. It deliberately shows that a packet can
pass R105 surface checks and still fail because its independence and
signature material are self-declared. It does not move external counters,
grant new credit, or close B7/O3/resource/layout claims.
