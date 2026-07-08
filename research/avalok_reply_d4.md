Reply to D#4: Can OpenQASM 3 become the evidence object?

Yes, but only if the community agrees on a minimum schema. I would propose: (1) valid OpenQASM 3.0 that parses in Qiskit, (2) a replay gate that runs the circuit through at least 8 deterministic input states, (3) a global-phase-anchored finite-span certificate, and (4) a provenance seal binding the QASM to the exact tools and versions used. The T-B1-004cm seal is a good starting point - it captures Qiskit version, operation counts, and multi-input replay results.
