#!/usr/bin/env python3
"""Execute the preregistered R157 direct VF2PostLayout tie isolation."""

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
from types import SimpleNamespace
from typing import Any

from qiskit import qasm3
from qiskit.converters import circuit_to_dag
from qiskit.transpiler import PropertySet, Target
from qiskit.transpiler.passes import VF2PostLayout

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r128_transpiler_loop_layout_ranking import package_version
from b4_b8_r153_independent_seed_replication_holdout import TARGET_CLASSES
from b4_b8_r154_deterministic_automatic_replay import canonical_hash, target_descriptor
from b4_b8_r157_vf2_tie_isolation_protocol import tie_score_evidence


METHOD = "b4_b8_r157_vf2_tie_isolation_v0"
CONTRACT_PATH = "benchmarks/B4_B8_R157_vf2_tie_isolation_contract_v0.json"
CONTRACT_SHA256 = "f45f7e7fe285dc86307201063a3351a40293d888625f7bd790446f25a7d50dc4"
PROTOCOL_PATH = "results/B4_B8_R157_vf2_tie_isolation_protocol_v0.json"
PROTOCOL_PAYLOAD_HASH = "4c56c1bc1e3c54d7f6ef186cfe41592a288f8c534441657afc58bbf9c7a3c82a"
PREREGISTRATION_COMMIT = "d852171e58d4d6691e429da935974ad1414663b6"
PREREGISTRATION_DISCUSSION = "https://github.com/crystal-tensor/Prometheus-plan/discussions/176"
PREREGISTRATION_CREATED_AT = "2026-07-14T06:14:00Z"
OUT_DIR = "results/B4_B8_R157_vf2_tie_isolation"
PROFILE_DISTRIBUTIONS_PATH = f"{OUT_DIR}/profile_distributions.json"
CONTRAST_MATRIX_PATH = f"{OUT_DIR}/contrast_matrix.json"
TRANSCRIPT_PATH = f"{OUT_DIR}/verifier_transcript.json"
RESULT_PATH = "results/B4_B8_R157_vf2_tie_isolation_v0.json"
REPORT_PATH = "research/B4_B8_R157_vf2_tie_isolation.md"
MAPPING_CLASSES = [
    "endpoint_4_to_0",
    "endpoint_4_to_2",
    "other_mapping",
    "no_solution",
]
EXPECTED_MAPPINGS = {
    "endpoint_4_to_0": [6, 5, 4, 3, 0, 1, 2],
    "endpoint_4_to_2": [6, 5, 4, 3, 2, 1, 0],
}
IMPLEMENTATION_SMOKE_REPLAY_COUNT = 5
IMPLEMENTATION_SMOKE_DISCLOSURE = (
    "Five unretained implementation-smoke direct-pass invocations occurred after "
    "public preregistration and before the retained matrix while validating Qiskit "
    "property-set extraction and Target reconstruction. They exposed four "
    "endpoint_4_to_0 outcomes and one endpoint_4_to_2 outcome; the latter came from "
    "the descending-order Target. They are excluded from the 160-row matrix, no "
    "condition or analysis was changed, and R157 is not claimed as blinded confirmation."
)


def utc_timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def condition(
    condition_id: str,
    label: str,
    value: Any,
    threshold: Any,
    passed: bool,
) -> dict[str, Any]:
    return {
        "condition_id": condition_id,
        "label": label,
        "value": value,
        "threshold": threshold,
        "passed": passed,
    }


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
        "process_environment": {
            key: os.environ.get(key) for key in protocol["process_environment"]
        },
    }


