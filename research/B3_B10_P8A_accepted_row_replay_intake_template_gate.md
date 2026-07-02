# B3/B10 P8-A Accepted-Row Replay Intake Template Gate

Status: `b3_b10_p8a_accepted_row_replay_intake_open_missing_rows`

## Summary

- Method: `b3_b10_p8a_accepted_row_replay_intake_template_gate_v0`
- Intake template: `B3B10-P8A-accepted-row-replay-intake`
- Source pressure packet hash: `55384c1a143b50d9b334193c3e55151f33bc9511b90dd19a21f22198bf9fe0b0`
- Acceptance submission hash: `40a5a0903de970b798f94d371c4d3cd6ccbdab9e514044ba760e05ac5db756cc`
- Row bundle hash: `64907f6c4fcdedede9e6edb0386a88bda478fc16ab06e462e3c68b1cfb2b5b53`
- Template table hash: `a82007811e0448e2436857aaf22ca5fcf30060a1d032370f8f8e8252848584a2`
- Row templates: `4`
- Required / production key count: `20` / `9`
- Submitted / accepted rows: `0` / `0`
- Denominator wins: `0`
- Requirements passed/failed: `6` / `3`
- Failed requirement IDs: `['A6', 'A7', 'A8']`
- validation_error_count: `0`

## Row Templates

### 1. B3B10-F1-pilot-row-h2-ccpvdz-compiled-ucc-adapt-v0

- Candidate row hash: `df0e080e64011ee171d8e3079e84b71a873a3af7fb460f663c510b4214cd81f0`
- Template hash: `9678bbf01c05e26fc9ea592a446329f1bf6018943b67c7c0af5985e4f68e16b2`
- Submitted row present: `False`
- Accepted full-covariance row: `False`
- Submission artifact path: `results/B3_B10_P8A_accepted_row_replay_submissions/B3B10-F1-pilot-row-h2-ccpvdz-compiled-ucc-adapt-v0.json`

### 2. B3B10-F1-row-h2o-symmetric-oh-stretch-full-covariance-v0

- Candidate row hash: `0615923d8d60fe38aef892188a16df434fbb69634d3bc4c5acd3aea0bb1afce4`
- Template hash: `368b0325b5cbf8acb5a5487494dc4bd477b17224557ae083786425f13f14a4ce`
- Submitted row present: `False`
- Accepted full-covariance row: `False`
- Submission artifact path: `results/B3_B10_P8A_accepted_row_replay_submissions/B3B10-F1-row-h2o-symmetric-oh-stretch-full-covariance-v0.json`

### 3. B3B10-F1-row-n2-bond-stretch-full-covariance-v0

- Candidate row hash: `6b583fb558d7e7b92af40564ca9d58374ef350ce92fa959ae74cdd60cbbb7a38`
- Template hash: `b1af5b183c10f6c257246aa48695349748d008b99c6aad4bc1a668c5b7340554`
- Submitted row present: `False`
- Accepted full-covariance row: `False`
- Submission artifact path: `results/B3_B10_P8A_accepted_row_replay_submissions/B3B10-F1-row-n2-bond-stretch-full-covariance-v0.json`

### 4. B3B10-F1-row-lih-bond-stretch-full-covariance-v0

- Candidate row hash: `df3c3011fe83cdb86a2a97b68f4b36c85a0ca14946a333192e3ea2565b38d46e`
- Template hash: `133bf6c47096b817b08cf1c34f59d09d257196e6442c5c25d979e7d85640d558`
- Submitted row present: `False`
- Accepted full-covariance row: `False`
- Submission artifact path: `results/B3_B10_P8A_accepted_row_replay_submissions/B3B10-F1-row-lih-bond-stretch-full-covariance-v0.json`

## Requirement Results

- A1 [PASS]: P8 pressure gate is current and points to P8-A as a ready packet
- A2 [PASS]: Four F1 candidate row templates are generated
- A3 [PASS]: Every template preserves the submitted F1 packet hashes
- A4 [PASS]: P8-A row schema and production evidence keys are fixed
- A5 [PASS]: Templates carry provenance only and preserve zero-credit boundary
- A6 [FAIL]: Submitted P8-A row replay artifacts exist for all four candidate rows
- A7 [FAIL]: Production replay keys are populated for all submitted P8-A rows
- A8 [FAIL]: At least one submitted P8-A row is accepted as a full-covariance row
- A9 [PASS]: No P8-A template promotes B3, B10, advantage, or BQP credit

## Claim Boundary

- Supported: P8-A now has four row-level intake templates for H2, H2O, N2, and LiH. The templates bind the submitted F1 packet hashes and identify the exact production replay keys required before any row can be accepted.
- Not supported: No P8-A row replay artifact has been submitted or accepted. This gate does not establish accepted rows, denominator wins, B3 reopen, B10-T1 credit, quantum advantage, or BQP separation.
- Next gate: Submit one or more row replay artifacts under the P8-A submission directory with observable-table, covariance replay, command, stdout, returncode, acceptance decision, denominator-link, and claim-boundary hashes.
- accepted_full_covariance_row_count: 0
- denominator_win_count: 0
- b3_reopen_ready: False
- b10_t1_credit_allowed: False
- quantum_advantage_claimed: False
- bqp_separation_claimed: False

## Validation

- validation_error_count: 0
