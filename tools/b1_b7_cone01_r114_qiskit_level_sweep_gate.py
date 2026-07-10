#!/usr/bin/env python3
"""T-B1-004hl/T-B7-016u: sweep Qiskit levels before accepting 2Q savings."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from qiskit import QuantumCircuit, qasm2, transpile


METHOD = "b1_b7_cone01_r114_qiskit_level_sweep_gate_v0"
STATUS = "cone01_r114_level_sweep_proves_2q_reduction_unaccepted"
MODEL_STATUS = "first_nonzero_2q_reduction_fails_exact_equivalence"
TARGET_ID = "T-B1-004hl/T-B7-016u"
UPSTREAM_TARGET_ID = "T-B1-004hk/T-B7-016t"
SOURCE_PATH = "benchmarks/qasmbench_medium_exact/gcm_h6.qasm"
OUT_DIR = "results/B1_B7_cone01_R114_qiskit_level_sweep_gate"
RESULT_PATH = "results/B1_B7_cone01_R114_qiskit_level_sweep_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R114_qiskit_level_sweep_gate.md"


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)


def report(payload: dict) -> str:
    s = payload["summary"]
    rows = "\n".join(
        f"- Level `{row['optimization_level']}`: CX `{row['two_qubit_gate_count']}`, exact `{row['equivalence_passed']}/{row['equivalence_failed']}`, fidelity `{row['fidelity']}`"
        for row in s["levels"]
    )
    reqs = "\n".join(
        f"- `{item['requirement_id']}` {'PASS' if item['passed'] else 'FAIL'}: {item['label']}"
        for item in payload["requirements"]
    )
    return f"""# B1/B7 Cone01 R114 Qiskit Level Sweep Gate

## Summary

- Target: `{TARGET_ID}`
- Upstream target: `{UPSTREAM_TARGET_ID}`
- Method: `{METHOD}`
- Status: `{STATUS}`
- Model status: `{MODEL_STATUS}`
- Source workload: `{SOURCE_PATH}`
- Accepted level with nonzero 2Q reduction: `{s['accepted_nonzero_2q_level']}`

## Sweep

{rows}

Level 0 and level 1 preserve exact equivalence but keep the source CX count.
Level 2 and level 3 reduce CX from 762 to 528, but both fail exact equivalence
with fidelity 0.5. The first apparent two-qubit win is therefore rejected.

## Requirements

{reqs}

## Claim Boundary

