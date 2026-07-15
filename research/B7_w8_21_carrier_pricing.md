# B7 w8_21 Explicit Carrier Pricing

- Status: `explicit_carrier_exact_replay_zero_resource_gain`
- Classification: `carrier_aware_semantic_control_and_commutation_price`
- Contexts tested: `7`
- Exact local-carrier replays: `7/7`
- Exact Rz/CX commutation identities: `7/7`
- Max local-carrier residual: `1.630271e-16`
- Max commutation residual: `0.000000e+00`
- Validation errors: `0`

## Heuristic question

If the external Rz cannot disappear inside the five-parameter normal form, what does the honest carrier cost look like when we keep it or commute it through a CX boundary?

## Exact carrier control

The explicit target-local carrier `Rz(f)` is retained after the exact two-CNOT normal form. All seven real source contexts replay exactly. The carrier-aware construction has 2 CNOTs and 6 arbitrary parameters, exactly matching the source context; it produces no resource saving.

The commutation identity `Rz_target(theta) CX = CX (CX Rz_target(theta) CX)` also passes for all seven angles. In the declared construction, moving the carrier across the CX introduces a conjugated carrier with two additional CNOTs, giving 4 CNOTs and 6 arbitrary parameters.

## Boundary

This is a positive semantic control and a cost certificate for two explicit carrier placements, not a theorem that all possible carriers are necessary. No occurrence removal, proxy-T reduction, or B7 credit is accepted.

## Next route

Only an alternative nonlocal scaffold with fewer than six arbitrary rotations and without the two-CNOT commuted-carrier penalty can change the ledger.
