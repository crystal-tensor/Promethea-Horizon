# B4/B8/B10 R175 Post-Run Adjudication

- Frozen result payload: `1ff039f6c9ed14831ec2b58e8053da523aa4c01f8d873a96b7f3c39f72439067`
- Decision: `integrated_rust_exact_score_rejected_on_frozen_matrix`
- Requirements: `13/14`; failed requirement: `P10`
- Credit change: `0`

## Why This Note Exists

The frozen result's structured status, requirement ledger, summary, and Markdown report all record a performance rejection. Its generated `claim_boundary.what_is_supported` sentence nevertheless says that the entry point passes the local timing gate. That sentence is an unconditional generator-text defect and conflicts with the frozen numeric evidence.

## Adjudication Rule

The structured requirement ledger controls the verdict. The aggregate exact/source median-time ratio is `2.5435627081021086` against a maximum of `2.5`, and the maximum cell ratio is `3.7348561515107708` against a maximum of `3.0`. Therefore P10 fails and R175 is rejected. The process peak-RSS ratio of `1.0180527696343158` passes its `1.25` limit, but a memory pass cannot override the timing failure.

The frozen result is retained unchanged so its public preregistration and independent-oracle binding remain auditable. No threshold was changed, no R175 rerun was selected, and no production, hardware, advantage, BQP, solved-frontier, or credit claim is admitted.

## Next Gate

R176 must preregister a new implementation and matrix before execution. A fixed-width or exponent-normalized exact accumulator is a candidate hypothesis; it must preserve all R175 correctness cases while meeting newly frozen timing and memory limits.