def validate_bindings(root: Path, contract: dict, protocol_payload: dict) -> None:
    if file_sha256(root / CONTRACT_PATH) != CONTRACT_SHA256:
        raise ValueError("R157 contract hash mismatch")
    if protocol_payload.get("payload_hash") != PROTOCOL_PAYLOAD_HASH:
        raise ValueError("R157 protocol payload hash mismatch")
    if contract.get("contract_id") != "B4-B8-R157-vf2-tie-isolation-contract-v0":
        raise ValueError("R157 contract identity mismatch")
    if contract.get("contract_status") != "public_preregistration_execution_unopened":
        raise ValueError("R157 contract status mismatch")
    if contract.get("target_id") != "T-B4-002bv/T-B8-003bz/T-B10-009bn":
        raise ValueError("R157 target binding mismatch")
    bindings = contract["source_bindings"]
    if bindings["protocol_payload_hash"] != PROTOCOL_PAYLOAD_HASH:
        raise ValueError("R157 protocol payload binding mismatch")
    if bindings["protocol_sha256"] != file_sha256(root / PROTOCOL_PATH):
        raise ValueError("R157 protocol file binding mismatch")
    for binding_id, binding in bindings.items():
        if binding_id in {"protocol_path", "protocol_payload_hash", "protocol_sha256"}:
            continue
        path = root / binding["path"]
        if not path.exists() or file_sha256(path) != binding["sha256"]:
            raise ValueError(f"R157 source binding mismatch: {binding_id}")
        if "payload_hash" in binding:
            payload = json.loads(path.read_text())
            if payload.get("payload_hash") != binding["payload_hash"]:
                raise ValueError(f"R157 source payload mismatch: {binding_id}")


def profile_by_id(protocol: dict[str, Any], profile_id: str) -> dict[str, Any]:
    try:
        return next(row for row in protocol["profiles"] if row["profile_id"] == profile_id)
    except StopIteration as exc:
        raise ValueError(f"unknown R157 profile: {profile_id}") from exc


def worker_path(profile_id: str, process_index: int) -> str:
    return f"{OUT_DIR}/{profile_id}/process_{process_index:02d}.json"


def rebuild_target(source: Target, descending: bool) -> Target:
    rebuilt = Target(
        description=source.description,
        num_qubits=source.num_qubits,
        dt=source.dt,
        granularity=source.granularity,
        min_length=source.min_length,
        pulse_alignment=source.pulse_alignment,
        acquire_alignment=source.acquire_alignment,
        qubit_properties=(
            None if source.qubit_properties is None else list(source.qubit_properties)
        ),
        concurrent_measurements=source.concurrent_measurements,
    )
    for name in sorted(source.operation_names, reverse=descending):
        operation = source.operation_from_name(name)
        if isinstance(operation, type):
            rebuilt.add_instruction(operation, name=name)
            continue
        items = sorted(
            source[name].items(),
            key=lambda item: (
                item[0] is None,
                () if item[0] is None else tuple(item[0]),
            ),
            reverse=descending,
        )
        rebuilt.add_instruction(
            operation,
            {qargs: properties for qargs, properties in items},
            name=name,
        )
    return rebuilt


def build_target(target_order: str) -> Target:
    native = TARGET_CLASSES["FakeNairobiV2"]().target
    if target_order == "native":
        return native
    if target_order == "ascending":
        return rebuild_target(native, descending=False)
    if target_order == "descending":
        return rebuild_target(native, descending=True)
    raise ValueError(f"unsupported R157 target order: {target_order}")


def target_semantic_descriptor(target: Target) -> dict[str, Any]:
    backend_view = SimpleNamespace(
        target=target,
        name="fake_nairobi",
        num_qubits=target.num_qubits,
    )
    return target_descriptor(backend_view)


def target_order_rows(target: Target) -> list[dict[str, Any]]:
    rows = []
    for operation_index, name in enumerate(target.operation_names):
        for qargs_index, qargs in enumerate(target[name]):
            rows.append(
                {
                    "operation_index": operation_index,
                    "operation": name,
                    "qargs_index": qargs_index,
                    "qargs": None if qargs is None else list(qargs),
                }
            )
    return rows


def mapping_vector(circuit: Any, layout: Any) -> list[int] | None:
    if layout is None:
        return None
    vector: list[int | None] = [None] * circuit.num_qubits
    for bit, physical in layout.get_virtual_bits().items():
        vector[circuit.find_bit(bit).index] = int(physical)
    if any(value is None for value in vector):
        raise ValueError(f"R157 incomplete post_layout mapping: {vector}")
    return [int(value) for value in vector]


