# B4/B8 R155 Execution-Mode Attribution Protocol

- Profiles / process replicates / total processes: `4` / `2` / `8`
- Rows / circuit executions / shots: `768` / `2304` / `4718592`
- Within-profile comparisons: `4`
- Serial-reference comparisons: `7`
- Stored-R153 row comparisons: `768`
- New hidden seeds / selection / route changes: `0` / `false` / `false`
- Contract SHA-256: `76f7939cdac7aa3b89cfb5f90a89e8d424a28cef5ec849434b4dc5858a4dfc9a`
- Execution started: `false`

## Frozen 2x2 Matrix

- `clamped_serial`: R154 replacement-replay control; environment threads `1`; Aer mode `explicit_serial`.
- `clamped_default_aer`: R153 code-equivalent Aer option path; environment threads `1`; Aer mode `no_explicit_parallel_override`.
- `four_thread_serial`: thread-environment stress with serial Aer execution; environment threads `4`; Aer mode `explicit_serial`.
- `four_thread_default_aer`: thread-environment and default-Aer interaction stress; environment threads `4`; Aer mode `no_explicit_parallel_override`.

R155 separates process thread clamps from explicit Aer serialization. Every
cell runs twice in separate operating-system processes and hashes every fresh
automatic OpenQASM 3 circuit, all three count vectors, and every scientific
row. Diagnostic completion does not require zero mismatch: a mismatch is valid
evidence if it is complete, bound to the frozen cell, and reproduced honestly.

This unopened protocol makes no causal attribution and introduces no hidden
statistical evidence. It does not support temporal or real-device transfer,
hardware performance, general route-generation advantage, quantum advantage,
BQP separation, a solved frontier, or new credit.
