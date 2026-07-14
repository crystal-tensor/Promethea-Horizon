#!/usr/bin/env python3
"""Execute the preregistered R159 ErrorMap accumulation trace matrix."""

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
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r128_transpiler_loop_layout_ranking import package_version
from b4_b8_r153_independent_seed_replication_holdout import TARGET_CLASSES
from b4_b8_r154_deterministic_automatic_replay import canonical_hash, target_descriptor


METHOD = "b4_b8_r159_error_map_accumulation_trace_v0"
PROTOCOL_PATH = "results/B4_B8_R159_error_map_accumulation_trace_protocol_v0.json"
CONTRACT_PATH = "benchmarks/B4_B8_R159_error_map_accumulation_trace_contract_v0.json"
BUILD_MANIFEST_PATH = "research/source_lineage/Qiskit_2_4_1_R159_instrumented_build_manifest.json"
OUT_DIR = "results/B4_B8_R159_error_map_accumulation_trace"
PROFILE_SUMMARY_PATH = f"{OUT_DIR}/profile_summary.json"
ASSOCIATION_PATH = f"{OUT_DIR}/trace_mapping_associations.json"
TRANSCRIPT_PATH = f"{OUT_DIR}/verifier_transcript.json"
RESULT_PATH = "results/B4_B8_R159_error_map_accumulation_trace_v0.json"
REPORT_PATH = "research/B4_B8_R159_error_map_accumulation_trace.md"
EXPECTED_MAPPINGS = {
    "endpoint_4_to_0": [6, 5, 4, 3, 0, 1, 2],
    "endpoint_4_to_2": [6, 5, 4, 3, 2, 1, 0],
}
MAPPING_CLASSES = ["endpoint_4_to_0", "endpoint_4_to_2", "other_mapping", "no_solution"]


def utc_timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


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


def validate_payload(payload: dict[str, Any], label: str) -> str:
    body = dict(payload)
    payload_hash = body.pop("payload_hash", None)
    if payload_hash != canonical_hash(body):
        raise ValueError(f"R159 {label} payload hash mismatch")
    return payload_hash


def validate_bindings(root: Path, protocol_payload: dict, contract: dict) -> tuple[str, str]:
    protocol_hash = validate_payload(protocol_payload, "protocol")
    contract_hash = validate_payload(contract, "contract")
    if protocol_payload.get("method") != "b4_b8_r159_error_map_accumulation_trace_protocol_v0":
        raise ValueError("R159 protocol identity mismatch")
    if contract.get("contract_id") != "B4-B8-R159-error-map-accumulation-trace-contract-v0":
        raise ValueError("R159 contract identity mismatch")
    bindings = contract["source_bindings"]
    if bindings["protocol"]["payload_hash"] != protocol_hash:
        raise ValueError("R159 contract protocol payload binding mismatch")
    for binding_id, binding in bindings.items():
        path = root / binding["path"]
        if not path.exists() or file_sha256(path) != binding["sha256"]:
            raise ValueError(f"R159 source binding mismatch: {binding_id}")
        if "payload_hash" in binding:
            payload = json.loads(path.read_text())
            if payload.get("payload_hash") != binding["payload_hash"]:
                raise ValueError(f"R159 source payload mismatch: {binding_id}")
    build_manifest = json.loads((root / BUILD_MANIFEST_PATH).read_text())
    validate_payload(build_manifest, "build manifest")
    import qiskit._accelerate as accelerate
    from qiskit._accelerate import vf2_layout

    binary_path = Path(accelerate.__file__).resolve()
    if file_sha256(binary_path) != build_manifest["instrumented_binary"]["sha256"]:
        raise ValueError("R159 imported accelerator binary hash mismatch")
    if binary_path.stat().st_size != build_manifest["instrumented_binary"]["size_bytes"]:
        raise ValueError("R159 imported accelerator binary size mismatch")
    if not hasattr(vf2_layout, "vf2_layout_pass_average_traced"):
        raise ValueError("R159 traced accelerator entry point missing")
    return protocol_hash, contract_hash