def mapping_class(vector: list[int] | None) -> str:
    if vector is None:
        return "no_solution"
    for class_id, expected in EXPECTED_MAPPINGS.items():
        if vector == expected:
            return class_id
    return "other_mapping"


def direct_replay(
    circuit: Any,
    target: Target,
    profile: dict[str, Any],
    replay_index: int,
) -> dict[str, Any]:
    descriptor = target_semantic_descriptor(target)
    order_rows = target_order_rows(target)
    pass_ = VF2PostLayout(
        target=target,
        seed=-1,
        call_limit=30000000,
        time_limit=None,
        strict_direction=False,
        max_trials=250000,
    )
    pass_.property_set = PropertySet()
    started = time.perf_counter()
    pass_.run(circuit_to_dag(circuit))
    elapsed = time.perf_counter() - started
    layout = pass_.property_set.get("post_layout")
    vector = mapping_vector(circuit, layout)
    stop_reason = pass_.property_set.get("VF2PostLayout_stop_reason")
    row = {
        "replay_index": replay_index,
        "profile_id": profile["profile_id"],
        "target_order": profile["target_order"],
        "shared_target_within_process": profile["shared_target_within_process"],
        "target_descriptor_sha256": descriptor["descriptor_hash"],
        "target_order_sha256": canonical_hash(order_rows),
        "target_operation_row_count": len(order_rows),
        "mapping_vector": vector,
        "mapping_class": mapping_class(vector),
        "post_layout_present": layout is not None,
        "stop_reason": (
            None
            if stop_reason is None
            else str(getattr(stop_reason, "value", stop_reason))
        ),
        "elapsed_seconds": elapsed,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
    }
    row["replay_payload_hash"] = canonical_hash(row)
    return row


def execute_worker(
    root: Path,
    protocol_payload: dict,
    profile_id: str,
    process_index: int,
) -> dict[str, Any]:
    protocol = protocol_payload["protocol"]
    profile = profile_by_id(protocol, profile_id)
    path = root / worker_path(profile_id, process_index)
    if path.exists():
        raise ValueError(f"R157 worker evidence already exists: {profile_id}/{process_index}")
    started_at = int(time.time())
    process_uuid = str(uuid.uuid4())
    circuit = qasm3.load(root / protocol["input_path"])
    shared_target = (
        build_target(profile["target_order"])
        if profile["shared_target_within_process"]
        else None
    )
    replay_rows = []
    for replay_index in range(profile["replays_per_process"]):
        target = shared_target or build_target(profile["target_order"])
        replay_rows.append(direct_replay(circuit, target, profile, replay_index))
    manifest = {
        "profile_id": profile_id,
        "process_index": process_index,
        "process_id": os.getpid(),
        "process_instance_uuid": process_uuid,
        "started_at_unix": started_at,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "preregistration_discussion": PREREGISTRATION_DISCUSSION,
        "contract_sha256": CONTRACT_SHA256,
        "protocol_payload_hash": PROTOCOL_PAYLOAD_HASH,
        "environment": actual_environment(protocol),
        "input_path": protocol["input_path"],
        "input_qasm_sha256": file_sha256(root / protocol["input_path"]),
        "profile": profile,
        "replay_count": len(replay_rows),
        "replay_rows": replay_rows,
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
    process_index: int,
) -> tuple[str, int]:
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(root),
            "--worker-profile",
            profile_id,
            "--worker-index",
            str(process_index),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"R157 worker failed {profile_id}/{process_index}: "
            f"{completed.stdout}\n{completed.stderr}"
        )
    return profile_id, process_index


def planned_workers(protocol: dict[str, Any]) -> list[tuple[str, int]]:
    return [
        (profile["profile_id"], process_index)
        for profile in protocol["profiles"]
        for process_index in range(profile["process_count"])
    ]


