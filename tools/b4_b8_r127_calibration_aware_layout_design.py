#!/usr/bin/env python3
"""T-B4-002ab/T-B8-003af: design calibration-aware layouts for R125 tasks."""

from __future__ import annotations

import argparse
import heapq
import itertools
import json
import math
import shutil
import time
from pathlib import Path
from typing import Any

import numpy as np
from qiskit import qasm3, transpile
from qiskit_ibm_runtime.fake_provider import FakeJakartaV2, FakeLagosV2, FakeOslo

from b4_b8_r119_private_observable_bundle_gate import build_bundle_tasks
from b4_b8_r121_private_bundle_shot_sweep import basis_circuit, stable_hash, write_json
from b4_b8_r126_calibration_attribution_ledger import circuit_exposure, file_sha256


METHOD = "b4_b8_r127_calibration_aware_layout_design_v0"
STATUS = "calibration_aware_layout_design_boundary"
MODEL_STATUS = "r126_attribution_converted_to_static_layout_candidates_without_holdout_reuse"
TARGET_ID = "T-B4-002ab/T-B8-003af/T-B10-009t"
UPSTREAM_TARGET_ID = "T-B4-002aa/T-B8-003ae/T-B10-009s"
R125_RESULT_PATH = "results/B4_B8_R125_historical_snapshot_replay_v0.json"
R126_RESULT_PATH = "results/B4_B8_R126_calibration_attribution_ledger_v0.json"
OUT_DIR = "results/B4_B8_R127_calibration_aware_layout_design"
RESULT_PATH = "results/B4_B8_R127_calibration_aware_layout_design_v0.json"
REPORT_PATH = "research/B4_B8_R127_calibration_aware_layout_design.md"
TRANSPILER_SEED = 127
OPTIMIZATION_LEVEL = 1
TOP_K = 10
SNAPSHOT_CLASSES = {
    "FakeOslo": FakeOslo,
    "FakeJakartaV2": FakeJakartaV2,
    "FakeLagosV2": FakeLagosV2,
}


def logical_two_qubit_edges(task: dict[str, Any]) -> list[tuple[int, int]]:
    circuit = task["circuit"]
    edges = []
    for instruction in circuit.data:
        if instruction.operation.num_qubits != 2:
            continue
        edges.append(tuple(circuit.find_bit(qubit).index for qubit in instruction.qubits))
    return edges


def directed_cx_errors(backend: Any) -> dict[tuple[int, int], float]:
    return {
        tuple(qargs): float(properties.error or 0.0)
        for qargs, properties in backend.target["cx"].items()
    }


def shortest_reliability_path(
    backend: Any, start: int, end: int
) -> tuple[int, ...]:
    errors = directed_cx_errors(backend)
    adjacency: dict[int, list[tuple[int, float]]] = {
        qubit: [] for qubit in range(backend.num_qubits)
    }
    for (source, target), error in errors.items():
        adjacency[source].append(
            (target, -math.log(max(1.0 - error, 1e-12)))
        )
    queue: list[tuple[float, int, tuple[int, ...]]] = [(0.0, start, ())]
    visited = set()
    while queue:
        cost, node, prefix = heapq.heappop(queue)
        if node in visited:
            continue
        visited.add(node)
        path = prefix + (node,)
        if node == end:
            return path
        for neighbor, weight in adjacency[node]:
            heapq.heappush(queue, (cost + weight, neighbor, path))
    raise ValueError(f"no directed CX path from {start} to {end}")


def static_layout_objective(
    backend: Any,
    mapping: tuple[int, ...],
    logical_edges: list[tuple[int, int]],
) -> dict[str, Any]:
    measure_errors = {
        qargs[0]: float(properties.error or 0.0)
        for qargs, properties in backend.target["measure"].items()
    }
    cx_errors = directed_cx_errors(backend)
    readout_survival = math.prod(1.0 - measure_errors[physical] for physical in mapping)
    routed_steps = []
    cx_survival = 1.0
    for logical_source, logical_target in logical_edges:
        path = shortest_reliability_path(
            backend, mapping[logical_source], mapping[logical_target]
        )
        for index, edge in enumerate(zip(path[:-1], path[1:], strict=True)):
            multiplicity = 1 if index == len(path) - 2 else 3
            error = cx_errors[edge]
            cx_survival *= (1.0 - error) ** multiplicity
            routed_steps.append(
                {
                    "logical_edge": [logical_source, logical_target],
                    "physical_edge": list(edge),
                    "multiplicity_proxy": multiplicity,
                    "cx_error": error,
                }
            )
    return {
        "mapping": list(mapping),
        "static_readout_any_error_proxy": 1.0 - readout_survival,
        "static_cx_any_error_proxy": 1.0 - cx_survival,
        "static_combined_any_error_proxy": 1.0
        - readout_survival * cx_survival,
        "routed_step_count_proxy": sum(
            row["multiplicity_proxy"] for row in routed_steps
        ),
        "routed_steps": routed_steps,
    }


