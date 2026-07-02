# B9 Checked-Run Acquisition Gate

Status: **checked_run_acquisition_open_toolchain_not_cached**

## Summary

- Method: `b9_checked_run_acquisition_gate_v0`
- Acquisition requirements passed/failed: 4 / 3
- Failed acquisition requirement IDs: ['A3', 'A4', 'A6']
- Lean 4 available: False
- Lake available: False
- Release host reachable: True
- Local toolchain cache present: False
- Checked transcript present: False

## Requirement Results

- A1 [PASS]: Offline proof bundle remains valid and hashable
- A2 [PASS]: Pinned Lean toolchain declaration is present
- A3 [FAIL]: Real Lean 4 executable is available without triggering an acquisition timeout
- A4 [FAIL]: Lake executable is available without triggering an acquisition timeout
- A5 [PASS]: Pinned Lean toolchain can be acquired or is already cached
- A6 [FAIL]: Checked Lean module transcript is present
- A7 [PASS]: Forbidden B9 theorem and Quantum PCP claims remain false

## Toolchain Probe

- Lean probes: `[{"available": true, "command": ["~/.elan/bin/lean", "--version"], "executable": "~/.elan/bin/lean", "returncode": null, "runtime_seconds": 10.004033088684082, "stderr": "", "stdout": "", "timed_out": true}, {"available": true, "command": ["~/Library/Python/3.9/bin/lean", "--version"], "executable": "~/Library/Python/3.9/bin/lean", "returncode": 0, "runtime_seconds": 0.4173462390899658, "stderr": "~/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020\n  warnings.warn(", "stdout": "lean 1.0.225", "timed_out": false}]`
- Lake probes: `[{"available": true, "command": ["~/.elan/bin/lake", "--version"], "executable": "~/.elan/bin/lake", "returncode": null, "runtime_seconds": 10.003285884857178, "stderr": "", "stdout": "", "timed_out": true}, {"available": false, "command": ["lake", "--version"], "executable": null, "returncode": null, "runtime_seconds": 0.0, "stderr": "", "stdout": "", "timed_out": false}]`
- Elan probes: `[{"available": true, "command": ["~/.elan/bin/elan", "--version"], "executable": "~/.elan/bin/elan", "returncode": 0, "runtime_seconds": 0.011323213577270508, "stderr": "", "stdout": "elan 4.2.3 (b6cec7e10 2026-06-08)", "timed_out": false}, {"available": false, "command": ["elan", "--version"], "executable": null, "returncode": null, "runtime_seconds": 0.0, "stderr": "", "stdout": "", "timed_out": false}]`
- Release host probe: `{"error": null, "host": "release.lean-lang.org", "port": 443, "reachable": true, "runtime_seconds": 8.170585870742798}`

## Claim Boundary

- Supported: The B9 proof-run acquisition blocker is now explicit: the offline bundle is valid, the pinned Lean 4.12.0 declaration exists, but this environment does not yet provide a usable Lean 4/Lake checked run transcript.
- Not supported: No proof-assistant checked theorem, Quantum PCP proof, NLTS theorem, or global gap-amplification impossibility theorem is established.
- Next gate: Provide an accepted transcript for lean --version, lake --version, and lake env lean B9/ClusterStabilizer/WidthLocality.lean, using either a reachable Lean release host, a trusted mirror/cache, or the reviewed GitHub workflow.
- proof_assistant_checked: False
- formal_theorem_proved: False
- explicit_not_quantum_pcp_proof: True

## Validation

- validation_error_count: 0
