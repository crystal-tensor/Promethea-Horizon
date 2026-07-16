# B9 Reverse Pauli Replay Inverse Gate

- Method: `b9_pauli_action_reverse_inverse_gate_v0`
- Status: `pauli_action_reverse_inverse_checked_not_linear_or_spectral_proof`
- Requirements passed/failed: `13` / `0`
- Fresh Lean/Lake commands returning zero: `3/3`
- Source SHA256: `ba8f328ab30a8f4ae7dff0b230daeafd279fec68b0fb31a4e6e07c622777cddf`
- Transcript SHA256: `87b0eb779a5e127fea04d1a3c71af9480fcf6014bf8f05a07c658ceead5e95f4`

## Supported Result

Lean checks that each Pauli factor replay is self-inverse and that any finite Pauli term followed by its reversed factor list restores the computational-basis state and accumulated plus/minus phase.

## Claim Boundary

This is a finite computational-basis replay inverse certificate, not a complex linear operator, Hermiticity proof, Hamiltonian sum, spectral theorem, Quantum PCP/NLTS theorem, global impossibility result, BQP separation, or quantum-advantage claim.

- R1 [PASS]: Lean and Lake version probes return zero
- R2 [PASS]: All six B9 modules compile together
- R3 [PASS]: The source defines reverse factor-list order
- R4 [PASS]: The source checks the identity action composition boundary
- R5 [PASS]: The source checks phase-plus multiplication
- R6 [PASS]: Each Pauli factor action is self-inverse
- R7 [PASS]: The term theorem uses reverse factor order
- R8 [PASS]: The term proof is lifted inductively over the factor list
- R9 [PASS]: The checked theorem recovers the identity action and input state
- R10 [PASS]: Fresh transcript binds every source and project hash
- R11 [PASS]: The proof is finite replay semantics rather than a spectral theorem
- R12 [PASS]: The source contains no matrix or complex-amplitude machinery
- R13 [PASS]: The source does not claim Quantum PCP, NLTS, BQP, or advantage resolution