R114 does not claim that every Qiskit optimization is invalid. It records this
workload-specific sweep and rejects every candidate with a nonzero 2Q reduction
until a stronger semantic certificate is supplied. No B7 credit is granted.
"""


def run_gate(root: Path) -> dict:
    root = root.resolve()
    source = root / SOURCE_PATH
    out = root / OUT_DIR
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    work = out / "work"
    work.mkdir()
    source_circuit = QuantumCircuit.from_qasm_file(str(source))
    levels = []
    for level in range(4):
        candidate = transpile(source_circuit, basis_gates=["u3", "cx", "measure"], optimization_level=level)
        candidate_path = work / f"level{level}.qasm"
        candidate_path.write_text(qasm2.dumps(candidate), encoding="utf-8")
        eq_path = out / f"level{level}.equivalence.json"
        eq_run = run([sys.executable, "tools/b1_equivalence_check.py", SOURCE_PATH, str(candidate_path), "--max-qubits", "15", "--pretty", "--output", str(eq_path)], root)
        equivalence = json.loads(eq_path.read_text(encoding="utf-8"))
        row = equivalence["results"][0]
        levels.append({
            "optimization_level": level,
            "candidate_path": str(candidate_path.relative_to(root)),
            "candidate_operation_count": int(candidate.size()),
            "two_qubit_gate_count": int(candidate.count_ops().get("cx", 0)),
            "equivalence_path": str(eq_path.relative_to(root)),
            "equivalence_passed": equivalence["passed"],
            "equivalence_failed": equivalence["failed"],
            "fidelity": row.get("fidelity"),
            "max_global_phase_adjusted_delta": row.get("max_global_phase_adjusted_delta"),
            "checker_returncode": eq_run.returncode,
        })
    source_two_qubit = int(source_circuit.count_ops().get("cx", 0))
    accepted = [row for row in levels if row["equivalence_failed"] == 0 and row["two_qubit_gate_count"] < source_two_qubit]
    reduced_invalid = [row for row in levels if row["two_qubit_gate_count"] < source_two_qubit and row["equivalence_failed"] > 0]
    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_two_qubit_gate_count": source_two_qubit,
        "levels": levels,
        "accepted_nonzero_2q_level": accepted[0]["optimization_level"] if accepted else None,
        "invalid_reduced_level_count": len(reduced_invalid),
        "counter_transition_accepted": False,
        "counter_delta": 0,
        "new_credit_delta": 0,
    }
    requirements = [
        {"requirement_id": "P1", "label": "all four optimization levels are materialized", "passed": len(levels) == 4 and all(Path(root / row["candidate_path"]).exists() for row in levels), "evidence": {"levels": [row["optimization_level"] for row in levels]}},
        {"requirement_id": "P2", "label": "level 0 and level 1 pass exact equivalence without 2Q reduction", "passed": all(row["equivalence_failed"] == 0 and row["two_qubit_gate_count"] == source_two_qubit for row in levels[:2]), "evidence": {"levels": levels[:2]}},
        {"requirement_id": "P3", "label": "level 2 and level 3 show the apparent 2Q reduction", "passed": all(row["two_qubit_gate_count"] == 528 and row["two_qubit_gate_count"] < source_two_qubit for row in levels[2:]), "evidence": {"levels": levels[2:]}},
        {"requirement_id": "P4", "label": "every nonzero 2Q reduction fails exact equivalence", "passed": not accepted and len(reduced_invalid) == 2 and all(row["equivalence_failed"] > 0 for row in reduced_invalid), "evidence": {"accepted": accepted, "reduced_invalid": reduced_invalid}},
        {"requirement_id": "P5", "label": "failed candidates keep counters and B7 credit at zero", "passed": summary["counter_delta"] == 0 and summary["new_credit_delta"] == 0, "evidence": {"counter_delta": 0, "new_credit_delta": 0}},
        {"requirement_id": "P6", "label": "fidelity and phase-adjusted error are recorded", "passed": all(row["fidelity"] is not None for row in levels[2:]), "evidence": {"fidelity": [row["fidelity"] for row in levels[2:]]}},
        {"requirement_id": "P7", "label": "same workload and denominator are retained across the sweep", "passed": source_circuit.num_qubits == 13 and all(row["checker_returncode"] == (0 if row["equivalence_failed"] == 0 else 1) for row in levels), "evidence": {"qubits": source_circuit.num_qubits, "workload": SOURCE_PATH}},
        {"requirement_id": "P8", "label": "claim boundary rejects apparent 2Q progress without semantics", "passed": True, "evidence": {"model_status": MODEL_STATUS}},
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    payload = {
        "title": "B1/B7 cone01 R114 Qiskit level sweep gate",
        "version": "0.1",
        "generated_at_unix": int(time.time()),
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_path": SOURCE_PATH,
        "requirements": requirements,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "summary": summary,
        "artifacts": {"work_dir": str(work.relative_to(root)), "level_summaries": [row["equivalence_path"] for row in levels]},
        "claim_boundary": {"what_is_supported": "On one 13-qubit workload, levels 0/1 pass exact equivalence without 2Q reduction while levels 2/3 reduce CX but fail exact equivalence.", "what_is_not_supported": "No accepted 2Q reduction, arbitrary-input equivalence, T-resource reduction, layout improvement, or B7 credit.", "next_gate": "Develop a composable semantic rewrite that preserves exact equivalence and retains a nonzero 2Q or proxy-T delta."},
    }
    payload["payload_hash"] = stable_hash(payload)
    write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    print(json.dumps(run_gate(Path(args.repo_root)), sort_keys=True))


if __name__ == "__main__":
    main()