def profile_by_id(protocol: dict[str, Any], profile_id: str) -> dict[str, Any]:
    try:
        return next(row for row in protocol["profiles"] if row["profile_id"] == profile_id)
    except StopIteration as exc:
        raise ValueError(f"unknown R159 profile: {profile_id}") from exc


def worker_path(profile_id: str) -> str:
    return f"{OUT_DIR}/{profile_id}.json"


def new_config() -> Any:
    from qiskit._accelerate.vf2_layout import VF2PassConfiguration

    return VF2PassConfiguration.from_legacy_api(
        call_limit=30000000,
        time_limit=None,
        max_trials=250000,
        shuffle_seed=-1,
        score_initial_layout=True,
    )


def mapping_vector(mapping: Any, num_qubits: int) -> list[int] | None:
    if mapping is None:
        return None
    vector: list[int | None] = [None] * num_qubits
    for virtual, physical in mapping.items():
        vector[int(virtual)] = int(physical)
    if any(value is None for value in vector):
        raise ValueError(f"R159 incomplete accelerator mapping: {vector}")
    return [int(value) for value in vector]


def classify(vector: list[int] | None) -> str:
    if vector is None:
        return "no_solution"
    for class_id, expected in EXPECTED_MAPPINGS.items():
        if vector == expected:
            return class_id
    return "other_mapping"


def normalize_trace(raw_trace: Any) -> list[dict[str, Any]]:
    rows = []
    for qargs, raw_steps, average_error_bits in raw_trace:
        steps = [
            {
                "operation": str(operation),
                "error_bits": int(error_bits),
                "accumulated_error_bits": int(accumulated_error_bits),
            }
            for operation, error_bits, accumulated_error_bits in raw_steps
        ]
        rows.append({
            "qargs": [int(value) for value in qargs],
            "steps": steps,
            "average_error_bits": int(average_error_bits),
        })
    return rows


def trace_signatures(trace_rows: list[dict[str, Any]]) -> tuple[str, str, str]:
    order_payload = [
        {"qargs": row["qargs"], "operations": [step["operation"] for step in row["steps"]]}
        for row in trace_rows
    ]
    error_bits_payload = [
        {"qargs": row["qargs"], "average_error_bits": row["average_error_bits"]}
        for row in trace_rows
    ]
    return canonical_hash(order_payload), canonical_hash(error_bits_payload), canonical_hash(trace_rows)


def execute_worker(
    root: Path,
    protocol_payload: dict[str, Any],
    contract: dict[str, Any],
    profile_id: str,
    preregistration: dict[str, str],
) -> dict[str, Any]:
    from qiskit import qasm3
    from qiskit._accelerate.vf2_layout import vf2_layout_pass_average_traced
    from qiskit.converters import circuit_to_dag

    protocol = protocol_payload["protocol"]
    profile = profile_by_id(protocol, profile_id)
    path = root / worker_path(profile_id)
    if path.exists():
        raise ValueError(f"R159 worker evidence already exists: {profile_id}")
    started_at = int(time.time())
    circuit = qasm3.load(root / protocol["input_path"])
    backend = TARGET_CLASSES[protocol["snapshot_name"]]()
    target = backend.target
    target_desc = target_descriptor(backend)
    dag = circuit_to_dag(circuit)
    config = new_config()
    identity_guards = [circuit, backend, target, dag, config]
    rows = []
    for replay_index in range(profile["replay_count"]):
        started = time.perf_counter()
        output, raw_trace = vf2_layout_pass_average_traced(
            dag,
            target,
            config,
            strict_direction=False,
            operation_order=profile["operation_order"],
        )
        trace_rows = normalize_trace(raw_trace)
        order_hash, error_bits_hash, trace_hash = trace_signatures(trace_rows)
        mapping = output.new_mapping()
        vector = mapping_vector(mapping, circuit.num_qubits)
        has_solution = bool(output.has_solution)
        row = {
            "replay_index": replay_index,
            "profile_id": profile_id,
            "operation_order": profile["operation_order"],
            "mapping_vector": vector,
            "mapping_class": classify(vector),
            "has_solution": has_solution,
            "stop_reason": "solution found" if vector is not None else ("no improvement" if has_solution else "no solution"),
            "trace_row_count": len(trace_rows),
            "operation_order_hash": order_hash,
            "average_error_bits_hash": error_bits_hash,
            "full_trace_hash": trace_hash,
            "trace_rows": trace_rows,
            "elapsed_seconds": time.perf_counter() - started,
            "simulation_execution_count": 0,
            "total_simulated_shots": 0,
        }
        row["replay_payload_hash"] = canonical_hash(row)
        rows.append(row)
    del identity_guards
    manifest = {
        "profile_id": profile_id,
        "process_id": os.getpid(),
        "process_instance_uuid": str(uuid.uuid4()),
        "started_at_unix": started_at,
        "preregistration": preregistration,
        "protocol_payload_hash": protocol_payload["payload_hash"],
        "contract_payload_hash": contract["payload_hash"],
        "environment": actual_environment(protocol),
        "input_qasm_sha256": file_sha256(root / protocol["input_path"]),
        "target_descriptor_sha256": target_desc["descriptor_hash"],
        "profile": profile,
        "shared_object_ids": {
            "circuit": id(circuit),
            "target": id(target),
            "dag": id(dag),
            "config": id(config),
        },
        "replay_count": len(rows),
        "replay_rows": rows,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
    }
    manifest["manifest_payload_hash"] = canonical_hash(manifest)
    write_json(path, manifest)
    return manifest


