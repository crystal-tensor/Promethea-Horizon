# B4/B8/B10 R177 Linux x86-64 Protocol

- Status: `preregistered_unopened`
- Protocol payload hash: `7ebca6d9dfef8d84e432e8d18af1f66835c1b192c12a2748fbec573c6d7d58d0`
- Contract payload hash: `306921baf18757ece97f7f20aa34e5e660971478f1cdb56b39aa13528f912d19`
- Execution: unopened until a public Discussion is created

## Research Question

Does an independently built Ubuntu x86-64 accelerator reproduce the full R176 exact-selection result and remain inside the same frozen local performance gates?

## Frozen Matrix

The workflow fixes `39` isolated Linux x86-64 workers, `2400` recorded calls, and `624` warmups across source f64, R175 BigUint, and R176 fixed exact scoring.

## Performance Gates

Fixed/source must remain at most `3.0` per cell and `2.5` aggregate; fixed/BigUint must remain at most `0.9` aggregate; peak RSS must remain at most `1.25` relative to source.

## Claim Boundary

This is a preregistered Ubuntu x86-64 build and replay contract. It does not claim an upstream patch, production remedy, confirmed Qiskit bug, successful cross-platform result, hardware evidence, quantum advantage, BQP separation, solved B4/B8/B10, or new credit before execution.
