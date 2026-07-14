#!/usr/bin/env python3
"""Execute the preregistered R158 VF2 accelerator-boundary matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from qiskit import qasm3
from qiskit._accelerate.error_map import ErrorMap
from qiskit._accelerate.vf2_layout import (
    VF2PassConfiguration,
    vf2_layout_pass_average,
)
from qiskit.converters import circuit_to_dag
from qiskit.transpiler import PropertySet
from qiskit.transpiler.passes import VF2PostLayout

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r128_transpiler_loop_layout_ranking import package_version
from b4_b8_r153_independent_seed_replication_holdout import TARGET_CLASSES
from b4_b8_r154_deterministic_automatic_replay import canonical_hash, target_descriptor


METHOD = "b4_b8_r158_vf2_accelerator_boundary_v0"
CONTRACT_PATH = "benchmarks/B4_B8_R158_vf2_accelerator_boundary_contract_v0.json"
CONTRACT_SHA256 = "c8ac00cb607174fa6d200c942810548f0b48e5efedf5a8bd119c56c230cfb8f8"
PROTOCOL_PATH = "results/B4_B8_R158_vf2_accelerator_boundary_protocol_v0.json"
PROTOCOL_PAYLOAD_HASH = "088054a2e0ae46638675e18c97f9f585edb930895ccb0c42891ccf89fc74abe2"
PREREGISTRATION_COMMIT = "1c996a0d27f8fa95581258988f620827f95deccc"
PREREGISTRATION_DISCUSSION = "https://github.com/crystal-tensor/Prometheus-plan/discussions/178"
PREREGISTRATION_CREATED_AT = "2026-07-14T07:20:00Z"
OUT_DIR = "results/B4_B8_R158_vf2_accelerator_boundary"
PROFILE_DISTRIBUTIONS_PATH = f"{OUT_DIR}/profile_distributions.json"
CONTRAST_MATRIX_PATH = f"{OUT_DIR}/contrast_matrix.json"
TRANSCRIPT_PATH = f"{OUT_DIR}/verifier_transcript.json"
RESULT_PATH = "results/B4_B8_R158_vf2_accelerator_boundary_v0.json"
REPORT_PATH = "research/B4_B8_R158_vf2_accelerator_boundary.md"
EXPECTED_MAPPINGS = {
    "endpoint_4_to_0": [6, 5, 4, 3, 0, 1, 2],
    "endpoint_4_to_2": [6, 5, 4, 3, 2, 1, 0],
}
MAPPING_CLASSES = ["endpoint_4_to_0", "endpoint_4_to_2", "other_mapping", "no_solution"]


def utc_timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def condition(condition_id: str, label: str, value: Any, threshold: Any, passed: bool) -> dict[str, Any]:
    return {"condition_id": condition_id, "label": label, "value": value, "threshold": threshold, "passed": passed}


def ensure_environment(protocol: dict[str, Any]) -> None:
    expected = protocol["process_environment"]
    actual = {key: os.environ.get(key) for key in expected}
    if actual == expected:
        return
    environment = dict(os.environ)
    environment.update(expected)
    os.execvpe(sys.executable, [sys.executable, *sys.argv], environment)


def actual_environment(protocol: dict[str, Any]) -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "qiskit": package_version("qiskit"),
        "qiskit_aer": package_version("qiskit-aer"),
        "qiskit_ibm_runtime": package_version("qiskit-ibm-runtime"),
        "process_environment": {key: os.environ.get(key) for key in protocol["process_environment"]},
    }


def validate_bindings(root: Path, contract: dict, protocol_payload: dict) -> None:
    if file_sha256(root / CONTRACT_PATH) != CONTRACT_SHA256:
        raise ValueError("R158 contract hash mismatch")
    if protocol_payload.get("payload_hash") != PROTOCOL_PAYLOAD_HASH:
        raise ValueError("R158 protocol payload hash mismatch")
    if contract.get("contract_id") != "B4-B8-R158-vf2-accelerator-boundary-contract-v0":
        raise ValueError("R158 contract identity mismatch")
    if contract.get("target_id") != "T-B4-002bx/T-B8-003cb/T-B10-009bp":
        raise ValueError("R158 target binding mismatch")
    bindings = contract["source_bindings"]
    if bindings["protocol_payload_hash"] != PROTOCOL_PAYLOAD_HASH:
        raise ValueError("R158 protocol payload binding mismatch")
    if bindings["protocol_sha256"] != file_sha256(root / PROTOCOL_PATH):
        raise ValueError("R158 protocol file binding mismatch")
    for binding_id, binding in bindings.items():
        if binding_id in {"protocol_path", "protocol_payload_hash", "protocol_sha256"}:
            continue
        path = root / binding["path"]
        if not path.exists() or file_sha256(path) != binding["sha256"]:
            raise ValueError(f"R158 source binding mismatch: {binding_id}")
        if "payload_hash" in binding:
            payload = json.loads(path.read_text())
            if payload.get("payload_hash") != binding["payload_hash"]:
                raise ValueError(f"R158 source payload mismatch: {binding_id}")


def profile_by_id(protocol: dict[str, Any], profile_id: str) -> dict[str, Any]:
    try:
        return next(row for row in protocol["profiles"] if row["profile_id"] == profile_id)
    except StopIteration as exc:
        raise ValueError(f"unknown R158 profile: {profile_id}") from exc


def worker_path(profile_id: str) -> str:
    return f"{OUT_DIR}/{profile_id}.json"


def new_config() -> Any:
    return VF2PassConfiguration.from_legacy_api(
        call_limit=30000000,
        time_limit=None,
        max_trials=250000,
        shuffle_seed=-1,
        score_initial_layout=True,
    )


def deterministic_error_map(target: Any) -> tuple[Any, dict[str, Any]]:
    error_map = ErrorMap(target.num_qubits)
    rows = []
    concrete_qargs = sorted(qargs for qargs in target.qargs if qargs is not None)
    for qargs in concrete_qargs:
        operation_rows = []
        for name in sorted(target.operation_names_for_qargs(qargs)):
            properties = target[name].get(qargs)
            error = 0.0 if properties is None or properties.error is None else float(properties.error)
            operation_rows.append({"operation": name, "error": error})
        if not operation_rows:
            continue
        average_error = sum(row["error"] for row in operation_rows) / len(operation_rows)
        key = (qargs[0], qargs[0]) if len(qargs) == 1 else tuple(qargs)
        error_map.add_error(key, average_error)
        rows.append({"qargs": list(qargs), "error_map_key": list(key), "operation_rows": operation_rows, "average_error": average_error})
    descriptor = {"construction": "qargs ascending, operation names ascending, Python f64 sum", "row_count": len(rows), "rows": rows}
    descriptor["payload_hash"] = canonical_hash(descriptor)
    return error_map, descriptor


def layout_vector_from_python_layout(circuit: Any, layout: Any) -> list[int] | None:
    if layout is None:
        return None
    vector: list[int | None] = [None] * circuit.num_qubits
    for bit, physical in layout.get_virtual_bits().items():
        vector[circuit.find_bit(bit).index] = int(physical)
    if any(value is None for value in vector):
        raise ValueError(f"R158 incomplete Python layout: {vector}")
    return [int(value) for value in vector]


def mapping_vector_from_accelerator(mapping: Any, num_qubits: int) -> list[int] | None:
    if mapping is None:
        return None
    vector: list[int | None] = [None] * num_qubits
    for virtual, physical in mapping.items():
        vector[int(virtual)] = int(physical)
    if any(value is None for value in vector):
        raise ValueError(f"R158 incomplete accelerator mapping: {vector}")
    return [int(value) for value in vector]


def classify(vector: list[int] | None) -> str:
    if vector is None:
        return "no_solution"
    for class_id, expected in EXPECTED_MAPPINGS.items():
        if vector == expected:
            return class_id
    return "other_mapping"


def execute_worker(root: Path, protocol_payload: dict, profile_id: str) -> dict[str, Any]:
    protocol = protocol_payload["protocol"]
    profile = profile_by_id(protocol, profile_id)
    path = root / worker_path(profile_id)
    if path.exists():
        raise ValueError(f"R158 worker evidence already exists: {profile_id}")
    started_at = int(time.time())
    circuit = qasm3.load(root / protocol["input_path"])
    target = TARGET_CLASSES[protocol["snapshot_name"]]().target
    target_desc = target_descriptor(TARGET_CLASSES[protocol["snapshot_name"]]())
    shared_dag = circuit_to_dag(circuit) if profile["dag_reused"] else None
    shared_config = new_config() if profile["config_reused"] else None
    shared_error_map = None
    error_map_descriptor = None
    if profile["error_map_mode"] == "external_shared_sorted_construction":
        shared_error_map, error_map_descriptor = deterministic_error_map(target)
    object_ids = {
        "circuit": id(circuit),
        "target": id(target),
        "shared_dag": None if shared_dag is None else id(shared_dag),
        "shared_config": None if shared_config is None else id(shared_config),
        "shared_error_map": None if shared_error_map is None else id(shared_error_map),
    }
    # Keep fresh per-call objects alive so CPython cannot recycle their ids and
    # blur the identity ledger before the worker manifest is written.
    identity_guards = []
    rows = []
    for replay_index in range(profile["replays_per_process"]):
        started = time.perf_counter()
        if profile["entry_point"] == "VF2PostLayout.run":
            dag = circuit_to_dag(circuit)
            pass_ = VF2PostLayout(
                target=target,
                seed=-1,
                call_limit=30000000,
                time_limit=None,
                strict_direction=False,
                max_trials=250000,
            )
            pass_.property_set = PropertySet()
            pass_.run(dag)
            layout = pass_.property_set.get("post_layout")
            vector = layout_vector_from_python_layout(circuit, layout)
            stop = pass_.property_set.get("VF2PostLayout_stop_reason")
            stop_reason = None if stop is None else str(getattr(stop, "value", stop))
            row_ids = {"dag": id(dag), "config": None, "error_map": None, "pass": id(pass_)}
            identity_guards.extend((dag, pass_))
            has_solution = layout is not None
        else:
            dag = shared_dag if shared_dag is not None else circuit_to_dag(circuit)
            config = shared_config if shared_config is not None else new_config()
            output = vf2_layout_pass_average(
                dag,
                target,
                config,
                strict_direction=False,
                avg_error_map=shared_error_map,
            )
            mapping = output.new_mapping()
            vector = mapping_vector_from_accelerator(mapping, circuit.num_qubits)
            has_solution = bool(output.has_solution)
            stop_reason = "solution found" if vector is not None else ("no improvement" if has_solution else "no solution")
            row_ids = {"dag": id(dag), "config": id(config), "error_map": None if shared_error_map is None else id(shared_error_map), "pass": None}
            identity_guards.extend((dag, config))
        row = {
            "replay_index": replay_index,
            "profile_id": profile_id,
            "entry_point": profile["entry_point"],
            "object_ids": row_ids,
            "mapping_vector": vector,
            "mapping_class": classify(vector),
            "has_solution": has_solution,
            "stop_reason": stop_reason,
            "elapsed_seconds": time.perf_counter() - started,
            "simulation_execution_count": 0,
            "total_simulated_shots": 0,
        }
        row["replay_payload_hash"] = canonical_hash(row)
        rows.append(row)
    manifest = {
        "profile_id": profile_id,
        "process_id": os.getpid(),
        "process_instance_uuid": str(uuid.uuid4()),
        "started_at_unix": started_at,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "preregistration_discussion": PREREGISTRATION_DISCUSSION,
        "contract_sha256": CONTRACT_SHA256,
        "protocol_payload_hash": PROTOCOL_PAYLOAD_HASH,
        "environment": actual_environment(protocol),
        "input_qasm_sha256": file_sha256(root / protocol["input_path"]),
        "target_descriptor_sha256": target_desc["descriptor_hash"],
        "profile": profile,
        "shared_object_ids": object_ids,
        "error_map_descriptor": error_map_descriptor,
        "replay_count": len(rows),
        "replay_rows": rows,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
    }
    manifest["manifest_payload_hash"] = canonical_hash(manifest)
    write_json(path, manifest)
    return manifest


def launch_worker(root: Path, script: Path, profile_id: str) -> str:
    completed = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "--worker-profile", profile_id],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"R158 worker failed {profile_id}: {completed.stdout}\n{completed.stderr}")
    return profile_id


def distributions(protocol: dict[str, Any], manifests: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for profile in protocol["profiles"]:
        manifest = next(row for row in manifests if row["profile_id"] == profile["profile_id"])
        replays = manifest["replay_rows"]
        counts = Counter(row["mapping_class"] for row in replays)
        unique = sum(value > 0 for value in counts.values())
        id_counts = {
            key: len({row["object_ids"].get(key) for row in replays if row["object_ids"].get(key) is not None})
            for key in ["dag", "config", "error_map", "pass"]
        }
        rows.append({
            "profile_id": profile["profile_id"],
            "process_count": 1,
            "replay_count": len(replays),
            "mapping_class_counts": {key: counts.get(key, 0) for key in MAPPING_CLASSES},
            "unique_mapping_class_count": unique,
            "profile_outcome": "collapse" if unique == 1 else "variation",
            "observed_object_identity_counts": id_counts,
            "expected_reuse": {"dag": profile["dag_reused"], "config": profile["config_reused"], "target": True, "error_map": profile["error_map_mode"].startswith("external_shared")},
            "error_map_descriptor_payload_hash": None if manifest["error_map_descriptor"] is None else manifest["error_map_descriptor"]["payload_hash"],
        })
    payload = {"profile_count": len(rows), "total_process_count": len(manifests), "total_direct_replay_count": sum(row["replay_count"] for row in rows), "profile_rows": rows}
    payload["profile_distributions_payload_hash"] = canonical_hash(payload)
    return payload


def contrast_matrix(profile_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["profile_id"]: row for row in profile_rows}
    ids = [row["profile_id"] for row in profile_rows]
    contrasts = []
    labels = ["Python wrapper removal", "DAG and config reconstruction removal", "internal ErrorMap reconstruction removal"]
    for index, label in enumerate(labels):
        left, right = by_id[ids[index]], by_id[ids[index + 1]]
        contrasts.append({"contrast_id": f"C{index + 1}", "boundary": label, "left_profile_id": ids[index], "right_profile_id": ids[index + 1], "left_outcome": left["profile_outcome"], "right_outcome": right["profile_outcome"], "left_mapping_class_counts": left["mapping_class_counts"], "right_mapping_class_counts": right["mapping_class_counts"], "causal_mechanism_claimed": False})
    final = by_id[ids[-1]]
    if final["profile_outcome"] == "variation":
        verdict = "rust_internal_variation_survives"
    elif by_id[ids[-2]]["profile_outcome"] == "variation":
        verdict = "internal_error_map_boundary"
    elif by_id[ids[-3]]["profile_outcome"] == "variation":
        verdict = "dag_or_config_boundary"
    elif by_id[ids[0]]["profile_outcome"] == "variation":
        verdict = "python_wrapper_boundary"
    else:
        verdict = "boundary_nonreproduction"
    payload = {"contrast_count": 3, "contrast_rows": contrasts, "fully_shared_profile_id": ids[-1], "fully_shared_profile_outcome": final["profile_outcome"], "classification": verdict, "lower_level_mechanism_claimed": False}
    payload["contrast_matrix_payload_hash"] = canonical_hash(payload)
    return payload


def build_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# B4/B8 R158 VF2 Accelerator-Boundary Result",
        "",
        f"- Status: `{result['status']}`",
        f"- Profiles / processes / direct calls: `{summary['profile_count']}` / `{summary['process_count']}` / `{summary['direct_replay_count']}`",
        f"- Classification: `{summary['classification']}`",
        f"- Fully shared profile outcome: `{summary['fully_shared_profile_outcome']}`",
        f"- Aggregate mapping counts: `{summary['mapping_class_counts']}`",
        f"- Simulation executions / shots: `{summary['simulation_execution_count']}` / `{summary['total_simulated_shots']}`",
        f"- Conditions passed/failed: `{summary['acceptance_conditions_passed']}` / `{summary['acceptance_conditions_failed']}`",
        f"- Requirements passed/failed: `{result['requirements_passed']}` / `{result['requirements_failed']}`",
        "",
        "## Profile Distributions",
        "",
        "| Profile | A | B | Other | No solution | Outcome | DAG/config/map identities |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in result["profile_distributions"]["profile_rows"]:
        counts = row["mapping_class_counts"]
        ids = row["observed_object_identity_counts"]
        lines.append(f"| `{row['profile_id']}` | {counts['endpoint_4_to_0']} | {counts['endpoint_4_to_2']} | {counts['other_mapping']} | {counts['no_solution']} | `{row['profile_outcome']}` | {ids['dag']}/{ids['config']}/{ids['error_map']} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        summary["diagnostic_interpretation"],
        "",
        "## Claim Boundary",
        "",
        "This result localizes a call boundary only. It does not identify candidate enumeration, hash-state, iterator order, floating-point accumulation, or last-improvement retention as the mechanism. It does not claim a confirmed Qiskit bug, general compiler determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit.",
        "",
    ])
    return "\n".join(lines)


def aggregate(root: Path, protocol_payload: dict, contract: dict) -> dict[str, Any]:
    protocol = protocol_payload["protocol"]
    manifests = []
    artifacts = []
    for profile in protocol["profiles"]:
        rel = worker_path(profile["profile_id"])
        path = root / rel
        manifest = json.loads(path.read_text())
        hp = dict(manifest)
        ph = hp.pop("manifest_payload_hash", None)
        if ph != canonical_hash(hp):
            raise ValueError(f"R158 worker payload mismatch: {profile['profile_id']}")
        manifests.append(manifest)
        artifacts.append({"profile_id": profile["profile_id"], "path": rel, "sha256": file_sha256(path), "manifest_payload_hash": ph})
    replays = [row for manifest in manifests for row in manifest["replay_rows"]]
    replay_fields_complete = all(
        all(
            key in row
            for key in [
                "entry_point",
                "object_ids",
                "mapping_vector",
                "mapping_class",
                "stop_reason",
                "elapsed_seconds",
            ]
        )
        for row in replays
    )
    replay_hashes_valid = all(
        row.get("replay_payload_hash")
        == canonical_hash({key: value for key, value in row.items() if key != "replay_payload_hash"})
        for row in replays
    )
    dist = distributions(protocol, manifests)
    contrasts = contrast_matrix(dist["profile_rows"])
    write_json(root / PROFILE_DISTRIBUTIONS_PATH, dist)
    write_json(root / CONTRAST_MATRIX_PATH, contrasts)
    counts = Counter(row["mapping_class"] for row in replays)
    after = all(manifest["started_at_unix"] >= utc_timestamp(PREREGISTRATION_CREATED_AT) for manifest in manifests)
    uuids = {manifest["process_instance_uuid"] for manifest in manifests}
    env_match = all(manifest["environment"]["process_environment"] == protocol["process_environment"] and manifest["environment"]["qiskit"] == protocol["frozen_software"]["qiskit"] for manifest in manifests)
    source_match = all(manifest["input_qasm_sha256"] == protocol["input_qasm_sha256"] and manifest["target_descriptor_sha256"] == protocol["target_descriptor_sha256"] for manifest in manifests)
    final_row = dist["profile_rows"][-1]
    final_identity = final_row["observed_object_identity_counts"]
    fully_shared = final_identity["dag"] == final_identity["config"] == final_identity["error_map"] == 1
    map_descriptor = manifests[-1]["error_map_descriptor"]
    map_bound = map_descriptor is not None and map_descriptor["row_count"] > 0 and map_descriptor["payload_hash"] == final_row["error_map_descriptor_payload_hash"]
    if contrasts["classification"] == "rust_internal_variation_survives":
        interpretation = "Variation survives repeated direct calls with one shared DAG, Target, configuration, and external ErrorMap. The observation boundary therefore moves inside per-call Rust VF2 graph/state/scoring construction, without identifying which internal operation is causal."
    else:
        interpretation = f"The staged boundary classification is {contrasts['classification']}; this localizes a reconstruction layer but does not identify a lower-level mechanism."
    summary = {
        "profile_count": 4,
        "process_count": len(manifests),
        "process_instance_uuid_count": len(uuids),
        "process_started_after_preregistration_count": sum(manifest["started_at_unix"] >= utc_timestamp(PREREGISTRATION_CREATED_AT) for manifest in manifests),
        "direct_replay_count": len(replays),
        "mapping_class_counts": {key: counts.get(key, 0) for key in MAPPING_CLASSES},
        "profile_collapse_count": sum(row["profile_outcome"] == "collapse" for row in dist["profile_rows"]),
        "profile_variation_count": sum(row["profile_outcome"] == "variation" for row in dist["profile_rows"]),
        "classification": contrasts["classification"],
        "fully_shared_profile_outcome": contrasts["fully_shared_profile_outcome"],
        "fully_shared_object_identity_verified": fully_shared,
        "external_error_map_descriptor_bound": map_bound,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "new_hidden_seed_count": 0,
        "candidate_selection_performed": False,
        "route_change_performed": False,
        "sampling_performed": False,
        "candidate_order_instrumented": False,
        "lower_level_mechanism_claimed": False,
        "qiskit_bug_claimed": False,
        "hardware_execution_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
        "diagnostic_interpretation": interpretation,
    }
    acceptance = [
        condition("A1", "contract, protocol, R157 evidence, source manifest, input, target, and binary hashes remain exact", True, True, True),
        condition("A2", "4 post-registration process artifacts retain 256 rows", [len(manifests), len(uuids), summary["process_started_after_preregistration_count"], len(replays)], [4, 4, 4, 256], len(manifests) == len(uuids) == summary["process_started_after_preregistration_count"] == 4 and len(replays) == 256),
        condition("A3", "all rows use the frozen source and environment", [env_match, source_match], [True, True], env_match and source_match),
        condition("A4", "all four profiles complete without replacement", len(dist["profile_rows"]), 4, len(dist["profile_rows"]) == 4 and all(row["replay_count"] == 64 for row in dist["profile_rows"])),
        condition(
            "A5",
            "entry point, object identities, mapping, stop reason, elapsed time, and row hashes are retained",
            [replay_fields_complete, replay_hashes_valid],
            [True, True],
            replay_fields_complete and replay_hashes_valid,
        ),
        condition("A6", "external ErrorMap is constructed once and reused", [fully_shared, map_bound], [True, True], fully_shared and map_bound),
        condition("A7", "new mappings and no-solution rows remain classified", sum(counts.values()), 256, sum(counts.values()) == 256),
        condition("A8", "three staged contrasts and fully shared verdict are emitted", contrasts["contrast_count"], 3, contrasts["contrast_count"] == 3),
        condition("A9", "two R157 mappings and tied score remain bound", protocol["shared_tied_score"], 0.45894321220828727, protocol["shared_tied_score"] == 0.45894321220828727),
        condition("A10", "forbidden claims remain false", 0, 0, True),
    ]
    requirements = [{"requirement_id": f"P{i}", "label": label, "passed": passed} for i, (label, passed) in enumerate([
        ("public preregistration precedes all four processes", after),
        ("protocol, contract, source lineage, binary, and R157 inputs are bound", True),
        ("four unique process identities are retained", len(uuids) == 4),
        ("all 256 replay rows retain required fields", len(replays) == 256),
        ("all four staged profiles complete", len(dist["profile_rows"]) == 4),
        ("the final profile reuses DAG, config, and ErrorMap", fully_shared),
        ("all outcomes remain classified", sum(counts.values()) == 256),
        ("three contrasts and the final verdict are complete", contrasts["contrast_count"] == 3),
        ("no simulation, shots, or sampling occur", True),
        ("no candidate-order, mechanism, bug, hardware, advantage, BQP, solved-frontier, or credit claim", True),
    ], 1)]
    summary["acceptance_conditions_passed"] = sum(row["passed"] for row in acceptance)
    summary["acceptance_conditions_failed"] = sum(not row["passed"] for row in acceptance)
    summary["global_acceptance"] = all(row["passed"] for row in acceptance)
    result = {
        "title": "B4/B8 R158 VF2 accelerator boundary",
        "version": 0,
        "method": METHOD,
        "status": "vf2_accelerator_boundary_diagnostic_complete" if summary["global_acceptance"] else "vf2_accelerator_boundary_diagnostic_incomplete",
        "model_status": "source_bound_call_localization_without_lower_level_mechanism_overclaim",
        "generated_at_unix": int(time.time()),
        "source_target_id": "T-B4-002by/T-B8-003cc/T-B10-009bq",
        "upstream_target_id": "T-B4-002bx/T-B8-003cb/T-B10-009bp",
        "summary": summary,
        "profile_distributions": {key: value for key, value in dist.items() if key != "profile_distributions_payload_hash"},
        "contrast_matrix": {key: value for key, value in contrasts.items() if key != "contrast_matrix_payload_hash"},
        "acceptance_conditions": acceptance,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [row["requirement_id"] for row in requirements if not row["passed"]],
        "artifacts": {"protocol": PROTOCOL_PATH, "contract": CONTRACT_PATH, "result": RESULT_PATH, "markdown_report": REPORT_PATH, "process_artifacts": artifacts, "profile_distributions": PROFILE_DISTRIBUTIONS_PATH, "contrast_matrix": CONTRAST_MATRIX_PATH, "verifier_transcript": TRANSCRIPT_PATH},
        "claim_boundary": {"what_is_supported": "one source-bound staged call-boundary diagnostic over the two exactly tied R157 mappings", "what_is_not_supported": "candidate-order instrumentation, a lower-level hash, iterator, floating-point, or retention mechanism, a confirmed Qiskit bug, hardware performance, advantage, BQP separation, solved B4/B8/B10, or new credit"},
    }
    result["payload_hash"] = canonical_hash(result)
    transcript = {"contract_sha256": CONTRACT_SHA256, "protocol_payload_hash": PROTOCOL_PAYLOAD_HASH, "result_payload_hash": result["payload_hash"], "profile_distributions_payload_hash": dist["profile_distributions_payload_hash"], "contrast_matrix_payload_hash": contrasts["contrast_matrix_payload_hash"], "process_artifact_count": len(artifacts), "direct_replay_count": len(replays), "global_acceptance": summary["global_acceptance"], "requirements_passed": result["requirements_passed"], "requirements_failed": result["requirements_failed"]}
    transcript["verifier_transcript_payload_hash"] = canonical_hash(transcript)
    write_json(root / TRANSCRIPT_PATH, transcript)
    write_json(root / RESULT_PATH, result)
    (root / REPORT_PATH).write_text(build_report(result), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the preregistered R158 VF2 accelerator-boundary matrix.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--worker-profile")
    args = parser.parse_args()
    root = args.root.resolve()
    protocol_payload = json.loads((root / PROTOCOL_PATH).read_text())
    contract = json.loads((root / CONTRACT_PATH).read_text())
    protocol = protocol_payload["protocol"]
    ensure_environment(protocol)
    validate_bindings(root, contract, protocol_payload)
    if args.worker_profile:
        execute_worker(root, protocol_payload, args.worker_profile)
        return 0
    if (root / OUT_DIR).exists() or (root / RESULT_PATH).exists() or (root / REPORT_PATH).exists():
        raise ValueError("R158 execution evidence already exists; refusing to overwrite")
    script = Path(__file__).resolve()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(launch_worker, root, script, profile["profile_id"]): profile["profile_id"] for profile in protocol["profiles"]}
        for future in as_completed(futures):
            print(f"R158 worker complete: {future.result()}")
    result = aggregate(root, protocol_payload, contract)
    print(json.dumps({"status": result["status"], "classification": result["summary"]["classification"], "mapping_class_counts": result["summary"]["mapping_class_counts"], "profile_variation_count": result["summary"]["profile_variation_count"], "requirements_passed": result["requirements_passed"], "requirements_failed": result["requirements_failed"], "payload_hash": result["payload_hash"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
