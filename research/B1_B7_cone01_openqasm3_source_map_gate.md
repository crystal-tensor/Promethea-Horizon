# B1/B7 cone_01 OpenQASM 3 Source-Map Gate

- Method: `b1_b7_cone01_openqasm3_source_map_gate_v0`
- Status: `cone01_openqasm3_source_map_passed_without_b7_resource_credit`
- Model status: `openqasm3_patch_lift_instruction_source_map_is_stable_without_b7_credit`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- QASM2 candidate: `results/B1_B7_cone01_qasm2_candidate_rewrite_gate/gcm_h6_line268_line1381_candidate.qasm`
- OpenQASM 3 artifact: `results/B1_B7_cone01_openqasm3_candidate_export_gate/gcm_h6_line268_line1381_candidate_openqasm3.qasm`

## Evidence

- Raw QASM2 / OpenQASM 3 line counts: 1884 / 1884
- Normalized stream match / instruction count: True / 1878
- Normalized stream SHA-256: `7cd50bea1f5a3c191c5735c0891d3f70f8c07a9cfca9d6e93724e6d49cb36343`
- Source-map rows / raw-line drift count: 1878 / 0
- Source-map SHA-256: `92a499ea6d549426095fbb0fc878f7033027991621a6d5ea1c03cd25d82e9e1e`
- Selected lines / dropped overlap lines: [268, 1381] / [1378]

## Patch Line Map

| QASM2 line | OpenQASM 3 line | Instruction index | Operation | Instruction hash |
| ---: | ---: | ---: | --- | --- |
| 268 | 268 | 263 | rz | `d691861b24af25eec6d32b02febf61df61f6b5665b1cd87ddca729477ec8f42b` |
| 1381 | 1381 | 1375 | U | `42681086a1bf5fb9e2936811eb13d36feec750c13dd4da116b20ce9ca3aa75e0` |
| 1378 | 1378 | 1372 | U | `a60da5f688e761a8917718078ebc62b778834ccaf9e6e08e370e331b6528b703` |

## Claim Boundary

The QASM2 and OpenQASM 3 candidate artifacts have a stable one-to-one instruction source map over 1,878 normalized instructions, including the selected patch lines and the dropped overlap line.

Unsupported claims:

- This is not a Qiskit OpenQASM 3 loader parse.
- This is not a symbolic exact full-circuit unitary proof.
- This is not arbitrary-input or full-Hilbert-space coverage.
- This does not price or eliminate the remaining local-U3 parameters.
- This does not improve the B7 resource ledger.