def launch_worker(
    root: Path,
    script: Path,
    profile_id: str,
    preregistration: dict[str, str],
) -> str:
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(root),
            "--worker-profile",
            profile_id,
            "--preregistration-commit",
            preregistration["commit"],
            "--preregistration-discussion",
            preregistration["discussion"],
            "--preregistration-created-at",
            preregistration["created_at"],
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"R159 worker failed {profile_id}: {completed.stdout}\n{completed.stderr}")
    return profile_id


def profile_summary(protocol: dict[str, Any], manifests: list[dict[str, Any]]) -> dict[str, Any]:
    profile_rows = []
    for profile in protocol["profiles"]:
        manifest = next(row for row in manifests if row["profile_id"] == profile["profile_id"])
        replays = manifest["replay_rows"]
        mapping_counts = Counter(row["mapping_class"] for row in replays)
        profile_rows.append({
            "profile_id": profile["profile_id"],
            "operation_order": profile["operation_order"],
            "process_count": 1,
            "replay_count": len(replays),
            "mapping_class_counts": {key: mapping_counts.get(key, 0) for key in MAPPING_CLASSES},
            "unique_mapping_class_count": sum(value > 0 for value in mapping_counts.values()),
            "unique_operation_order_hash_count": len({row["operation_order_hash"] for row in replays}),
            "unique_average_error_bits_hash_count": len({row["average_error_bits_hash"] for row in replays}),
            "unique_full_trace_hash_count": len({row["full_trace_hash"] for row in replays}),
            "profile_outcome": "collapse" if sum(value > 0 for value in mapping_counts.values()) == 1 else "variation",
        })
    payload = {
        "profile_count": len(profile_rows),
        "total_process_count": len(manifests),
        "total_trace_replay_count": sum(row["replay_count"] for row in profile_rows),
        "profile_rows": profile_rows,
    }
    payload["profile_summary_payload_hash"] = canonical_hash(payload)
    return payload


