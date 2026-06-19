# B1/B7 Cone_01 Line-1381 Exact-Decomposition Pressure Gate

Status: `cone01_line1381_exact_decomposition_pressure_not_accepted`

This artifact consumes T-B1-004am and tests the five remaining off-grid local-U3 parameters on line 1381 against simple exact-decomposition and source-absorption contracts.

## Summary

- Target candidate line: `1381`
- Remaining off-grid parameters tested: `5`
- Parameter indices: `[3, 4, 9, 16, 17]`
- Pi/4 exact parameters: `0`
- Power-of-two pi-grid exact parameters: `0`
- Rational-pi exact parameters: `0`
- Source-absorbed parameters: `0`
- Accepted exact decompositions: `0`
- Remaining unaccepted parameters: `5`
- Accepted full-circuit replay certificates: `0`
- Accepted occurrence/proxy-T reduction: `0` / `0`
- Validation errors: `0`

## Parameter Pressure Rows

| Param index | Value/pi | Pi/4 error | Best dyadic pi grid | Dyadic error | Best rational pi grid | Rational error | Accepted |
|---:|---:|---:|---|---:|---|---:|---|
| 3 | 0.454632085623 | 1.425275e-01 | 29/64 | 4.734649e-03 | 5/11 | 2.721596e-04 | False |
| 4 | -0.365263446443 | 3.621108e-01 | -23/64 | 1.849910e-02 | -61/167 | 1.889553e-05 | False |
| 9 | -0.335026659005 | 2.671191e-01 | -21/64 | 2.168220e-02 | -66/197 | 4.015880e-06 | False |
| 16 | 0.177917927571 | 2.264525e-01 | 11/64 | 1.898442e-02 | 29/163 | 1.199190e-05 | False |
| 17 | 0.134736553557 | 3.621108e-01 | 9/64 | 1.849910e-02 | 64/475 | 9.065023e-07 | False |

## Claim Boundary

This closes only a simple exact-decomposition route. It does not prove that line 1381 cannot be solved by a broader symbolic synthesis, context-aware absorption, or a verified full-circuit replay. The B7 ledger remains unchanged at zero accepted occurrence removals and zero accepted proxy-T reduction.

## Next Required Gate

The next B1/B7 route must leave the local parameter-only setting: either construct a broader symbolic synthesis object for line 1381, absorb the five parameters into neighboring context with replay certificates, or produce a full-circuit replay certificate that prices the remaining rotations honestly.
