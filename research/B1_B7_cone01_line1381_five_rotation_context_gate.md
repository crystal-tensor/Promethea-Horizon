# B1/B7 Cone_01 Line-1381 Five-Rotation Context Gate

Status: `cone01_line1381_five_rotation_context_not_accepted`

This artifact consumes T-B1-004aq and tests whether the five remaining line-1381 local-U3 parameters can be absorbed by signed sums of exactly five nearby same-support context rotations in the native optimized `gcm_h6` QASM.

## Summary

- Target candidate line: `1381`
- Support qubits: `[4, 8]`
- Source window: `1369`-`1379`
- Context radius: `+/-64` lines
- Context rotation arguments reviewed: `44`
- Parameters tested: `5`
- Meet-in-the-middle split: `2+3`
- Width-5 combinations per parameter: `34752256`
- Virtual signed combination tests covered: `173761280`
- Width-5 exact absorption parameters: `0`
- Min / max best width-5 grid error: `1.581991109333e-03` / `2.665955174941e-02`
- Accepted replay / occurrence / proxy-T reduction: `0` / `0` / `0`
- Validation errors: `0`

## Parameter Rows

| Param index | Value/pi | Best width-5 error | Best lines | Accepted |
|---:|---:|---:|---|---|
| 3 | 0.454632085623 | 2.665955e-02 | [1322, 1327, 1349, 1351, 1352] | False |
| 4 | -0.365263446443 | 2.746555e-03 | [1327, 1346, 1349, 1351, 1378] | False |
| 9 | -0.335026659005 | 1.557153e-02 | [1311, 1352, 1378, 1381, 1424] | False |
| 16 | 0.177917927571 | 1.581991e-03 | [1327, 1349, 1352, 1378, 1381] | False |
| 17 | 0.134736553557 | 2.746555e-03 | [1327, 1346, 1349, 1351, 1378] | False |

## Claim Boundary

This closes only a bounded exactly-five-rotation context-combination route. It does not rule out six-or-more-rotation symbolic absorption, commutation-aware rewriting, broader symbolic synthesis, or full-circuit replay. The B7 ledger remains unchanged at zero accepted occurrence removals and zero accepted proxy-T reduction.

## Next Required Gate

The next useful route should stop expanding cheap local context width unless it has a new symbolic reason. It should instead build a commutation-aware symbolic/full-circuit replay certificate, honestly price or absorb the line-1381 burden, recover line 1378 without double-counting, or move to a different occurrence-removing scaffold with B7 ledger discipline.