def association_payload(manifests: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    native_manifest = next(row for row in manifests if row["profile_id"] == "native_hashset_order")
    order_to_error: defaultdict[str, set[str]] = defaultdict(set)
    error_to_mapping: defaultdict[str, set[str]] = defaultdict(set)
    for row in native_manifest["replay_rows"]:
        order_to_error[row["operation_order_hash"]].add(row["average_error_bits_hash"])
        error_to_mapping[row["average_error_bits_hash"]].add(row["mapping_class"])
    profile_by_id = {row["profile_id"]: row for row in summary["profile_rows"]}
    native = profile_by_id["native_hashset_order"]
    ascending = profile_by_id["ascending_sorted_order"]
    descending = profile_by_id["descending_sorted_order"]
    order_to_error_functional = all(len(values) == 1 for values in order_to_error.values())
    error_to_mapping_functional = all(len(values) == 1 for values in error_to_mapping.values())
    sorted_profiles_collapse = ascending["profile_outcome"] == descending["profile_outcome"] == "collapse"
    if native["profile_outcome"] == "collapse":
        classification = "native_nonreproduction"
    elif not sorted_profiles_collapse:
        classification = "variation_survives_sorted_accumulation"
    elif len(error_to_mapping) > 1 and order_to_error_functional and error_to_mapping_functional:
        classification = "operation_order_f64_path_supported"
    elif not error_to_mapping_functional:
        classification = "average_error_bits_insufficient_for_mapping"
    elif native["unique_operation_order_hash_count"] > 1 and native["unique_average_error_bits_hash_count"] == 1:
        classification = "operation_order_changes_without_average_bit_change"
    else:
        classification = "trace_inconclusive"
    payload = {
        "classification": classification,
        "native_operation_order_hash_count": len(order_to_error),
        "native_average_error_bits_hash_count": len(error_to_mapping),
        "native_order_to_error_functional": order_to_error_functional,
        "native_error_bits_to_mapping_functional": error_to_mapping_functional,
        "native_order_hashes_with_multiple_error_maps": sum(len(values) > 1 for values in order_to_error.values()),
        "native_error_maps_with_multiple_mappings": sum(len(values) > 1 for values in error_to_mapping.values()),
        "sorted_profiles_collapse": sorted_profiles_collapse,
        "ascending_mapping_class_counts": ascending["mapping_class_counts"],
        "descending_mapping_class_counts": descending["mapping_class_counts"],
        "causal_mechanism_claimed": False,
        "confirmed_qiskit_bug_claimed": False,
    }
    payload["association_payload_hash"] = canonical_hash(payload)
    return payload


def condition(condition_id: str, label: str, value: Any, threshold: Any, passed: bool) -> dict[str, Any]:
    return {"condition_id": condition_id, "label": label, "value": value, "threshold": threshold, "passed": passed}


def build_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# B4/B8 R159 ErrorMap Accumulation Trace",
        "",
        f"- Status: `{result['status']}`",
        f"- Classification: `{summary['classification']}`",
        f"- Profiles / processes / traced calls: `{summary['profile_count']}` / `{summary['process_count']}` / `{summary['trace_replay_count']}`",
        f"- Aggregate mapping counts: `{summary['mapping_class_counts']}`",
        f"- Native order/error-bit hashes: `{summary['native_operation_order_hash_count']}` / `{summary['native_average_error_bits_hash_count']}`",
        f"- Native order->bits / bits->mapping functional: `{summary['native_order_to_error_functional']}` / `{summary['native_error_bits_to_mapping_functional']}`",
        f"- Sorted profiles collapse: `{summary['sorted_profiles_collapse']}`",
        f"- Simulation executions / shots: `{summary['simulation_execution_count']}` / `{summary['total_simulated_shots']}`",
        f"- Conditions passed/failed: `{summary['acceptance_conditions_passed']}` / `{summary['acceptance_conditions_failed']}`",
        f"- Requirements passed/failed: `{result['requirements_passed']}` / `{result['requirements_failed']}`",
        "",
        "## Profile Summary",
        "",
        "| Profile | A | B | Other | No solution | Order hashes | Error-bit hashes | Outcome |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["profile_summary"]["profile_rows"]:
        counts = row["mapping_class_counts"]
        lines.append(
            f"| `{row['profile_id']}` | {counts['endpoint_4_to_0']} | {counts['endpoint_4_to_2']} | "
            f"{counts['other_mapping']} | {counts['no_solution']} | {row['unique_operation_order_hash_count']} | "
            f"{row['unique_average_error_bits_hash_count']} | `{row['profile_outcome']}` |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        summary["diagnostic_interpretation"],
        "",
        "## Claim Boundary",
        "",
        "This source-instrumented diagnostic can support or reject a specific ErrorMap accumulation path. It does not by itself establish a confirmed Qiskit bug, a cross-platform compiler theorem, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.",
        "",
    ])
    return "\n".join(lines)


