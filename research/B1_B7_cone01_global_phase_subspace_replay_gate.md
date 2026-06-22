# B1/B7 cone_01 Global-Phase Subspace Replay Gate

## Summary

- Method: `b1_b7_cone01_global_phase_subspace_replay_gate_v0`
- Status: `cone01_global_phase_subspace_replay_passed_not_symbolic_certificate`
- Source QASM: `results/b1_native_t_resource_optimizer/qasmbench_medium_exact/gcm_h6.qasm`
- Candidate QASM: `results/B1_B7_cone01_qasm2_candidate_rewrite_gate/gcm_h6_line268_line1381_candidate.qasm`
- Global phase anchor: `zero` / `-2.4388324596671658` radians
- Input cases: `21` total; `6` basis anchors and `15` coherent pair superpositions
- Global-phase subspace replay passed: `True`
- Max global-anchor phase delta radians: `3.142993331217661e-14`
- Min overlap magnitude: `0.9999999999999772`
- Min fidelity / max infidelity: `0.9999999999999547` / `4.529709940470639e-14`
- Max anchored amplitude / probability delta: `1.3928889642636009e-13` / `1.074140776324839e-14`
- Accepted full-circuit patch / replay / occurrence / proxy-T reduction: `0` / `0` / `0` / `0`
- Validation errors: `0`

## Input Cases

| Case | Kind | Anchor phase delta | Fidelity | Max probability delta | Passed |
|---|---|---:|---:|---:|---|
| `zero` | `basis_subspace_anchor` | `-0.0` | `0.9999999999999551` | `5.551115123125783e-16` | `True` |
| `x_q0` | `basis_subspace_anchor` | `-0.0` | `0.9999999999999551` | `5.551115123125783e-16` | `True` |
| `x_q4` | `basis_subspace_anchor` | `1.677392667334493e-14` | `0.9999999999999547` | `4.996003610813204e-16` | `True` |
| `x_q14` | `basis_subspace_anchor` | `-5.083008082831797e-16` | `0.9999999999999589` | `4.996003610813204e-16` | `True` |
| `x_q0_q4` | `basis_subspace_anchor` | `1.677392667334493e-14` | `0.9999999999999547` | `4.996003610813204e-16` | `True` |
| `x_q4_q14` | `basis_subspace_anchor` | `1.609619226230069e-14` | `0.9999999999999583` | `7.771561172376096e-16` | `True` |
| `sup_zero_plus_x_q0` | `coherent_pair_superposition` | `1.2707520207079492e-15` | `0.9999999999999583` | `1.249000902703301e-16` | `True` |
| `sup_zero_minus_x_q0` | `coherent_pair_superposition` | `1.2707520207079492e-15` | `0.9999999999999583` | `1.249000902703301e-16` | `True` |
| `sup_zero_iplus_x_q0` | `coherent_pair_superposition` | `1.2707520207079492e-15` | `0.9999999999999583` | `1.249000902703301e-16` | `True` |
| `sup_zero_plus_x_q4` | `coherent_pair_superposition` | `2.6431642030725342e-14` | `0.9999999999999578` | `1.074140776324839e-14` | `True` |
| `sup_zero_minus_x_q4` | `coherent_pair_superposition` | `-8.556396939433526e-15` | `0.9999999999999587` | `1.066507993030541e-14` | `True` |
| `sup_zero_iplus_x_q4` | `coherent_pair_superposition` | `-3.142993331217661e-14` | `0.9999999999999591` | `4.697631172945194e-15` | `True` |
| `sup_x_q0_plus_x_q14` | `coherent_pair_superposition` | `4.235840069026497e-16` | `0.9999999999999576` | `5.551115123125783e-16` | `True` |
| `sup_x_q0_minus_x_q14` | `coherent_pair_superposition` | `4.235840069026497e-16` | `0.9999999999999576` | `5.551115123125783e-16` | `True` |
| `sup_x_q0_iplus_x_q14` | `coherent_pair_superposition` | `5.930176096637096e-16` | `0.9999999999999576` | `5.551115123125783e-16` | `True` |
| `sup_x_q4_plus_x_q0_q4` | `coherent_pair_superposition` | `1.75363778857697e-14` | `0.9999999999999576` | `1.1102230246251565e-16` | `True` |
| `sup_x_q4_minus_x_q0_q4` | `coherent_pair_superposition` | `1.75363778857697e-14` | `0.9999999999999576` | `1.1102230246251565e-16` | `True` |
| `sup_x_q4_iplus_x_q0_q4` | `coherent_pair_superposition` | `1.75363778857697e-14` | `0.9999999999999576` | `1.1102230246251565e-16` | `True` |
| `sup_x_q0_q4_plus_x_q4_q14` | `coherent_pair_superposition` | `1.685864347472546e-14` | `0.9999999999999576` | `3.885780586188048e-16` | `True` |
| `sup_x_q0_q4_minus_x_q4_q14` | `coherent_pair_superposition` | `1.685864347472546e-14` | `0.9999999999999576` | `3.885780586188048e-16` | `True` |
| `sup_x_q0_q4_iplus_x_q4_q14` | `coherent_pair_superposition` | `1.685864347472546e-14` | `0.9999999999999578` | `3.885780586188048e-16` | `True` |

## Claim Boundary

The T-B1-004av QASM2 candidate has sampled subspace replay under one global phase anchor across basis anchors and coherent pair superpositions.

Unsupported claims:

- This is not a symbolic unitary-equivalence proof for arbitrary input states.
- This is not an exhaustive input-space replay certificate.
- This is not an accepted B7 occurrence-removing certificate.
- This does not recover the dropped line-1378 overlap delta.
- This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.

## Interpretation

This gate fixes one global phase using the zero-input replay and reuses it across a small basis-anchor subspace and coherent pair superpositions. It is stronger than independently aligned sampled inputs, but it remains sampled numerical evidence with zero B7 ledger credit.
