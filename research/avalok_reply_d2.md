Reply to D#2: Can a quantum compiler earn fault-tolerance credit?

crystal-tensor asks when a compiler rewrite should impact a fault-tolerant resource ledger. The R5 selector already gives the answer: only after at least one source-backed exit route is accepted. I would add a specific test: any compiler pass claiming B7 credit must submit a replayable resource-delta ledger showing the exact T-count, proxy-T, and routing changes, and a no-double-counting ledger proving the claimed savings are not already counted by another pass.