def aggregate(
    root: Path,
    protocol_payload: dict[str, Any],
    contract: dict[str, Any],
    preregistration: dict[str, str],
) -> dict[str, Any]:
    protocol = protocol_payload["protocol"]
    manifests = []
    process_artifacts = []
    for profile in protocol["profiles"]:
        rel = worker_path(profile["profile_id"])
        path = root / rel
        manifest = json.loads(path.read_text())
        body = dict(manifest)
        payload_hash = body.pop("manifest_payload_hash", None)
        if payload_hash != canonical_hash(body):
            raise ValueError(f"R159 worker payload mismatch: {profile['profile_id']}")
        manifests.append(manifest)
        process_artifacts.append({
            "profile_id": profile["profile_id"],
            "path": rel,
            "sha256": file_sha256(path),
            "manifest_payload_hash": payload_hash,
        })
    replays = [row for manifest in manifests for row in manifest["replay_rows"]]
    profiles = profile_summary(protocol, manifests)
    associations = association_payload(manifests, profiles)
    write_json(root / PROFILE_SUMMARY_PATH, profiles)
    write_json(root / ASSOCIATION_PATH, associations)
    counts = Counter(row["mapping_class"] for row in replays)
    preregistered_at = utc_timestamp(preregistration["created_at"])
    after_preregistration = all(manifest["started_at_unix"] >= preregistered_at for manifest in manifests)
    process_uuids = {manifest["process_instance_uuid"] for manifest in manifests}
    environment_match = all(
        manifest["environment"]["process_environment"] == protocol["process_environment"]
        and manifest["environment"]["qiskit"] == protocol["frozen_software"]["qiskit"]
        for manifest in manifests
    )
    source_match = all(
        manifest["input_qasm_sha256"] == protocol["input_qasm_sha256"]
        and manifest["target_descriptor_sha256"] == protocol["target_descriptor_sha256"]
        for manifest in manifests
    )
    trace_complete = all(
        row["trace_row_count"] > 0
        and row["operation_order_hash"]
        and row["average_error_bits_hash"]
        and row["full_trace_hash"]
        and row["replay_payload_hash"]
        for row in replays
    )
    all_replay_hashes_valid = all(
        row["replay_payload_hash"]
        == canonical_hash({key: value for key, value in row.items() if key != "replay_payload_hash"})
        for row in replays
    )
    if associations["classification"] == "operation_order_f64_path_supported":
        interpretation = "Native HashSet order changes produce multiple average-error bit maps, each bit map predicts one tied mapping, and both sorted controls collapse. This supports the operation-order-to-f64-to-selection path in this instrumented build, without elevating it to a confirmed general bug claim."
    elif associations["classification"] == "average_error_bits_insufficient_for_mapping":
        interpretation = "At least one identical retained average-error bit map leads to both tied mappings, so ErrorMap numeric values alone do not explain selection."
    elif associations["classification"] == "variation_survives_sorted_accumulation":
        interpretation = "At least one sorted accumulation control still varies, so sorting ErrorMap operation accumulation is insufficient to stabilize the tied selection."
    else:
        interpretation = f"The preregistered trace classification is {associations['classification']}; the retained trace does not support a broader causal claim."
    summary = {
        "profile_count": len(profiles["profile_rows"]),
        "process_count": len(manifests),
        "process_instance_uuid_count": len(process_uuids),
        "process_started_after_preregistration_count": sum(manifest["started_at_unix"] >= preregistered_at for manifest in manifests),
        "trace_replay_count": len(replays),
        "mapping_class_counts": {key: counts.get(key, 0) for key in MAPPING_CLASSES},
        "profile_collapse_count": sum(row["profile_outcome"] == "collapse" for row in profiles["profile_rows"]),
        "profile_variation_count": sum(row["profile_outcome"] == "variation" for row in profiles["profile_rows"]),
        "classification": associations["classification"],
        "native_operation_order_hash_count": associations["native_operation_order_hash_count"],
        "native_average_error_bits_hash_count": associations["native_average_error_bits_hash_count"],
        "native_order_to_error_functional": associations["native_order_to_error_functional"],
        "native_error_bits_to_mapping_functional": associations["native_error_bits_to_mapping_functional"],
        "sorted_profiles_collapse": associations["sorted_profiles_collapse"],
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "new_hidden_seed_count": 0,
        "candidate_selection_performed": False,
        "route_change_performed": False,
        "sampling_performed": False,
        "confirmed_qiskit_bug_claimed": False,
        "hardware_execution_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
        "diagnostic_interpretation": interpretation,
    }
    acceptance = [
        condition("A1", "protocol, contract, patch, build manifest, binary, input, target, and R158 result remain bound", True, True, True),
        condition("A2", "three post-registration process artifacts retain 256 calls", [len(manifests), len(process_uuids), len(replays)], [3, 3, 256], len(manifests) == len(process_uuids) == 3 and len(replays) == 256 and after_preregistration),
        condition("A3", "all calls use the frozen source and environment", [environment_match, source_match], [True, True], environment_match and source_match),
        condition("A4", "native, ascending, and descending profiles complete without replacement", [row["replay_count"] for row in profiles["profile_rows"]], [128, 64, 64], [row["replay_count"] for row in profiles["profile_rows"]] == [128, 64, 64]),
        condition("A5", "every call retains operation order, f64 accumulation, average bits, mapping, and row hash", [trace_complete, all_replay_hashes_valid], [True, True], trace_complete and all_replay_hashes_valid),
        condition("A6", "profile summary and trace-to-mapping associations are emitted", [len(profiles["profile_rows"]), bool(associations["classification"])], [3, True], len(profiles["profile_rows"]) == 3 and bool(associations["classification"])),
        condition("A7", "all mapping and no-solution outcomes remain classified", sum(counts.values()), 256, sum(counts.values()) == 256),
        condition("A8", "native order-to-bits and bits-to-mapping tests are retained regardless of verdict", ["native_order_to_error_functional" in associations, "native_error_bits_to_mapping_functional" in associations], [True, True], True),
        condition("A9", "the two R157 mappings and exact tied score remain bound", protocol["shared_tied_score"], 0.45894321220828727, protocol["shared_tied_score"] == 0.45894321220828727),
        condition("A10", "forbidden bug, hardware, advantage, BQP, solved-frontier, and credit claims remain false", 0, 0, True),
    ]
    requirements = [{"requirement_id": f"P{index}", "label": label, "passed": passed} for index, (label, passed) in enumerate([
        ("public preregistration precedes all three process artifacts", after_preregistration),
        ("instrumented source patch and compiled binary are hash-bound", True),
        ("three unique process identities are retained", len(process_uuids) == 3),
        ("all 256 calls retain complete trace rows", len(replays) == 256 and trace_complete),
        ("native, ascending, and descending profiles complete", len(profiles["profile_rows"]) == 3),
        ("operation-order and average-error-bit associations are emitted", bool(associations["classification"])),
        ("all outcomes remain classified", sum(counts.values()) == 256),
        ("every replay and worker payload hash validates", all_replay_hashes_valid),
        ("no simulation, shots, sampling, candidate selection, or route change occurs", True),
        ("no confirmed bug, hardware, advantage, BQP, solved-frontier, or credit claim is made", True),
    ], 1)]
    summary["acceptance_conditions_passed"] = sum(row["passed"] for row in acceptance)
    summary["acceptance_conditions_failed"] = sum(not row["passed"] for row in acceptance)
    summary["global_acceptance"] = all(row["passed"] for row in acceptance)
    result = {
        "title": "B4/B8 R159 ErrorMap accumulation trace",
        "version": 0,
        "method": METHOD,
        "status": "error_map_accumulation_trace_complete" if summary["global_acceptance"] else "error_map_accumulation_trace_incomplete",
        "model_status": "source_instrumented_error_map_accumulation_diagnostic_without_confirmed_bug_claim",
        "generated_at_unix": int(time.time()),
        "source_target_id": "T-B4-002ca/T-B8-003ce/T-B10-009bs",
        "upstream_target_id": "T-B4-002bz/T-B8-003cd/T-B10-009br",
        "preregistration": preregistration,
        "summary": summary,
        "profile_summary": {key: value for key, value in profiles.items() if key != "profile_summary_payload_hash"},
        "trace_mapping_associations": {key: value for key, value in associations.items() if key != "association_payload_hash"},
        "acceptance_conditions": acceptance,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [row["requirement_id"] for row in requirements if not row["passed"]],
        "artifacts": {
            "protocol": PROTOCOL_PATH,
            "contract": CONTRACT_PATH,
            "build_manifest": BUILD_MANIFEST_PATH,
            "result": RESULT_PATH,
            "markdown_report": REPORT_PATH,
            "process_artifacts": process_artifacts,
            "profile_summary": PROFILE_SUMMARY_PATH,
            "trace_mapping_associations": ASSOCIATION_PATH,
            "verifier_transcript": TRANSCRIPT_PATH,
        },
        "claim_boundary": {
            "what_is_supported": "one source-instrumented native-versus-sorted ErrorMap accumulation diagnostic over the two exactly tied R157 mappings",
            "what_is_not_supported": "a confirmed Qiskit bug, cross-platform compiler theorem, hardware performance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    result["payload_hash"] = canonical_hash(result)
    transcript = {
        "protocol_payload_hash": protocol_payload["payload_hash"],
        "contract_payload_hash": contract["payload_hash"],
        "result_payload_hash": result["payload_hash"],
        "profile_summary_payload_hash": profiles["profile_summary_payload_hash"],
        "association_payload_hash": associations["association_payload_hash"],
        "process_artifact_count": len(process_artifacts),
        "trace_replay_count": len(replays),
        "global_acceptance": summary["global_acceptance"],
        "requirements_passed": result["requirements_passed"],
        "requirements_failed": result["requirements_failed"],
    }
    transcript["verifier_transcript_payload_hash"] = canonical_hash(transcript)
    write_json(root / TRANSCRIPT_PATH, transcript)
    write_json(root / RESULT_PATH, result)
    (root / REPORT_PATH).write_text(build_report(result), encoding="utf-8")
    return result


def parse_preregistration(args: argparse.Namespace) -> dict[str, str]:
    preregistration = {
        "commit": args.preregistration_commit,
        "discussion": args.preregistration_discussion,
        "created_at": args.preregistration_created_at,
    }
    if not all(preregistration.values()):
        raise ValueError("R159 preregistration commit, discussion, and created-at are required")
    if not preregistration["discussion"].startswith("https://github.com/crystal-tensor/Prometheus-plan/discussions/"):
        raise ValueError("R159 preregistration discussion URL mismatch")
    utc_timestamp(preregistration["created_at"])
    return preregistration


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the preregistered R159 ErrorMap accumulation trace matrix.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--worker-profile")
    parser.add_argument("--preregistration-commit")
    parser.add_argument("--preregistration-discussion")
    parser.add_argument("--preregistration-created-at")
    args = parser.parse_args()
    root = args.root.resolve()
    protocol_payload = json.loads((root / PROTOCOL_PATH).read_text())
    contract = json.loads((root / CONTRACT_PATH).read_text())
    protocol = protocol_payload["protocol"]
    ensure_environment(protocol)
    validate_bindings(root, protocol_payload, contract)
    preregistration = parse_preregistration(args)
    if args.worker_profile:
        execute_worker(root, protocol_payload, contract, args.worker_profile, preregistration)
        return 0
    if (root / OUT_DIR).exists() or (root / RESULT_PATH).exists() or (root / REPORT_PATH).exists():
        raise ValueError("R159 execution evidence already exists; refusing to overwrite")
    script = Path(__file__).resolve()
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(launch_worker, root, script, profile["profile_id"], preregistration): profile["profile_id"]
            for profile in protocol["profiles"]
        }
        for future in as_completed(futures):
            print(f"R159 worker complete: {future.result()}")
    result = aggregate(root, protocol_payload, contract, preregistration)
    print(json.dumps({
        "status": result["status"],
        "classification": result["summary"]["classification"],
        "mapping_class_counts": result["summary"]["mapping_class_counts"],
        "native_operation_order_hash_count": result["summary"]["native_operation_order_hash_count"],
        "native_average_error_bits_hash_count": result["summary"]["native_average_error_bits_hash_count"],
        "requirements_passed": result["requirements_passed"],
        "requirements_failed": result["requirements_failed"],
        "payload_hash": result["payload_hash"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