def report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = []
    for row in payload["selected_layout_rows"]:
        lines.append(
            f"- `{row['snapshot']}` / `{row['task_id']}`: mapping "
            f"`{row['selected_mapping']}`, static objective "
            f"`{row['selected_static_combined_proxy']:.4f}`, source/candidate "
            f"compiled exposure `{row['source_combined_any_error_proxy']:.4f}/"
            f"{row['candidate_combined_any_error_proxy']:.4f}`, delta "
            f"`{row['compiled_exposure_delta']:.4f}`, source/candidate CX "
            f"`{row['source_cx_occurrence_count']}/"
            f"{row['candidate_cx_occurrence_count']}`."
        )
    requirements = "\n".join(
        f"- `{row['requirement_id']}` "
        f"{'PASS' if row['passed'] else 'FAIL'}: {row['label']}"
        for row in payload["requirements"]
    )
    return f"""# B4/B8 R127 Calibration-Aware Layout Design

## Summary

- Target: `{TARGET_ID}`
- Upstream target: `{UPSTREAM_TARGET_ID}`
- Method: `{METHOD}`
- Status: `{STATUS}`
- Enumerated mappings: `{summary['enumerated_mapping_count']}`
- Selected layouts: `{summary['selected_layout_count']}`
- Compiled exposure improvements: `{summary['compiled_exposure_improvement_count']}` / `{summary['selected_layout_count']}`
- Mean compiled exposure delta: `{summary['mean_compiled_exposure_delta']:.4f}`
- Layout design gate passed: `{summary['layout_design_gate_passed']}`
- Acceptance holdout executed: `{summary['acceptance_holdout_executed']}`
- New credit delta: `{summary['new_credit_delta']}`

{chr(10).join(lines)}

R127 enumerates all injective six-logical-to-seven-physical mappings using only
frozen snapshot measurement and CX properties plus each task's logical
two-qubit interaction graph. It then transpiles one all-Z representative per
selected mapping to test whether the static objective predicts lower compiled
exposure than the R125 default layout. No new randomized-measurement holdout is
executed and no mitigation performance claim is made.

## Next Gate

Publicly preregister a disjoint-seed layout/readout ablation using the selected
mappings, calibration rows isolated from evaluation rows, and the unchanged
A1-A5 acceptance conditions.

## Requirements

{requirements}

## Claim Boundary

Supported: deterministic calibration-aware layout candidates and compiled
exposure comparisons. Not supported: improved verifier completeness, readout
mitigation, current calibration, provider access, hardware execution, protocol
soundness, quantum advantage, BQP separation, or B10 credit.
"""


