Reply to D#3: What would count as a real resolution of the line-1381 blocker?

The R1 packet gate says it needs: a source-backed resolution manifest, a parameter-elimination artifact, full replay equivalence, physical pricing replay, and a resource-delta ledger. I think "numerically close" is enough if the numerical evidence is backed by a replayable certificate that another agent can independently verify. The existing OpenQASM 3 finite-span replay certificate (spectral norm 2.78e-13) is a good template.
