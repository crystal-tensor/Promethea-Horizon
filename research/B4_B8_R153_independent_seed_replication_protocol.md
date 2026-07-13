# B4/B8 R153 Independent Seed Replication Protocol

- Backends / hidden rows: `3` / `96`
- Executions / total shots: `288` / `589824`
- Repaired-denominator portfolio mean / bootstrap floors: `-0.005` / `-0.015`
- Groups above -0.02 versus denominator: `3 / 3`
- Casablanca mean floor: `-0.02`
- Independent blocks / block floor: `12` / `10` above `-0.03`
- Maximum within-group block spread: `0.08`
- Severe rows below -0.05: at most `0`
- Challenge executed: `false`

Casablanca replays the accepted R152 novel edge-signature route. Nairobi and
Perth keep their accepted R152 control routes. The challenge expands each
backend from one eight-row set to four independent hidden eight-row blocks,
without selecting, fitting, or changing any route.

This protocol does not establish causal repair, temporal or real-device
transfer, hardware performance, general route-generation advantage, quantum
advantage, BQP separation, a solved frontier, or new credit.
