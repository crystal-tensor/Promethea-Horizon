# B1/B7 cone_01 Line-1381 Leave-One-Out Parameter Gate

- Method: `b1_b7_cone01_line1381_leave_one_out_parameter_gate_v0`
- Status: `cone01_line1381_no_single_parameter_free_removal`
- Model status: `each_current_line1381_off_grid_parameter_is_leave_one_out_required`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Source five-parameter repair: `results/B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json`
- Source pricing dominance: `results/B1_B7_cone01_union_region_pricing_dominance_gate_v0.json`

## Result

- Current line-1381 off-grid parameter indices: `[3, 4, 9, 16, 17]`
- Base five-parameter residual: `6.513210005207597e-13`
- Leave-one-out rows: `5`
- Exact pass / fail: `0` / `5`
- Best leave-one-out residual: `0.09892087709180968` at parameter `3`
- Worst leave-one-out residual: `0.288314847983953` at parameter `4`
- Minimum residual ratio to exact tolerance: `9892087.709180968`
- Single-parameter free removal accepted: `False`
- Accepted occurrence / proxy-T reduction / B7 claim: `0` / `0` / `False`

## Leave-One-Out Rows

| Fixed parameter | Snap error | Reoptimized indices | Residual | Exact |
| --- | ---: | --- | ---: | --- |
| 3 | 0.142527506515 | `[4, 9, 16, 17]` | 0.0989208770918 | False |
| 4 | 0.362110796574 | `[3, 9, 16, 17]` | 0.288314847984 | False |
| 9 | 0.267119127289 | `[3, 4, 16, 17]` | 0.135804589681 | False |
| 16 | 0.226452509199 | `[3, 4, 9, 17]` | 0.105965133408 | False |
| 17 | 0.362110796574 | `[3, 4, 9, 16]` | 0.213640129389 | False |

## Claim Boundary

- This is a scaffold-local leave-one-out pressure gate, not a global minimality theorem.
- The result blocks a cheap single-parameter removal claim for line 1381, but it does not remove, absorb, or symbolically decompose the five-parameter burden.