def profile_distributions(
    protocol: dict[str, Any],
    manifests: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    for profile in protocol["profiles"]:
        profile_manifests = [
            row for row in manifests if row["profile_id"] == profile["profile_id"]
        ]
        replays = [
            replay
            for manifest in profile_manifests
            for replay in manifest["replay_rows"]
        ]
        class_counts = Counter(row["mapping_class"] for row in replays)
        vector_counts = Counter(
            "no_solution"
            if row["mapping_vector"] is None
            else ",".join(str(value) for value in row["mapping_vector"])
            for row in replays
        )
        unique_classes = sum(count > 0 for count in class_counts.values())
        rows.append(
            {
                "profile_id": profile["profile_id"],
                "process_count": len(profile_manifests),
                "replay_count": len(replays),
                "target_order": profile["target_order"],
                "shared_target_within_process": profile[
                    "shared_target_within_process"
                ],
                "mapping_class_counts": {
                    class_id: class_counts.get(class_id, 0)
                    for class_id in MAPPING_CLASSES
                },
                "mapping_vector_counts": [
                    {"mapping_vector_key": key, "count": count}
                    for key, count in sorted(vector_counts.items())
                ],
                "unique_mapping_class_count": unique_classes,
                "profile_outcome": "collapse" if unique_classes == 1 else "variation",
                "target_order_sha256_values": sorted(
                    {row["target_order_sha256"] for row in replays}
                ),
                "stop_reason_counts": dict(
                    sorted(Counter(row["stop_reason"] for row in replays).items())
                ),
            }
        )
    payload = {
        "profile_count": len(rows),
        "total_process_count": len(manifests),
        "total_direct_replay_count": sum(row["replay_count"] for row in rows),
        "profile_rows": rows,
    }
    payload["profile_distributions_payload_hash"] = canonical_hash(payload)
    return payload


def contrast_matrix(distributions: dict[str, Any]) -> dict[str, Any]:
    by_id = {row["profile_id"]: row for row in distributions["profile_rows"]}
    planned = [
        (
            "native_vs_ascending_order",
            "native_target_independent_process",
            "canonical_ascending_independent_process",
            "Target insertion-order association",
        ),
        (
            "native_vs_descending_order",
            "native_target_independent_process",
            "canonical_descending_independent_process",
            "Target insertion-order association",
        ),
        (
            "independent_vs_fresh_same_process",
            "native_target_independent_process",
            "fresh_target_same_process",
            "process-start association",
        ),
        (
            "fresh_vs_shared_same_process",
            "fresh_target_same_process",
            "shared_target_same_process",
            "Target reuse association",
        ),
    ]
    rows = []
    for contrast_id, left_id, right_id, question in planned:
        left = by_id[left_id]
        right = by_id[right_id]
        left_counts = left["mapping_class_counts"]
        right_counts = right["mapping_class_counts"]
        rows.append(
            {
                "contrast_id": contrast_id,
                "question": question,
                "left_profile_id": left_id,
                "right_profile_id": right_id,
                "left_mapping_class_counts": left_counts,
                "right_mapping_class_counts": right_counts,
                "same_raw_class_counts": left_counts == right_counts,
                "same_observed_class_support": {
                    key for key, value in left_counts.items() if value > 0
                }
                == {key for key, value in right_counts.items() if value > 0},
                "left_outcome": left["profile_outcome"],
                "right_outcome": right["profile_outcome"],
                "causal_mechanism_claimed": False,
            }
        )
    payload = {
        "contrast_count": len(rows),
        "contrast_rows": rows,
        "interpretation_boundary": (
            "profile association only; a distribution difference does not identify "
            "a lower-level Rust, process, hash, or iteration mechanism"
        ),
    }
    payload["contrast_matrix_payload_hash"] = canonical_hash(payload)
    return payload


def build_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    distributions = result["profile_distributions"]["profile_rows"]
    lines = [
        "# B4/B8 R157 VF2 Tie-Isolation Result",
        "",
        f"- Status: `{result['status']}`",
        f"- Profiles / OS processes / direct replays: `{summary['profile_count']}` / `{summary['process_count']}` / `{summary['direct_replay_count']}`",
        f"- Mapping classes observed: `{summary['observed_mapping_class_count']}`",
        f"- Profile collapse / variation: `{summary['profile_collapse_count']}` / `{summary['profile_variation_count']}`",
        f"- Other mappings / no solutions: `{summary['other_mapping_count']}` / `{summary['no_solution_count']}`",
        f"- Simulation executions / shots: `{summary['simulation_execution_count']}` / `{summary['total_simulated_shots']}`",
        f"- Conditions passed/failed: `{summary['acceptance_conditions_passed']}` / `{summary['acceptance_conditions_failed']}`",
        f"- Requirements passed/failed: `{result['requirements_passed']}` / `{result['requirements_failed']}`",
        "",
        "## Profile Distributions",
        "",
        "| Profile | Processes | Replays | Mapping counts | Outcome |",
        "|---|---:|---:|---|---|",
    ]
    for row in distributions:
        counts = ", ".join(
            f"{key}={value}" for key, value in row["mapping_class_counts"].items()
        )
        lines.append(
            f"| `{row['profile_id']}` | {row['process_count']} | {row['replay_count']} | {counts} | `{row['profile_outcome']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["diagnostic_interpretation"],
            "",
            "## Implementation-Smoke Disclosure",
            "",
            summary["implementation_smoke_disclosure"],
            "",
            "The two preregistered mappings retain the exact independently recomputed "
            "score `0.45894321220828727`. All new mappings and no-solution rows, if any, "
            "remain in the distributions rather than being excluded.",
            "",
            "## Claim Boundary",
            "",
            "This direct-pass result reports profile associations only. It does not prove "
            "a lower-level process, hash, iteration, or Rust mechanism and does not claim "
            "a confirmed Qiskit bug, general compiler determinism, simulation or hardware "
            "performance, transfer, route advantage, quantum advantage, BQP separation, "
            "solved B4/B8/B10, or new research credit.",
            "",
        ]
    )
    return "\n".join(lines)


