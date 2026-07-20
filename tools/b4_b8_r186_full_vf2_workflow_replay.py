#!/usr/bin/env python3
"""Execute the preregistered R186 full VF2 workflow translation matrix."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
import uuid
from itertools import permutations
from pathlib import Path
from typing import Any

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r154_deterministic_automatic_replay import canonical_hash, target_descriptor
from b4_b8_r181_active_limb_replay import actual_environment, mapping_vector
from b4_b8_r182_score_cost_attribution_replay import (
    cell_definitions,
    prepare_small_gap,
    prepare_standard,
)


METHOD = "b4_b8_r186_full_vf2_workflow_replay_v0"
PROTOCOL_PATH = "results/B4_B8_R186_full_vf2_workflow_protocol_v0.json"
DESIGN_CONTRACT_PATH = "benchmarks/B4_B8_R186_full_vf2_workflow_contract_v0.json"
EXECUTION_CONTRACT_PATH = (
    "benchmarks/B4_B8_R186_full_vf2_workflow_execution_contract_v0.json"
)
R181_PROTOCOL_PATH = "results/B4_B8_R181_active_limb_protocol_v0.json"
PLATFORMS = {
    "linux_x86_64": {
        "system": "Linux",
        "machine": "x86_64",
        "binary_path": "research/source_lineage/Qiskit_2_4_1_R184_window_exact_pyext.x86_64-linux-gnu.so",
        "out_dir": "results/B4_B8_R186_full_vf2_workflow_linux_x86_64_replay",
        "result_path": "results/B4_B8_R186_full_vf2_workflow_linux_x86_64_v0.json",
        "report_path": "research/B4_B8_R186_full_vf2_workflow_linux_x86_64.md",
    },
    "macos_arm64": {
        "system": "Darwin",
        "machine": "arm64",
        "binary_path": "research/source_lineage/Qiskit_2_4_1_R185_window_exact_pyext.arm64-darwin.so",
        "out_dir": "results/B4_B8_R186_full_vf2_workflow_macos_arm64_replay",
        "result_path": "results/B4_B8_R186_full_vf2_workflow_macos_arm64_v0.json",
        "report_path": "research/B4_B8_R186_full_vf2_workflow_macos_arm64.md",
    },
}
ARMS = {
    "baseline": {
        "policy": "rust_biguint_exact_retained_binary64",
        "entrypoint": "vf2_layout_pass_average_exact_score",
    },
    "reference": {
        "policy": "rust_prefix_initialized_34_limb_exact",
        "entrypoint": "vf2_layout_pass_average_prefix_initialized_exact_score",
    },
    "candidate": {
        "policy": "rust_windowed_4_limb_exact_with_biguint_fallback",
        "entrypoint": "vf2_layout_pass_average_window_exact_score",
    },
}
SURFACES = ("accelerator_entrypoint", "python_passmanager")
ARM_ORDERS = [list(order) for order in permutations(ARMS)]
SURFACE_ORDERS = [list(SURFACES), list(reversed(SURFACES))]
SCHEDULES = [
    [
        {"surface": surface, "arm": arm}
        for surface in surface_order
        for arm in arm_order
    ]
    for arm_order in ARM_ORDERS
    for surface_order in SURFACE_ORDERS
]
PROCESS_ENVIRONMENT = {
    "MKL_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
    "QISKIT_PARALLEL": "FALSE",
    "RAYON_NUM_THREADS": "1",
}


def validate_hash_field(payload: dict[str, Any], field: str, label: str) -> str:
    body = dict(payload)
    observed = body.pop(field, None)
    if not observed or observed != canonical_hash(body):
        raise ValueError(f"R186 {label} hash mismatch")
    return str(observed)


def load_inputs(root: Path) -> tuple[dict[str, Any], ...]:
    payloads = tuple(
        json.loads((root / relative).read_text(encoding="utf-8"))
        for relative in (
            PROTOCOL_PATH,
            DESIGN_CONTRACT_PATH,
            EXECUTION_CONTRACT_PATH,
            R181_PROTOCOL_PATH,
        )
    )
    validate_hash_field(payloads[0], "payload_hash", "protocol")
    validate_hash_field(payloads[1], "payload_hash", "design contract")
    validate_hash_field(payloads[2], "payload_hash", "execution contract")
    validate_hash_field(payloads[3], "payload_hash", "R181 protocol")
    return payloads


def validate_contracts(
    root: Path,
    protocol: dict[str, Any],
    design: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    if protocol.get("method") != "b4_b8_r186_full_vf2_workflow_protocol_v0":
        raise ValueError("R186 protocol identity mismatch")
    if design.get("protocol_payload_hash") != protocol["payload_hash"]:
        raise ValueError("R186 design protocol binding mismatch")
    if execution.get("protocol_payload_hash") != protocol["payload_hash"]:
        raise ValueError("R186 execution protocol binding mismatch")
    if execution.get("design_contract_payload_hash") != design["payload_hash"]:
        raise ValueError("R186 execution design binding mismatch")
    if execution.get("execution_started") is not False:
        raise ValueError("R186 execution contract is not unopened")
    for section in ("source_bindings", "tool_bindings"):
        for binding in execution[section].values():
            path = root / binding["path"]
            if not path.is_file() or file_sha256(path) != binding["sha256"]:
                raise ValueError(f"R186 binding mismatch: {binding['path']}")


def runtime_preregistration(
    root: Path, args: argparse.Namespace, execution: dict[str, Any]
) -> dict[str, str]:
    public = execution["public_preregistration"]
    observed = {
        "commit": args.preregistration_commit,
        "discussion": args.preregistration_discussion,
        "created_at": args.preregistration_created_at,
    }
    current = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if current != observed["commit"]:
        raise ValueError("R186 runtime commit does not match HEAD")
    if observed["discussion"] != public["discussion"]:
        raise ValueError("R186 public Discussion mismatch")
    if observed["created_at"] != public["created_at"]:
        raise ValueError("R186 public Discussion timestamp mismatch")
    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            public["public_design_commit"],
            current,
        ],
        cwd=root,
        check=False,
    )
    if ancestor.returncode:
        raise ValueError("R186 runtime commit predates the public design")
    return observed


def verify_clean_public_commit(root: Path, expected_commit: str) -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=root, text=True
    )
    if status.strip():
        raise ValueError("R186 execution must start from a clean worktree")
    output = subprocess.check_output(
        ["git", "ls-remote", "origin", "refs/heads/main"], cwd=root, text=True
    ).strip()
    remote = output.split()[0] if output else ""
    if remote != expected_commit:
        raise ValueError("R186 execution commit is not public main")


def verify_platform(platform_id: str) -> dict[str, str]:
    definition = PLATFORMS[platform_id]
    observed = {"system": platform.system(), "machine": platform.machine()}
    if observed != {
        "system": definition["system"],
        "machine": definition["machine"],
    }:
        raise ValueError(f"R186 platform mismatch: {observed}")
    return observed


def prepare_overlay(root: Path, platform_id: str, protocol: dict[str, Any]) -> Path:
    spec = importlib.util.find_spec("qiskit")
    if spec is None or not spec.submodule_search_locations:
        raise ValueError("R186 cannot locate installed Qiskit")
    source = Path(next(iter(spec.submodule_search_locations))).resolve()
    binary = root / PLATFORMS[platform_id]["binary_path"]
    binary_hash = file_sha256(binary)
    overlay = Path("/tmp") / f"prometheus-r186-{platform_id}-{binary_hash[:16]}"
    if overlay.exists():
        shutil.rmtree(overlay)
    package = overlay / "qiskit"
    shutil.copytree(source, package)
    for candidate in package.glob("_accelerate*.so"):
        candidate.unlink()
    installed = package / "_accelerate.abi3.so"
    shutil.copy2(binary, installed)
    if file_sha256(installed) != binary_hash:
        raise ValueError("R186 overlay accelerator copy mismatch")
    python_boundary = package / "transpiler/passes/layout/vf2_layout.py"
    expected = protocol["qiskit_boundary"]["python_vf2_layout_sha256"]
    if file_sha256(python_boundary) != expected:
        raise ValueError("R186 Python VF2Layout source hash mismatch")
    return overlay


def imported_binary() -> Path:
    import qiskit

    candidates = sorted(Path(qiskit.__file__).resolve().parent.glob("_accelerate*.so"))
    if len(candidates) != 1:
        raise ValueError(f"R186 expected one accelerator, found {len(candidates)}")
    return candidates[0]


def new_pass_config() -> Any:
    from qiskit._accelerate.vf2_layout import VF2PassConfiguration

    return VF2PassConfiguration.from_legacy_api(
        call_limit=30000000,
        time_limit=None,
        max_trials=250000,
        shuffle_seed=-1,
        score_initial_layout=False,
    )


def direct_mapping(
    function: Any, dag: Any, target: Any, error_map: Any
) -> list[int] | None:
    output = function(
        dag,
        target,
        new_pass_config(),
        strict_direction=False,
        avg_error_map=error_map,
    )
    return mapping_vector(output.new_mapping(), target.num_qubits)


def passmanager_mapping(
    function: Any,
    dag: Any,
    circuit: Any,
    target: Any,
    error_map: Any,
) -> list[int] | None:
    from qiskit.transpiler import PassManager
    from qiskit.transpiler.basepasses import AnalysisPass
    from qiskit.transpiler.passes import VF2Layout

    vf2_python = importlib.import_module(
        "qiskit.transpiler.passes.layout.vf2_layout"
    )

    class InjectExternalErrorMap(AnalysisPass):
        def run(self, _dag: Any) -> None:
            self.property_set["vf2_avg_error_map"] = error_map

    original = vf2_python.vf2_layout_pass_average
    try:
        vf2_python.vf2_layout_pass_average = function
        vf2_pass = VF2Layout(
            target=target,
            strict_direction=False,
            seed=-1,
            call_limit=30000000,
            time_limit=None,
            max_trials=250000,
        )
        PassManager([InjectExternalErrorMap(), vf2_pass]).run(circuit)
        layout = vf2_pass.property_set.get("layout")
        if layout is None:
            return None
        return [int(layout[qubit]) for qubit in dag.qubits]
    finally:
        vf2_python.vf2_layout_pass_average = original


def run_surface(
    surface: str,
    function: Any,
    dag: Any,
    circuit: Any,
    target: Any,
    error_map: Any,
) -> list[int] | None:
    if surface == "accelerator_entrypoint":
        return direct_mapping(function, dag, target, error_map)
    if surface == "python_passmanager":
        return passmanager_mapping(function, dag, circuit, target, error_map)
    raise ValueError(f"R186 unknown timing surface: {surface}")


def worker_path(platform_id: str, cell_id: str) -> str:
    return f"{PLATFORMS[platform_id]['out_dir']}/{cell_id}.json"


def execute_worker(
    root: Path,
    platform_id: str,
    protocol: dict[str, Any],
    design: dict[str, Any],
    execution: dict[str, Any],
    r181: dict[str, Any],
    cell_id: str,
    preregistration: dict[str, str],
) -> dict[str, Any]:
    from qiskit._accelerate import vf2_layout as accelerator
    from qiskit.converters import dag_to_circuit

    cells = {row["cell_id"]: row for row in cell_definitions(r181)}
    if cell_id not in cells:
        raise ValueError("R186 worker identity is outside the frozen matrix")
    output_path = root / worker_path(platform_id, cell_id)
    if output_path.exists():
        raise ValueError(f"R186 worker already exists: {output_path}")
    expected_binary = root / PLATFORMS[platform_id]["binary_path"]
    binary = imported_binary()
    if file_sha256(binary) != file_sha256(expected_binary):
        raise ValueError("R186 worker imported the wrong accelerator")
    cell = cells[cell_id]
    prepared = (
        prepare_standard(root, r181, cell)
        if cell["kind"] == "standard"
        else prepare_small_gap(root, r181, cell)
    )
    circuit = dag_to_circuit(prepared["dag"])
    functions = {
        arm: getattr(accelerator, definition["entrypoint"])
        for arm, definition in ARMS.items()
    }
    units = prepared["work_units"]
    workload = protocol["frozen_workload"]
    warmup_matches = {
        surface: {arm: 0 for arm in ARMS} for surface in SURFACES
    }
    started_at = int(time.time())

    for warmup_index, schedule in enumerate(SCHEDULES):
        unit = units[warmup_index % len(units)]
        for step in schedule:
            vector = run_surface(
                step["surface"],
                functions[step["arm"]],
                prepared["dag"],
                circuit,
                prepared["target"],
                unit["error_map"],
            )
            warmup_matches[step["surface"]][step["arm"]] += int(
                vector == unit["expected"]
            )

    rows = []
    for row_index in range(workload["measured_rows_per_cell"]):
        unit = units[row_index % len(units)]
        schedule_index = row_index % len(SCHEDULES)
        schedule = SCHEDULES[schedule_index]
        measurements = {
            surface: {arm: {} for arm in ARMS} for surface in SURFACES
        }
        for execution_position, step in enumerate(schedule):
            started = time.perf_counter_ns()
            vector = run_surface(
                step["surface"],
                functions[step["arm"]],
                prepared["dag"],
                circuit,
                prepared["target"],
                unit["error_map"],
            )
            elapsed = time.perf_counter_ns() - started
            measurements[step["surface"]][step["arm"]] = {
                "policy": ARMS[step["arm"]]["policy"],
                "mapping_vector": vector,
                "matches_expected": vector == unit["expected"],
                "elapsed_nanoseconds": elapsed,
                "execution_position": execution_position,
            }
        ratios = {}
        for surface in SURFACES:
            candidate = measurements[surface]["candidate"]["elapsed_nanoseconds"]
            baseline = measurements[surface]["baseline"]["elapsed_nanoseconds"]
            reference = measurements[surface]["reference"]["elapsed_nanoseconds"]
            ratios[surface] = {
                "candidate_to_baseline": candidate / baseline,
                "candidate_to_reference": candidate / reference,
            }
        row: dict[str, Any] = {
            "platform_id": platform_id,
            "cell_id": cell_id,
            "subcell_id": unit["subcell_id"],
            "kind": cell["kind"],
            "case_id": unit["case_id"],
            "row_index": row_index,
            "schedule_index": schedule_index,
            "execution_schedule": schedule,
            "expected_mapping_vector": unit["expected"],
            "measurements": measurements,
            "paired_ratios": ratios,
            "all_six_mappings_match_expected": all(
                measurements[surface][arm]["matches_expected"]
                for surface in SURFACES
                for arm in ARMS
            ),
            "cross_surface_arm_mapping_match": all(
                measurements[SURFACES[0]][arm]["mapping_vector"]
                == measurements[SURFACES[1]][arm]["mapping_vector"]
                for arm in ARMS
            ),
            "timing_call_count": 6,
            "simulation_execution_count": 0,
            "total_simulated_shots": 0,
            "real_backend_row_count": 0,
        }
        if "error_map_descriptor_hash" in unit:
            row["error_map_descriptor_hash"] = unit["error_map_descriptor_hash"]
            row["exact_minimum_gap_ulp_ratio"] = unit[
                "exact_minimum_gap_ulp_ratio"
            ]
        row["row_hash"] = canonical_hash(row)
        rows.append(row)

    schedule_counts = {
        str(index): sum(row["schedule_index"] == index for row in rows)
        for index in range(len(SCHEDULES))
    }
    manifest = {
        "title": "R186 isolated full VF2 workflow cell",
        "version": 0,
        "method": METHOD,
        "status": "isolated_full_workflow_worker_complete",
        "platform_id": platform_id,
        "cell": cell,
        "process_id": os.getpid(),
        "process_instance_uuid": str(uuid.uuid4()),
        "started_at_unix": started_at,
        "preregistration": preregistration,
        "protocol_payload_hash": protocol["payload_hash"],
        "design_contract_payload_hash": design["payload_hash"],
        "execution_contract_payload_hash": execution["payload_hash"],
        "environment": actual_environment(),
        "accelerator_path": str(binary),
        "accelerator_sha256": file_sha256(binary),
        "python_vf2_layout_sha256": file_sha256(
            Path(importlib.import_module(
                "qiskit.transpiler.passes.layout.vf2_layout"
            ).__file__).resolve()
        ),
        "input_path": prepared["input_path"],
        "input_sha256": file_sha256(root / prepared["input_path"]),
        "source_worker_path": prepared["source_worker_path"],
        "target_descriptor_sha256": target_descriptor(prepared["backend"])[
            "descriptor_hash"
        ],
        "schedule_rule": "all_six_arm_orders_crossed_with_both_surface_orders_repeated_three_times",
        "schedule_counts": schedule_counts,
        "warmup_call_count": len(SCHEDULES) * len(ARMS) * len(SURFACES),
        "warmup_matches_expected": warmup_matches,
        "recorded_row_count": len(rows),
        "timing_call_count": sum(row["timing_call_count"] for row in rows),
        "replay_rows": rows,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "real_backend_row_count": 0,
    }
    manifest["manifest_hash"] = canonical_hash(manifest)
    write_json(output_path, manifest)
    return manifest


def launch_worker(
    root: Path,
    overlay: Path,
    platform_id: str,
    cell_id: str,
    preregistration: dict[str, str],
) -> None:
    environment = dict(os.environ)
    environment.update(PROCESS_ENVIRONMENT)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(overlay), str(root / "tools"), environment.get("PYTHONPATH", "")]
    )
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--root",
        str(root),
        "--platform",
        platform_id,
        "--worker-cell",
        cell_id,
        "--preregistration-commit",
        preregistration["commit"],
        "--preregistration-discussion",
        preregistration["discussion"],
        "--preregistration-created-at",
        preregistration["created_at"],
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"R186 worker failed: {platform_id}/{cell_id}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )


def validate_worker(manifest: dict[str, Any], path: Path) -> None:
    validate_hash_field(manifest, "manifest_hash", f"worker {path.name}")
    for row in manifest["replay_rows"]:
        validate_hash_field(row, "row_hash", f"row {path.name}")


def paired_median(rows: list[dict[str, Any]], surface: str, key: str) -> float:
    return statistics.median(row["paired_ratios"][surface][key] for row in rows)


def classify_platform(
    root: Path,
    platform_id: str,
    protocol: dict[str, Any],
    design: dict[str, Any],
    execution: dict[str, Any],
    manifests: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = [row for manifest in manifests for row in manifest["replay_rows"]]
    direct_ratio = paired_median(
        rows, "accelerator_entrypoint", "candidate_to_baseline"
    )
    workflow_ratio = paired_median(
        rows, "python_passmanager", "candidate_to_baseline"
    )
    retention = (
        (1.0 - workflow_ratio) / (1.0 - direct_ratio)
        if direct_ratio < 1.0
        else None
    )
    cell_summaries = []
    for manifest in sorted(manifests, key=lambda item: item["cell"]["cell_id"]):
        selected = manifest["replay_rows"]
        cell_summaries.append(
            {
                "cell": manifest["cell"],
                "row_count": len(selected),
                "schedule_counts": manifest["schedule_counts"],
                "all_six_mappings_match_expected": all(
                    row["all_six_mappings_match_expected"] for row in selected
                ),
                "surface_ratios": {
                    surface: {
                        "candidate_to_baseline_paired_median": paired_median(
                            selected, surface, "candidate_to_baseline"
                        ),
                        "candidate_to_reference_paired_median": paired_median(
                            selected, surface, "candidate_to_reference"
                        ),
                        "arm_median_elapsed_nanoseconds": {
                            arm: statistics.median(
                                row["measurements"][surface][arm][
                                    "elapsed_nanoseconds"
                                ]
                                for row in selected
                            )
                            for arm in ARMS
                        },
                    }
                    for surface in SURFACES
                },
            }
        )
    hypothesis_support = {
        "H1-full-boundary-integrity": all(
            row["all_six_mappings_match_expected"]
            and row["cross_surface_arm_mapping_match"]
            for row in rows
        ),
        "H2-direct-window-competitiveness": direct_ratio <= 1.0,
        "H3-passmanager-window-competitiveness": workflow_ratio <= 1.0,
        "H4-relative-saving-retention": retention is not None and retention >= 0.1,
    }
    workload = protocol["frozen_workload"]
    requirements = {
        "P1_contracts_and_bindings_validate": True,
        "P2_public_preregistration_predates_execution": True,
        "P3_platform_and_binary_match": all(
            manifest["platform_id"] == platform_id for manifest in manifests
        ),
        "P4_python_vf2_source_hash_matches": all(
            manifest["python_vf2_layout_sha256"]
            == protocol["qiskit_boundary"]["python_vf2_layout_sha256"]
            for manifest in manifests
        ),
        "P5_all_six_mappings_match": hypothesis_support[
            "H1-full-boundary-integrity"
        ],
        "P6_matrix_and_schedule_counts_match": (
            len(manifests) == workload["workload_cell_count"]
            and len(rows) == workload["measured_row_count"]
            and all(
                manifest["recorded_row_count"]
                == workload["measured_rows_per_cell"]
                and set(manifest["schedule_counts"].values())
                == {workload["repetitions_per_schedule_per_cell"]}
                for manifest in manifests
            )
        ),
        "P7_call_counts_match": (
            sum(manifest["timing_call_count"] for manifest in manifests)
            == workload["measured_timing_call_count_per_platform"]
            and sum(manifest["warmup_call_count"] for manifest in manifests)
            == workload["warmup_call_count_per_platform"]
        ),
        "P8_platform_hypotheses_follow_frozen_rules": all(
            hypothesis_support.values()
        ),
        "P9_zero_simulation_and_hardware_rows": all(
            row["simulation_execution_count"] == 0
            and row["total_simulated_shots"] == 0
            and row["real_backend_row_count"] == 0
            for row in rows
        ),
        "P10_claim_boundary_preserved": True,
    }
    passed = sum(requirements.values())
    result = {
        "title": f"B4/B8/B10 R186 full VF2 workflow {platform_id} result",
        "version": 0,
        "method": METHOD,
        "status": "platform_complete_cross_platform_oracle_pending",
        "source_target_id": "T-B4-002eh/T-B8-003el/T-B10-009dx-r186-result",
        "platform_id": platform_id,
        "protocol_payload_hash": protocol["payload_hash"],
        "design_contract_payload_hash": design["payload_hash"],
        "execution_contract_payload_hash": execution["payload_hash"],
        "preregistration": manifests[0]["preregistration"],
        "worker_count": len(manifests),
        "measured_row_count": len(rows),
        "measured_timing_call_count": sum(
            manifest["timing_call_count"] for manifest in manifests
        ),
        "warmup_call_count": sum(
            manifest["warmup_call_count"] for manifest in manifests
        ),
        "mapping_check_count": len(rows) * len(ARMS) * len(SURFACES),
        "mapping_match_count": sum(
            row["measurements"][surface][arm]["matches_expected"]
            for row in rows
            for surface in SURFACES
            for arm in ARMS
        ),
        "aggregate_surface_ratios": {
            surface: {
                "candidate_to_baseline_paired_median": paired_median(
                    rows, surface, "candidate_to_baseline"
                ),
                "candidate_to_reference_paired_median": paired_median(
                    rows, surface, "candidate_to_reference"
                ),
                "arm_median_elapsed_nanoseconds": {
                    arm: statistics.median(
                        row["measurements"][surface][arm]["elapsed_nanoseconds"]
                        for row in rows
                    )
                    for arm in ARMS
                },
            }
            for surface in SURFACES
        },
        "relative_saving_retention_fraction": retention,
        "cell_summaries": cell_summaries,
        "hypothesis_support": hypothesis_support,
        "requirements": requirements,
        "requirements_passed": passed,
        "requirements_failed": len(requirements) - passed,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "real_backend_row_count": 0,
        "claim_boundary": {
            "external_monkeypatch_harness": True,
            "cross_architecture_conclusion_pending_oracle": True,
            "upstream_patch_accepted": False,
            "full_transpilation_pipeline_benchmarked": False,
            "production_qiskit_remedy_claimed": False,
            "hardware_result_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "solved_frontier_claimed": False,
            "new_credit_delta": 0,
        },
        "worker_manifest_paths": [
            worker_path(platform_id, manifest["cell"]["cell_id"])
            for manifest in sorted(
                manifests, key=lambda item: item["cell"]["cell_id"]
            )
        ],
    }
    result["payload_hash"] = canonical_hash(result)
    write_json(root / PLATFORMS[platform_id]["result_path"], result)
    return result


def render_report(result: dict[str, Any]) -> str:
    direct = result["aggregate_surface_ratios"]["accelerator_entrypoint"]
    workflow = result["aggregate_surface_ratios"]["python_passmanager"]
    support = result["hypothesis_support"]
    lines = [
        f"# B4/B8/B10 R186 Full VF2 Workflow: {result['platform_id']}",
        "",
        f"- Status: `{result['status']}`",
        f"- Result payload hash: `{result['payload_hash']}`",
        f"- Requirements: `{result['requirements_passed']}/{result['requirements_passed'] + result['requirements_failed']}`",
        f"- Mapping checks: `{result['mapping_match_count']}/{result['mapping_check_count']}`",
        f"- Measured calls: `{result['measured_timing_call_count']}`",
        f"- Warmup calls: `{result['warmup_call_count']}`",
        "",
        "## Heuristic Question",
        "",
        "Does the exact-score representation remain faster after Qiskit's Python `VF2Layout` and `PassManager` orchestration is included?",
        "",
        "## Ratios",
        "",
        f"- Direct window/BigUint: `{direct['candidate_to_baseline_paired_median']:.9f}x`",
        f"- Direct window/prefix: `{direct['candidate_to_reference_paired_median']:.9f}x`",
        f"- PassManager window/BigUint: `{workflow['candidate_to_baseline_paired_median']:.9f}x`",
        f"- PassManager window/prefix: `{workflow['candidate_to_reference_paired_median']:.9f}x`",
        f"- Relative saving retained: `{result['relative_saving_retention_fraction']:.9f}`",
        "",
        "## Platform Hypotheses",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in support.items())
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This is an external source-faithful Qiskit 2.4.1 monkeypatch harness, not an upstream integration or full transpilation benchmark. It contains zero simulations, zero quantum shots, and zero real-backend rows. Cross-architecture classification remains pending until the standard-library oracle checks both platform results.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    parser.add_argument("--worker-cell")
    parser.add_argument("--preregistration-commit", required=True)
    parser.add_argument("--preregistration-discussion", required=True)
    parser.add_argument("--preregistration-created-at", required=True)
    args = parser.parse_args()
    root = (args.root or Path(__file__).resolve().parents[1]).resolve()
    protocol, design, execution, r181 = load_inputs(root)
    validate_contracts(root, protocol, design, execution)
    preregistration = runtime_preregistration(root, args, execution)
    verify_platform(args.platform)

    if args.worker_cell:
        execute_worker(
            root,
            args.platform,
            protocol,
            design,
            execution,
            r181,
            args.worker_cell,
            preregistration,
        )
        return 0

    verify_clean_public_commit(root, preregistration["commit"])
    definition = PLATFORMS[args.platform]
    for relative in (definition["result_path"], definition["report_path"]):
        if (root / relative).exists():
            raise ValueError(f"R186 platform output already exists: {relative}")
    out_dir = root / definition["out_dir"]
    if out_dir.exists():
        raise ValueError(f"R186 platform worker directory already exists: {out_dir}")
    overlay = prepare_overlay(root, args.platform, protocol)
    cells = cell_definitions(r181)
    for cell in cells:
        launch_worker(
            root,
            overlay,
            args.platform,
            cell["cell_id"],
            preregistration,
        )
    manifests = []
    for cell in cells:
        path = root / worker_path(args.platform, cell["cell_id"])
        manifest = json.loads(path.read_text(encoding="utf-8"))
        validate_worker(manifest, path)
        manifests.append(manifest)
    result = classify_platform(
        root, args.platform, protocol, design, execution, manifests
    )
    (root / definition["report_path"]).write_text(
        render_report(result), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "platform_id": args.platform,
                "status": result["status"],
                "requirements": [
                    result["requirements_passed"],
                    result["requirements_failed"],
                ],
                "hypothesis_support": result["hypothesis_support"],
                "result_payload_hash": result["payload_hash"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