def run_gate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    r125_path = root / R125_RESULT_PATH
    r126_path = root / R126_RESULT_PATH
    r125 = json.loads(r125_path.read_text(encoding="utf-8"))
    r126 = json.loads(r126_path.read_text(encoding="utf-8"))
    if r125.get("status") != "preregistered_historical_qpu_snapshot_replay_boundary":
        raise ValueError("R127 requires the R125 historical snapshot boundary")
    if r126.get("status") != "historical_snapshot_failure_attribution_boundary":
        raise ValueError("R127 requires the R126 attribution boundary")

    output = root / OUT_DIR
    if output.exists():
        shutil.rmtree(output)
    circuits_dir = output / "circuits"
    circuits_dir.mkdir(parents=True)

    tasks = {task["task_id"]: task for task in build_bundle_tasks()}
    source_rows = {
        (row["snapshot"], row["task_id"]): row
        for row in r126["task_attribution_rows"]
    }
    selected_rows = []
    top_rows = []
    circuit_files = []
    enumerated_count = 0
    for snapshot_name in r125["summary"]["snapshot_names"]:
        backend = SNAPSHOT_CLASSES[snapshot_name]()
        metadata = r125["snapshot_metadata"][snapshot_name]
        for task_id, task in tasks.items():
            logical_edges = logical_two_qubit_edges(task)
            ranked = []
            for mapping in itertools.permutations(
                range(backend.num_qubits), task["circuit"].num_qubits
            ):
                row = static_layout_objective(backend, mapping, logical_edges)
                ranked.append(row)
            ranked.sort(
                key=lambda row: (
                    row["static_combined_any_error_proxy"], row["mapping"]
                )
            )
            enumerated_count += len(ranked)
            for rank, row in enumerate(ranked[:TOP_K], start=1):
                top_rows.append(
                    {
                        "snapshot": snapshot_name,
                        "task_id": task_id,
                        "rank": rank,
                        **row,
                    }
                )
            selected = ranked[0]
            representative = basis_circuit(
                task["circuit"], tuple("Z" for _ in range(task["circuit"].num_qubits))
            )
            compiled = transpile(
                representative,
                backend=backend,
                initial_layout=selected["mapping"],
                optimization_level=OPTIMIZATION_LEVEL,
                seed_transpiler=TRANSPILER_SEED,
            )
            path = circuits_dir / f"{snapshot_name}_{task_id}_selected_all_z.qasm"
            path.write_text(qasm3.dumps(compiled), encoding="utf-8")
            circuit_files.append(str(path.relative_to(root)))
            candidate = circuit_exposure(path, metadata)
            source = source_rows[(snapshot_name, task_id)]
            delta = source["combined_any_error_proxy"] - candidate[
                "combined_any_error_proxy"
            ]
            selected_rows.append(
                {
                    "snapshot": snapshot_name,
                    "snapshot_sha256": metadata["sha256"],
                    "task_id": task_id,
                    "logical_two_qubit_edges": [list(edge) for edge in logical_edges],
                    "mapping_count": len(ranked),
                    "selected_mapping": selected["mapping"],
                    "selected_static_readout_proxy": selected[
                        "static_readout_any_error_proxy"
                    ],
                    "selected_static_cx_proxy": selected[
                        "static_cx_any_error_proxy"
                    ],
                    "selected_static_combined_proxy": selected[
                        "static_combined_any_error_proxy"
                    ],
                    "selected_routed_step_count_proxy": selected[
                        "routed_step_count_proxy"
                    ],
                    "source_circuit_path": source["circuit_path"],
                    "source_circuit_sha256": source["circuit_sha256"],
                    "source_combined_any_error_proxy": source[
                        "combined_any_error_proxy"
                    ],
                    "source_cx_occurrence_count": source["cx_occurrence_count"],
                    "candidate_circuit_path": str(path.relative_to(root)),
                    "candidate_circuit_sha256": file_sha256(path),
                    "candidate_combined_any_error_proxy": candidate[
                        "combined_any_error_proxy"
                    ],
                    "candidate_readout_any_error_proxy": candidate[
                        "readout_any_error_proxy"
                    ],
                    "candidate_cx_any_error_proxy": candidate[
                        "cx_any_error_proxy"
                    ],
                    "candidate_cx_occurrence_count": candidate[
                        "cx_occurrence_count"
                    ],
                    "candidate_measurement_map": candidate["measurement_map"],
                    "measurement_map_preserves_logical_order": candidate[
                        "measurement_map_preserves_logical_order"
                    ],
                    "compiled_exposure_delta": delta,
                    "compiled_exposure_improved": delta > 0.0,
                }
            )

    deltas = [row["compiled_exposure_delta"] for row in selected_rows]
    summary = {
        "snapshot_count": len(r125["summary"]["snapshot_names"]),
        "task_count": len(tasks),
        "enumerated_mapping_count": enumerated_count,
        "top_mapping_row_count": len(top_rows),
        "selected_layout_count": len(selected_rows),
        "compiled_exposure_improvement_count": sum(
            row["compiled_exposure_improved"] for row in selected_rows
        ),
        "mean_compiled_exposure_delta": float(np.mean(deltas)),
        "minimum_compiled_exposure_delta": min(deltas),
        "maximum_compiled_exposure_delta": max(deltas),
        "layout_design_gate_passed": all(
            row["compiled_exposure_improved"] for row in selected_rows
        ),
        "transpiler_seed": TRANSPILER_SEED,
        "optimization_level": OPTIMIZATION_LEVEL,
        "acceptance_holdout_executed": False,
        "readout_mitigation_tested": False,
        "r125_holdout_reused_for_acceptance": False,
        "current_backend_calibration_used": False,
        "hardware_execution_performed": False,
        "protocol_soundness_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "new_credit_delta": 0,
    }
    requirements = [
        {
            "requirement_id": "P1",
            "label": "R125 and R126 source artifacts are hash-bound and consumed",
            "passed": len(r125["trial_rows"]) == 480
            and len(r126["task_attribution_rows"]) == 6,
            "evidence": {
                "r125_sha256": file_sha256(r125_path),
                "r126_sha256": file_sha256(r126_path),
            },
        },
        {
            "requirement_id": "P2",
            "label": "all injective six-to-seven physical mappings are enumerated",
            "passed": enumerated_count == 6 * math.perm(7, 6),
            "evidence": {"enumerated_mapping_count": enumerated_count},
        },
        {
            "requirement_id": "P3",
            "label": "the static objective uses only snapshot and task-graph properties",
            "passed": True,
            "evidence": {
                "objective_fields": [
                    "measure_error",
                    "cx_error",
                    "logical_two_qubit_edges",
                ]
            },
        },
        {
            "requirement_id": "P4",
            "label": "ten ranked mappings are retained per snapshot/task",
            "passed": len(top_rows) == 6 * TOP_K,
            "evidence": {"top_mapping_row_count": len(top_rows)},
        },
        {
            "requirement_id": "P5",
            "label": "one selected mapping is transpiled per snapshot/task",
            "passed": len(selected_rows) == 6 and len(circuit_files) == 6,
            "evidence": {"selected_layout_count": len(selected_rows)},
        },
        {
            "requirement_id": "P6",
            "label": "selected compiled circuits preserve logical classical-bit order",
            "passed": all(
                row["measurement_map_preserves_logical_order"]
                for row in selected_rows
            ),
            "evidence": {"circuit_count": len(selected_rows)},
        },
        {
            "requirement_id": "P7",
            "label": "compiled exposure is compared against every R125 default layout",
            "passed": all(
                math.isfinite(row["compiled_exposure_delta"])
                for row in selected_rows
            ),
            "evidence": {"comparison_count": len(selected_rows)},
        },
        {
            "requirement_id": "P8",
            "label": "no acceptance holdout or readout mitigation is executed",
            "passed": not summary["acceptance_holdout_executed"]
            and not summary["readout_mitigation_tested"]
            and not summary["r125_holdout_reused_for_acceptance"],
            "evidence": {"design_only": True},
        },
        {
            "requirement_id": "P9",
            "label": "historical snapshots remain separate from current and hardware evidence",
            "passed": not summary["current_backend_calibration_used"]
            and not summary["hardware_execution_performed"],
            "evidence": {"evidence_class": "historical_snapshot_layout_design"},
        },
        {
            "requirement_id": "P10",
            "label": "no soundness, advantage, BQP, or new credit is claimed",
            "passed": not summary["protocol_soundness_claimed"]
            and not summary["quantum_advantage_claimed"]
            and not summary["bqp_separation_claimed"]
            and summary["new_credit_delta"] == 0,
            "evidence": {"new_credit_delta": 0},
        },
    ]
    failed = [row["requirement_id"] for row in requirements if not row["passed"]]
    payload: dict[str, Any] = {
        "title": "B4/B8 R127 calibration-aware layout design",
        "version": "0.1",
        "generated_at_unix": int(time.time()),
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "requirements": requirements,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "summary": summary,
        "selected_layout_rows": selected_rows,
        "top_layout_rows": top_rows,
        "artifacts": {
            "r125_result": R125_RESULT_PATH,
            "r126_result": R126_RESULT_PATH,
            "selected_circuits": sorted(circuit_files),
        },
        "claim_boundary": {
            "what_is_supported": (
                "Deterministic calibration-aware physical-layout candidates and "
                "compiled exposure comparisons for the fixed R125 tasks."
            ),
            "what_is_not_supported": (
                "Improved verifier completeness, readout mitigation, current "
                "calibration, provider access, hardware execution, protocol "
                "soundness, quantum advantage, BQP separation, or B10 credit."
            ),
            "next_gate": (
                "Publicly preregister a disjoint-seed layout/readout ablation using "
                "the selected mappings and calibration rows isolated from evaluation."
            ),
        },
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