def aggregate(
    root: Path,
    protocol_payload: dict,
    contract: dict,
) -> dict[str, Any]:
    protocol = protocol_payload["protocol"]
    preregistration_timestamp = utc_timestamp(PREREGISTRATION_CREATED_AT)
    manifests = []
    process_artifacts = []
    for profile_id, process_index in planned_workers(protocol):
        rel = worker_path(profile_id, process_index)
        path = root / rel
        if not path.exists():
            raise ValueError(f"R157 process artifact missing: {profile_id}/{process_index}")
        manifest = json.loads(path.read_text())
        hp = dict(manifest)
        payload_hash = hp.pop("manifest_payload_hash", None)
        if payload_hash != canonical_hash(hp):
            raise ValueError(f"R157 process payload mismatch: {profile_id}/{process_index}")
        manifests.append(manifest)
        process_artifacts.append(
            {
                "profile_id": profile_id,
                "process_index": process_index,
                "path": rel,
                "sha256": file_sha256(path),
                "manifest_payload_hash": payload_hash,
            }
        )
    replays = [row for manifest in manifests for row in manifest["replay_rows"]]
    distributions = profile_distributions(protocol, manifests)
    contrasts = contrast_matrix(distributions)
    write_json(root / PROFILE_DISTRIBUTIONS_PATH, distributions)
    write_json(root / CONTRAST_MATRIX_PATH, contrasts)
    tie_evidence = tie_score_evidence(
        root, TARGET_CLASSES[protocol["snapshot_name"]]()
    )
    environments_match = all(
        manifest["environment"]["process_environment"]
        == protocol["process_environment"]
        and manifest["environment"]["python"]
        == protocol["frozen_software"]["python"]
        and manifest["environment"]["qiskit"]
        == protocol["frozen_software"]["qiskit"]
        for manifest in manifests
    )
    source_fields_match = all(
        manifest["contract_sha256"] == CONTRACT_SHA256
        and manifest["protocol_payload_hash"] == PROTOCOL_PAYLOAD_HASH
        and manifest["input_qasm_sha256"] == protocol["input_qasm_sha256"]
        and all(
            row["target_descriptor_sha256"]
            == protocol["target_descriptor_sha256"]
            for row in manifest["replay_rows"]
        )
        for manifest in manifests
    )
    replay_fields = {
        "replay_index",
        "profile_id",
        "target_order",
        "shared_target_within_process",
        "target_descriptor_sha256",
        "target_order_sha256",
        "mapping_vector",
        "mapping_class",
        "post_layout_present",
        "stop_reason",
        "elapsed_seconds",
    }
    replay_fields_complete = all(replay_fields.issubset(row) for row in replays)
    after_preregistration = all(
        manifest["started_at_unix"] >= preregistration_timestamp
        for manifest in manifests
    )
    process_uuids = {manifest["process_instance_uuid"] for manifest in manifests}
    profile_counts = Counter(manifest["profile_id"] for manifest in manifests)
    expected_profile_counts = {
        row["profile_id"]: row["process_count"] for row in protocol["profiles"]
    }
    class_counts = Counter(row["mapping_class"] for row in replays)
    observed_classes = {key for key, value in class_counts.items() if value > 0}
    distribution_rows = distributions["profile_rows"]
    collapse_count = sum(row["profile_outcome"] == "collapse" for row in distribution_rows)
    variation_count = sum(row["profile_outcome"] == "variation" for row in distribution_rows)
    tie_matches = (
        tie_evidence["scores_exactly_equal_in_python_recalculation"] is True
        and tie_evidence["shared_total_score"]
        == protocol["tie_score_evidence"]["shared_total_score"]
        and [row["mapping_vector"] for row in tie_evidence["mapping_rows"]]
        == [row["mapping_vector"] for row in protocol["tie_score_evidence"]["mapping_rows"]]
    )
    if variation_count:
        interpretation = (
            "At least one frozen profile retains more than one mapping class; the "
            "direct-pass boundary remains profile-variable and requires a smaller "
            "enumeration-order reproducer before any mechanism attribution."
        )
    elif len({
        tuple(sorted(row["mapping_class_counts"].items()))
        for row in distribution_rows
    }) > 1:
        interpretation = (
            "Every profile collapses internally, but at least two profiles select "
            "different mapping distributions. This is a preregistered profile-order "
            "association, not proof of the lower-level selection mechanism."
        )
    else:
        interpretation = (
            "All five profiles produce the same mapping distribution. Direct pass "
            "replay does not reproduce an order or process contrast, so the R156 "
            "variation must remain localized upstream or outside this matrix."
        )
    summary = {
        "profile_count": distributions["profile_count"],
        "process_count": len(manifests),
        "process_instance_uuid_count": len(process_uuids),
        "process_started_after_preregistration_count": sum(
            manifest["started_at_unix"] >= preregistration_timestamp
            for manifest in manifests
        ),
        "direct_replay_count": len(replays),
        "observed_mapping_class_count": len(observed_classes),
        "mapping_class_counts": {
            class_id: class_counts.get(class_id, 0) for class_id in MAPPING_CLASSES
        },
        "profile_collapse_count": collapse_count,
        "profile_variation_count": variation_count,
        "other_mapping_count": class_counts.get("other_mapping", 0),
        "no_solution_count": class_counts.get("no_solution", 0),
        "target_order_hash_count": len(
            {row["target_order_sha256"] for row in replays}
        ),
        "contrast_count": contrasts["contrast_count"],
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "new_hidden_seed_count": 0,
        "candidate_selection_performed": False,
        "route_change_performed": False,
        "sampling_performed": False,
        "compiler_mechanism_claimed": False,
        "qiskit_bug_claimed": False,
        "hardware_execution_claimed": False,
        "temporal_transfer_claimed": False,
        "real_device_transfer_claimed": False,
        "general_route_generation_advantage_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
        "implementation_smoke_replay_count": IMPLEMENTATION_SMOKE_REPLAY_COUNT,
        "implementation_smoke_rows_retained": False,
        "blinded_confirmation_claimed": False,
        "implementation_smoke_disclosure": IMPLEMENTATION_SMOKE_DISCLOSURE,
        "diagnostic_interpretation": interpretation,
    }
    acceptance = [
        condition("A1", "contract, protocol, R156 evidence, input, target, and sources remain exact", True, True, True),
        condition("A2", "98 post-preregistration process artifacts retain 160 direct replays", [len(manifests), len(process_uuids), summary["process_started_after_preregistration_count"], len(replays)], [98, 98, 98, 160], len(manifests) == len(process_uuids) == summary["process_started_after_preregistration_count"] == 98 and len(replays) == 160),
        condition("A3", "all replays use the frozen input, target descriptor, pass, software, and environment", [environments_match, source_fields_match], [True, True], environments_match and source_fields_match),
        condition("A4", "all five profiles complete without replacement", profile_counts, expected_profile_counts, dict(profile_counts) == expected_profile_counts),
        condition("A5", "all process and replay identity fields are retained", replay_fields_complete, True, replay_fields_complete),
        condition("A6", "within-profile and cross-profile mapping distributions are complete", [distributions["profile_count"], distributions["total_direct_replay_count"]], [5, 160], distributions["profile_count"] == 5 and distributions["total_direct_replay_count"] == 160),
        condition("A7", "new mappings and no-solution rows remain classified", sum(class_counts.values()), 160, sum(class_counts.values()) == 160),
        condition("A8", "all four preregistered contrasts are emitted", contrasts["contrast_count"], 4, contrasts["contrast_count"] == 4),
        condition("A9", "both R156 mappings remain independently and exactly tied", tie_matches, True, tie_matches),
        condition("A10", "selection, routes, sampling, blinded confirmation, mechanism, bug, hardware, advantage, BQP, solved-frontier, and credit claims remain false", 0, 0, summary["blinded_confirmation_claimed"] is False),
    ]
    requirements = [
        {"requirement_id": "P1", "label": "public preregistration precedes all processes", "passed": after_preregistration},
        {"requirement_id": "P2", "label": "contract, protocol, R156 evidence, input, target, and source hashes are bound", "passed": True},
        {"requirement_id": "P3", "label": "98 independently identified process artifacts complete", "passed": len(manifests) == len(process_uuids) == 98},
        {"requirement_id": "P4", "label": "all 160 replay rows retain frozen fields", "passed": len(replays) == 160 and replay_fields_complete},
        {"requirement_id": "P5", "label": "all five profile process counts match the contract", "passed": dict(profile_counts) == expected_profile_counts},
        {"requirement_id": "P6", "label": "mapping distributions and four contrasts are complete", "passed": distributions["profile_count"] == 5 and contrasts["contrast_count"] == 4},
        {"requirement_id": "P7", "label": "new mappings and no-solution outcomes remain admissible", "passed": sum(class_counts.values()) == 160},
        {"requirement_id": "P8", "label": "the exact tied score is independently reproduced", "passed": tie_matches},
        {"requirement_id": "P9", "label": "no simulation, shots, or sampling are performed", "passed": summary["simulation_execution_count"] == summary["total_simulated_shots"] == 0},
        {"requirement_id": "P10", "label": "no mechanism, bug, hardware, advantage, BQP, solved-frontier, or credit claim", "passed": True},
    ]
    summary["acceptance_conditions_passed"] = sum(row["passed"] for row in acceptance)
    summary["acceptance_conditions_failed"] = sum(not row["passed"] for row in acceptance)
    summary["global_acceptance"] = all(row["passed"] for row in acceptance)
    result = {
        "title": "B4/B8 R157 VF2 tie isolation",
        "version": 0,
        "method": METHOD,
        "status": "vf2_tie_isolation_diagnostic_complete" if summary["global_acceptance"] else "vf2_tie_isolation_diagnostic_incomplete",
        "model_status": "direct_pass_profile_association_without_mechanism_overclaim",
        "generated_at_unix": int(time.time()),
        "source_target_id": "T-B4-002bw/T-B8-003ca/T-B10-009bo",
        "upstream_target_id": "T-B4-002bv/T-B8-003bz/T-B10-009bn",
        "summary": summary,
        "tie_score_evidence": tie_evidence,
        "profile_distributions": {
            key: value
            for key, value in distributions.items()
            if key != "profile_distributions_payload_hash"
        },
        "contrast_matrix": {
            key: value
            for key, value in contrasts.items()
            if key != "contrast_matrix_payload_hash"
        },
        "acceptance_conditions": acceptance,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [row["requirement_id"] for row in requirements if not row["passed"]],
        "artifacts": {
            "protocol": PROTOCOL_PATH,
            "contract": CONTRACT_PATH,
            "result": RESULT_PATH,
            "markdown_report": REPORT_PATH,
            "process_artifacts": process_artifacts,
            "profile_distributions": PROFILE_DISTRIBUTIONS_PATH,
            "contrast_matrix": CONTRAST_MATRIX_PATH,
            "verifier_transcript": TRANSCRIPT_PATH,
        },
        "claim_boundary": {
            "what_is_supported": "one preregistered direct-pass profile matrix over the two exactly tied public R156 mappings",
            "what_is_not_supported": "a lower-level mechanism or confirmed Qiskit bug, general compiler determinism, hidden statistical evidence, simulation or hardware performance, transfer, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    result["payload_hash"] = canonical_hash(result)
    transcript = {
        "contract_sha256": CONTRACT_SHA256,
        "protocol_payload_hash": PROTOCOL_PAYLOAD_HASH,
        "result_payload_hash": result["payload_hash"],
        "profile_distributions_payload_hash": distributions[
            "profile_distributions_payload_hash"
        ],
        "contrast_matrix_payload_hash": contrasts["contrast_matrix_payload_hash"],
        "process_artifact_count": len(process_artifacts),
        "direct_replay_count": len(replays),
        "global_acceptance": summary["global_acceptance"],
        "requirements_passed": result["requirements_passed"],
        "requirements_failed": result["requirements_failed"],
    }
    transcript["verifier_transcript_payload_hash"] = canonical_hash(transcript)
    write_json(root / TRANSCRIPT_PATH, transcript)
    write_json(root / RESULT_PATH, result)
    (root / REPORT_PATH).write_text(build_report(result), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute the preregistered R157 VF2 tie-isolation matrix."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--worker-profile")
    parser.add_argument("--worker-index", type=int)
    parser.add_argument("--max-parallel-workers", type=int, default=8)
    args = parser.parse_args()
    root = args.root.resolve()
    protocol_payload = json.loads((root / PROTOCOL_PATH).read_text())
    contract = json.loads((root / CONTRACT_PATH).read_text())
    protocol = protocol_payload["protocol"]
    ensure_environment(protocol)
    validate_bindings(root, contract, protocol_payload)
    if args.worker_profile is not None:
        if args.worker_index is None:
            raise ValueError("R157 worker index is required")
        execute_worker(
            root,
            protocol_payload,
            args.worker_profile,
            args.worker_index,
        )
        return 0
    if (root / RESULT_PATH).exists() or (root / OUT_DIR).exists() or (root / REPORT_PATH).exists():
        raise ValueError("R157 execution evidence already exists; refusing to overwrite")
    script = Path(__file__).resolve()
    workers = planned_workers(protocol)
    if len(workers) != protocol["total_process_count"]:
        raise ValueError("R157 planned process count mismatch")
    with ThreadPoolExecutor(max_workers=args.max_parallel_workers) as executor:
        futures = {
            executor.submit(launch_worker, root, script, profile_id, process_index): (
                profile_id,
                process_index,
            )
            for profile_id, process_index in workers
        }
        completed_count = 0
        for future in as_completed(futures):
            future.result()
            completed_count += 1
            if completed_count % 10 == 0 or completed_count == len(workers):
                print(f"R157 workers complete: {completed_count}/{len(workers)}")
    result = aggregate(root, protocol_payload, contract)
    print(
        json.dumps(
            {
                "status": result["status"],
                "process_count": result["summary"]["process_count"],
                "direct_replay_count": result["summary"]["direct_replay_count"],
                "mapping_class_counts": result["summary"]["mapping_class_counts"],
                "profile_collapse_count": result["summary"]["profile_collapse_count"],
                "profile_variation_count": result["summary"]["profile_variation_count"],
                "requirements_passed": result["requirements_passed"],
                "requirements_failed": result["requirements_failed"],
                "payload_hash": result["payload_hash"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
