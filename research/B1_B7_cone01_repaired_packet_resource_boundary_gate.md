# B1/B7 Cone_01 Repaired Packet Resource Boundary Gate

Status: `cone01_repaired_packet_resource_boundary_not_ledger_accepted`

This artifact consumes the 3/3 exact packet repairs from T-B1-004ai/aj/al and asks whether the repaired reduced-CNOT packet set can be accepted by the B7 ledger.

## Summary

- Packets with bounded exact repairs: `3` / `3`
- Candidate CNOT reduction if accepted: `9`
- Source off-grid parameters: `1`
- Original replacement off-grid parameters: `40`
- Repaired off-grid parameters: `5`
- Off-grid parameter reduction vs original candidate: `35`
- Original incremental proxy-T pressure: `780`
- Repaired incremental proxy-T pressure: `80`
- Packets with remaining off-grid repair: `1`
- Accepted full-circuit replay certificates: `0`
- Accepted occurrence/proxy-T reduction: `0` / `0`
- Validation errors: `0`

## Packet Rows

| Candidate line | Repair gate | CNOT delta | Repaired off-grid params | Incremental proxy-T pressure | Exact residual | Accepted replay |
|---:|---|---:|---:|---:|---:|---|
| 1378 | T-B1-004ai | 3 | 0 | 0 | 9.049428e-13 | False |
| 268 | T-B1-004aj | 3 | 0 | 0 | 6.398929e-13 | False |
| 1381 | T-B1-004al | 3 | 5 | 80 | 6.513934e-13 | False |

## Claim Boundary

The repaired packet set is materially stronger than the original arbitrary-U3 candidate set: off-grid replacement pressure falls from 40 parameters to 5. However, the remaining five off-grid parameters on line 1381, plus the absence of symbolic full-circuit replay certificates, still block B7 ledger acceptance.

## Next Required Gate

The next route must either exact-decompose or absorb the five line-1381 off-grid local-U3 parameters and emit full-circuit replay certificates, or reject the reduced-CNOT route as a ledger-improving rewrite.
