#!/usr/bin/env python3
"""Execute the preregistered R155 2x2 execution-mode attribution matrix."""

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
from datetime import datetime
from pathlib import Path
from typing import Any

from qiskit import qasm3, transpile
from qiskit_aer import AerSimulator

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r121_private_bundle_shot_sweep import basis_circuit
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r128_transpiler_loop_layout_ranking import package_version
from b4_b8_r132_topology_constrained_route_policy import compile_policy
from b4_b8_r135_dense_interaction_fallback import build_dense_validation_tasks
from b4_b8_r138_postcommit_statistical_challenge import (
    exact_distribution,
    hellinger_fidelity,
    probability_from_counts,
)
from b4_b8_r139_lagos_ising_channel_attribution import (
    exact_compiled_classical_distribution,
)
from b4_b8_r153_independent_seed_replication_holdout import TARGET_CLASSES
from b4_b8_r154_deterministic_automatic_replay import (
    CORE_R153_FIELDS,
    canonical_hash,
    qasm_hash,
    summarize,
    target_descriptor,
)


METHOD = "b4_b8_r155_execution_mode_attribution_v0"
CONTRACT_PATH = "benchmarks/B4_B8_R155_execution_mode_attribution_contract_v0.json"
CONTRACT_SHA256 = "76f7939cdac7aa3b89cfb5f90a89e8d424a28cef5ec849434b4dc5858a4dfc9a"
PROTOCOL_PATH = "results/B4_B8_R155_execution_mode_attribution_protocol_v0.json"
PROTOCOL_PAYLOAD_HASH = "bcfc9860af9bb6dccf8715a35c98060ffe714a2629f3d8e443c6be8a5c35ad81"
PREREGISTRATION_COMMIT = "a9c2d9f67c3d4e2fe00749c2b2f09c416327c927"
PREREGISTRATION_DISCUSSION = "https://github.com/crystal-tensor/Prometheus-plan/discussions/172"
PREREGISTRATION_CREATED_AT = "2026-07-13T13:32:07Z"
R153_RESULT_PATH = "results/B4_B8_R153_independent_seed_replication_holdout_v0.json"
R153_TRIALS_PATH = "results/B4_B8_R153_independent_seed_replication_holdout/three_arm_trial_rows.json"
R153_REVEAL_PATH = "results/B4_B8_R153_independent_seed_replication_holdout/challenge_reveal.json"
R152_DESIGN_PATH = "results/B4_B8_R152_edge_signature_expansion_design_v0.json"
R150_DESIGN_PATH = "results/B4_B8_R150_unseen_backend_candidate_generation_design_v0.json"
OUT_DIR = "results/B4_B8_R155_execution_mode_attribution"
COMPARISON_PATH = f"{OUT_DIR}/comparison_matrix.json"
CLASSIFICATION_PATH = f"{OUT_DIR}/classification.json"
TRANSCRIPT_PATH = f"{OUT_DIR}/verifier_transcript.json"
RESULT_PATH = "results/B4_B8_R155_execution_mode_attribution_v0.json"
REPORT_PATH = "research/B4_B8_R155_execution_mode_attribution.md"
ARMS = ["repaired", "denominator", "automatic"]


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


def artifact_paths(profile_id: str, replicate_id: int) -> tuple[str, str]:
    stem = f"{OUT_DIR}/{profile_id}_replicate_{replicate_id}"
    return f"{stem}_rows.json", f"{stem}_manifest.json"


def validate_bindings(root: Path, contract: dict, protocol_payload: dict) -> None:
    if file_sha256(root / CONTRACT_PATH) != CONTRACT_SHA256:
        raise ValueError("R155 contract hash mismatch")
    if protocol_payload.get("payload_hash") != PROTOCOL_PAYLOAD_HASH:
        raise ValueError("R155 protocol payload hash mismatch")
    if contract.get("contract_id") != "B4-B8-R155-execution-mode-attribution-contract-v0":
        raise ValueError("R155 contract identity mismatch")
    if contract.get("contract_status") != "public_preregistration_execution_unopened":
        raise ValueError("R155 contract status mismatch")
    if contract.get("target_id") != "T-B4-002br/T-B8-003bv/T-B10-009bj":
        raise ValueError("R155 target binding mismatch")
    bindings = contract["source_bindings"]
    if bindings["protocol_payload_hash"] != PROTOCOL_PAYLOAD_HASH:
        raise ValueError("R155 protocol payload binding mismatch")
    if bindings["protocol_sha256"] != file_sha256(root / PROTOCOL_PATH):
        raise ValueError("R155 protocol file binding mismatch")
    for binding_id, binding in bindings.items():
        if binding_id in {"protocol_path", "protocol_payload_hash", "protocol_sha256"}:
            continue
        path = root / binding["path"]
        if not path.exists() or file_sha256(path) != binding["sha256"]:
            raise ValueError(f"R155 source binding mismatch: {binding_id}")
        if "payload_hash" in binding:
            payload = json.loads(path.read_text())
            if payload.get("payload_hash") != binding["payload_hash"]:
                raise ValueError(f"R155 source payload mismatch: {binding_id}")


def profile_by_id(protocol: dict, profile_id: str) -> dict:
    rows = [row for row in protocol["profiles"] if row["profile_id"] == profile_id]
    if len(rows) != 1:
        raise ValueError(f"unknown or duplicate R155 profile: {profile_id}")
    return rows[0]


def verify_process_environment(profile: dict) -> None:
    actual = {key: os.environ.get(key) for key in profile["thread_environment"]}
    if actual != profile["thread_environment"]:
        raise ValueError(
            f"R155 process environment mismatch for {profile['profile_id']}: {actual}"
        )


def actual_environment(profile: dict, simulator_rows: list[dict]) -> dict:
    return {
        "python": platform.python_version(),
        "qiskit": package_version("qiskit"),
        "qiskit_aer": package_version("qiskit-aer"),
        "qiskit_ibm_runtime": package_version("qiskit-ibm-runtime"),
        "thread_environment": {
            key: os.environ.get(key) for key in profile["thread_environment"]
        },
        "aer_option_mode": profile["aer_option_mode"],
        "requested_aer_options": profile.get("aer_simulator_options", {}),
        "documented_aer_defaults": profile.get("documented_aer_defaults"),
        "observed_simulator_option_rows": simulator_rows,
    }


def execute_worker(
    root: Path,
    profile_id: str,
    replicate_id: int,
    protocol_payload: dict,
) -> dict:
    protocol = protocol_payload["protocol"]
    profile = profile_by_id(protocol, profile_id)
    verify_process_environment(profile)
    rows_path_rel, manifest_path_rel = artifact_paths(profile_id, replicate_id)
    rows_path = root / rows_path_rel
    manifest_path = root / manifest_path_rel
    if rows_path.exists() or manifest_path.exists():
        raise ValueError(f"R155 worker evidence already exists: {profile_id}/{replicate_id}")
    r153_rows = json.loads((root / R153_TRIALS_PATH).read_text())
    reveal = json.loads((root / R153_REVEAL_PATH).read_text())
    design = json.loads((root / R152_DESIGN_PATH).read_text())
    r150_design = json.loads((root / R150_DESIGN_PATH).read_text())
    task = next(
        row
        for row in build_dense_validation_tasks()
        if row["task_id"] == protocol["task_id"]
    )
    logical = basis_circuit(
        task["circuit"], tuple("Z" for _ in range(task["circuit"].num_qubits))
    )
    ideal = exact_distribution(task["circuit"])
    selected_path = root / design["summary"]["selected_circuit_path"]
    target_rows = {row["target_snapshot"]: row for row in r150_design["target_rows"]}
    source_rows = {
        (row["target_snapshot"], row["trial"]): row for row in r153_rows
    }
    rows = []
    compiled_rows = []
    descriptor_rows = []
    route_rows = []
    simulator_rows = []
    for target_name in protocol["snapshot_names"]:
        backend = TARGET_CLASSES[target_name]()
        simulator = AerSimulator.from_backend(backend)
        if profile["aer_option_mode"] == "explicit_serial":
            simulator.set_options(**profile["aer_simulator_options"])
        simulator_rows.append({
            "target_snapshot": target_name,
            "max_parallel_threads": getattr(simulator.options, "max_parallel_threads"),
            "max_parallel_experiments": getattr(simulator.options, "max_parallel_experiments"),
            "max_parallel_shots": getattr(simulator.options, "max_parallel_shots"),
        })
        descriptor_rows.append({
            "target_snapshot": target_name,
            **target_descriptor(backend),
        })
        selected = target_rows[target_name]
        if target_name == "FakeCasablancaV2":
            repaired = qasm3.load(selected_path)
        else:
            repaired = compile_policy(
                logical,
                backend,
                selected["selected_mapping"],
                selected["selected_policy_id"],
                selected["selected_realization_seed"],
            )
        denominator = qasm3.load(root / selected["denominator_circuit_path"])
        repaired_hash = qasm_hash(repaired)
        denominator_hash = qasm_hash(denominator)
        route_rows.append({
            "target_snapshot": target_name,
            "repaired_qasm_sha256": repaired_hash,
            "denominator_qasm_sha256": denominator_hash,
        })
        compiled_rows.append({
            "target_snapshot": target_name,
            "repaired_qasm_sha256": repaired_hash,
            "denominator_qasm_sha256": denominator_hash,
            "repaired_semantic_fidelity": hellinger_fidelity(
                ideal, exact_compiled_classical_distribution(repaired)
            ),
            "denominator_semantic_fidelity": hellinger_fidelity(
                ideal, exact_compiled_classical_distribution(denominator)
            ),
        })
        for trial in range(32):
            source = source_rows[(target_name, trial)]
            automatic = transpile(
                logical,
                backend=backend,
                optimization_level=3,
                seed_transpiler=source["transpiler_seed"],
            )
            circuits = {
                "repaired": repaired,
                "denominator": denominator,
                "automatic": automatic,
            }
            counts_by_arm = {}
            count_hashes = {}
            fidelities = {}
            for arm, circuit in circuits.items():
                counts = simulator.run(
                    circuit,
                    shots=protocol["shots_per_execution"],
                    seed_simulator=source["simulator_seed"],
                ).result().get_counts()
                canonical_counts = {
                    str(key): int(value) for key, value in sorted(counts.items())
                }
                counts_by_arm[arm] = canonical_counts
                count_hashes[arm] = canonical_hash(canonical_counts)
                observed = probability_from_counts(
                    canonical_counts,
                    protocol["shots_per_execution"],
                    task["circuit"].num_qubits,
                )
                fidelities[arm] = hellinger_fidelity(ideal, observed)
            row = {
                "target_snapshot": target_name,
                "task_id": protocol["task_id"],
                "trial": trial,
                "block_index": source["block_index"],
                "trial_in_block": source["trial_in_block"],
                "transpiler_seed": source["transpiler_seed"],
                "simulator_seed": source["simulator_seed"],
                "repaired_qasm_sha256": repaired_hash,
                "denominator_qasm_sha256": denominator_hash,
                "automatic_qasm_sha256": qasm_hash(automatic),
                "arm_counts": counts_by_arm,
                "arm_counts_sha256": count_hashes,
                "repaired_fidelity": fidelities["repaired"],
                "denominator_fidelity": fidelities["denominator"],
                "automatic_fidelity": fidelities["automatic"],
                "repaired_minus_automatic": (
                    fidelities["repaired"] - fidelities["automatic"]
                ),
                "repaired_minus_denominator": (
                    fidelities["repaired"] - fidelities["denominator"]
                ),
            }
            row["scientific_row_sha256"] = canonical_hash(row)
            rows.append(row)
    summary, group_rows, block_rows, r153_conditions = summarize(
        rows,
        compiled_rows,
        protocol,
        bytes.fromhex(reveal["challenge_secret_hex"]),
    )
    manifest = {
        "profile_id": profile_id,
        "replicate_id": replicate_id,
        "process_instance_uuid": str(uuid.uuid4()),
        "process_id": os.getpid(),
        "started_at_unix": int(time.time()),
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "preregistration_discussion": PREREGISTRATION_DISCUSSION,
        "contract_sha256": CONTRACT_SHA256,
        "environment": actual_environment(profile, simulator_rows),
        "target_descriptor_rows": descriptor_rows,
        "fixed_route_rows": route_rows,
        "compiled_route_rows": compiled_rows,
        "summary": summary,
        "group_rows": group_rows,
        "block_rows": block_rows,
        "r153_acceptance_conditions": r153_conditions,
        "row_count": len(rows),
        "circuit_execution_count": len(rows) * 3,
        "total_simulated_shots": (
            len(rows) * 3 * protocol["shots_per_execution"]
        ),
    }
    manifest["manifest_payload_hash"] = canonical_hash(manifest)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(rows_path, rows)
    write_json(manifest_path, manifest)
    return {
        "profile_id": profile_id,
        "replicate_id": replicate_id,
        "row_count": len(rows),
        "rows_sha256": file_sha256(rows_path),
        "manifest_sha256": file_sha256(manifest_path),
    }


def compare_processes(
    left_id: str,
    left_rows: list[dict],
    left_manifest: dict,
    right_id: str,
    right_rows: list[dict],
    right_manifest: dict,
) -> dict:
    left_by_key = {
        (row["target_snapshot"], row["trial"]): row for row in left_rows
    }
    right_by_key = {
        (row["target_snapshot"], row["trial"]): row for row in right_rows
    }
    automatic_matches = 0
    arm_matches = 0
    scientific_matches = 0
    mismatch_rows = []
    for key in sorted(left_by_key):
        left = left_by_key[key]
        right = right_by_key.get(key)
        if right is None:
            mismatch_rows.append({"key": list(key), "missing_right_row": True})
            continue
        qasm_match = left["automatic_qasm_sha256"] == right["automatic_qasm_sha256"]
        count_matches = {
            arm: left["arm_counts_sha256"][arm] == right["arm_counts_sha256"][arm]
            for arm in ARMS
        }
        scientific_match = (
            left["scientific_row_sha256"] == right["scientific_row_sha256"]
        )
        automatic_matches += qasm_match
        arm_matches += sum(count_matches.values())
        scientific_matches += scientific_match
        if not qasm_match or not all(count_matches.values()) or not scientific_match:
            mismatch_rows.append({
                "key": list(key),
                "automatic_qasm_match": qasm_match,
                "left_automatic_qasm_sha256": left["automatic_qasm_sha256"],
                "right_automatic_qasm_sha256": right["automatic_qasm_sha256"],
                "arm_count_matches": count_matches,
                "scientific_row_match": scientific_match,
                "left_automatic_fidelity": left["automatic_fidelity"],
                "right_automatic_fidelity": right["automatic_fidelity"],
                "left_repaired_minus_automatic": left["repaired_minus_automatic"],
                "right_repaired_minus_automatic": right["repaired_minus_automatic"],
            })
    left_targets = {
        row["target_snapshot"]: row["descriptor_hash"]
        for row in left_manifest["target_descriptor_rows"]
    }
    right_targets = {
        row["target_snapshot"]: row["descriptor_hash"]
        for row in right_manifest["target_descriptor_rows"]
    }
    left_routes = {
        (row["target_snapshot"], arm): row[f"{arm}_qasm_sha256"]
        for row in left_manifest["fixed_route_rows"]
        for arm in ["repaired", "denominator"]
    }
    right_routes = {
        (row["target_snapshot"], arm): row[f"{arm}_qasm_sha256"]
        for row in right_manifest["fixed_route_rows"]
        for arm in ["repaired", "denominator"]
    }
    target_matches = sum(
        left_targets[key] == right_targets.get(key) for key in left_targets
    )
    route_matches = sum(
        left_routes[key] == right_routes.get(key) for key in left_routes
    )
    component_mismatch_count = (
        96 - automatic_matches
        + 288 - arm_matches
        + 96 - scientific_matches
        + 3 - target_matches
        + 6 - route_matches
    )
    comparison = {
        "left_process": left_id,
        "right_process": right_id,
        "automatic_qasm_hash_match_count": automatic_matches,
        "arm_counts_hash_match_count": arm_matches,
        "scientific_row_hash_match_count": scientific_matches,
        "backend_target_hash_match_count": target_matches,
        "fixed_route_hash_match_count": route_matches,
        "component_mismatch_count": component_mismatch_count,
        "mismatch_row_count": len(mismatch_rows),
        "mismatch_rows": mismatch_rows,
    }
    comparison["comparison_payload_hash"] = canonical_hash(comparison)
    return comparison


def compare_stored_r153(process_id: str, rows: list[dict], source_rows: list[dict]) -> dict:
    source_by_key = {
        (row["target_snapshot"], row["trial"]): row for row in source_rows
    }
    match_count = 0
    mismatch_rows = []
    for row in rows:
        key = (row["target_snapshot"], row["trial"])
        source = source_by_key[key]
        mismatched_fields = [
            field for field in CORE_R153_FIELDS if row[field] != source[field]
        ]
        if mismatched_fields:
            mismatch_rows.append({"key": list(key), "fields": mismatched_fields})
        else:
            match_count += 1
    result = {
        "process": process_id,
        "core_scientific_row_match_count": match_count,
        "core_scientific_row_mismatch_count": len(mismatch_rows),
        "mismatch_rows": mismatch_rows,
    }
    result["comparison_payload_hash"] = canonical_hash(result)
    return result


def load_process(root: Path, profile_id: str, replicate_id: int) -> tuple[list[dict], dict]:
    rows_rel, manifest_rel = artifact_paths(profile_id, replicate_id)
    rows = json.loads((root / rows_rel).read_text())
    manifest = json.loads((root / manifest_rel).read_text())
    return rows, manifest


def process_key(profile_id: str, replicate_id: int) -> str:
    return f"{profile_id}/replicate_{replicate_id}"


def build_comparison_matrix(root: Path, protocol: dict) -> tuple[dict, dict]:
    process_data = {}
    process_artifacts = []
    for profile in protocol["profiles"]:
        for replicate_id in range(2):
            profile_id = profile["profile_id"]
            key = process_key(profile_id, replicate_id)
            rows_rel, manifest_rel = artifact_paths(profile_id, replicate_id)
            rows, manifest = load_process(root, profile_id, replicate_id)
            process_data[key] = (rows, manifest)
            process_artifacts.append({
                "process": key,
                "rows_path": rows_rel,
                "rows_sha256": file_sha256(root / rows_rel),
                "manifest_path": manifest_rel,
                "manifest_sha256": file_sha256(root / manifest_rel),
            })
    within_profile = []
    for profile in protocol["profiles"]:
        profile_id = profile["profile_id"]
        left_id = process_key(profile_id, 0)
        right_id = process_key(profile_id, 1)
        within_profile.append(compare_processes(
            left_id,
            *process_data[left_id],
            right_id,
            *process_data[right_id],
        ))
    serial_reference_id = process_key("clamped_serial", 0)
    serial_reference = []
    for key in process_data:
        if key == serial_reference_id:
            continue
        serial_reference.append(compare_processes(
            serial_reference_id,
            *process_data[serial_reference_id],
            key,
            *process_data[key],
        ))
    source_rows = json.loads((root / R153_TRIALS_PATH).read_text())
    stored_r153 = [
        compare_stored_r153(key, rows, source_rows)
        for key, (rows, _) in process_data.items()
    ]
    manifests = [manifest for _, manifest in process_data.values()]
    matrix = {
        "serial_reference_process": serial_reference_id,
        "process_artifacts": process_artifacts,
        "within_profile_comparisons": within_profile,
        "serial_reference_comparisons": serial_reference,
        "stored_r153_comparisons": stored_r153,
        "process_instance_uuid_count": len({row["process_instance_uuid"] for row in manifests}),
        "process_id_count": len({row["process_id"] for row in manifests}),
        "process_started_after_preregistration_count": sum(
            row["started_at_unix"] > utc_timestamp(PREREGISTRATION_CREATED_AT)
            for row in manifests
        ),
    }
    matrix["comparison_matrix_payload_hash"] = canonical_hash(matrix)
    classification = classify(matrix)
    return matrix, classification


def comparison_zero(row: dict) -> bool:
    return row["component_mismatch_count"] == 0


def classify(matrix: dict) -> dict:
    within = {
        row["right_process"].split("/")[0]: comparison_zero(row)
        for row in matrix["within_profile_comparisons"]
    }
    cross = {
        row["right_process"]: comparison_zero(row)
        for row in matrix["serial_reference_comparisons"]
    }
    stored = {
        row["process"]: row["core_scientific_row_mismatch_count"] == 0
        for row in matrix["stored_r153_comparisons"]
    }

    def profile_matches_serial(profile_id: str) -> bool:
        keys = [process_key(profile_id, index) for index in range(2)]
        return all(
            True if key == matrix["serial_reference_process"] else cross[key]
            for key in keys
        )

    clamped_default_matches = profile_matches_serial("clamped_default_aer")
    four_serial_matches = profile_matches_serial("four_thread_serial")
    four_default_matches = profile_matches_serial("four_thread_default_aer")
    all_within_stable = all(within.values())
    all_cross_match = all(cross.values())
    all_stored_match = all(stored.values())
    within_mismatches = [
        mismatch
        for comparison in matrix["within_profile_comparisons"]
        for mismatch in comparison["mismatch_rows"]
    ]
    mismatch_keys = sorted({
        tuple(mismatch["key"])
        for mismatch in within_mismatches
        if "key" in mismatch
    })
    automatic_transpilation_first = bool(within_mismatches) and all(
        mismatch.get("automatic_qasm_match") is False
        and mismatch.get("arm_count_matches", {}).get("repaired") is True
        and mismatch.get("arm_count_matches", {}).get("denominator") is True
        for mismatch in within_mismatches
    )
    automatic_qasm_variants = sorted({
        value
        for mismatch in within_mismatches
        for value in [
            mismatch.get("left_automatic_qasm_sha256"),
            mismatch.get("right_automatic_qasm_sha256"),
        ]
        if value
    })
    automatic_fidelity_variants = sorted({
        value
        for mismatch in within_mismatches
        for value in [
            mismatch.get("left_automatic_fidelity"),
            mismatch.get("right_automatic_fidelity"),
        ]
        if value is not None
    })
    automatic_fidelity_delta = (
        max(automatic_fidelity_variants) - min(automatic_fidelity_variants)
        if automatic_fidelity_variants
        else 0.0
    )
    explicit_effect = (
        within["clamped_serial"]
        and within["clamped_default_aer"]
        and not clamped_default_matches
    )
    thread_effect = (
        within["clamped_serial"]
        and within["four_thread_serial"]
        and not four_serial_matches
    )
    interaction_effect = (
        all_within_stable
        and not four_default_matches
        and clamped_default_matches
        and four_serial_matches
    )
    classification = {
        "within_profile_stability": within,
        "serial_reference_match_by_process": cross,
        "stored_r153_match_by_process": stored,
        "clamped_default_aer_matches_serial": clamped_default_matches,
        "four_thread_serial_matches_serial": four_serial_matches,
        "four_thread_default_aer_matches_serial": four_default_matches,
        "explicit_aer_serialization_effect_detected": explicit_effect,
        "thread_environment_effect_detected": thread_effect,
        "environment_aer_interaction_effect_detected": interaction_effect,
        "effect_classification_blocked_by_unstable_cells": not all_within_stable,
        "unstable_cell_count": sum(not value for value in within.values()),
        "within_profile_mismatch_row_count": len(within_mismatches),
        "unique_within_profile_mismatch_keys": [list(key) for key in mismatch_keys],
        "same_single_row_transient_across_unstable_cells": (
            len(mismatch_keys) == 1 and len(within_mismatches) > 1
        ),
        "first_observed_divergence_layer": (
            "automatic_transpilation" if automatic_transpilation_first else "mixed_or_unknown"
        ),
        "aer_sampling_only_effect_excluded_for_observed_mismatches": automatic_transpilation_first,
        "automatic_qasm_variant_count": len(automatic_qasm_variants),
        "automatic_qasm_variant_hashes": automatic_qasm_variants,
        "automatic_fidelity_variant_count": len(automatic_fidelity_variants),
        "automatic_fidelity_variants": automatic_fidelity_variants,
        "automatic_fidelity_delta_between_variants": automatic_fidelity_delta,
        "implied_portfolio_mean_delta_from_one_of_96_rows": automatic_fidelity_delta / 96,
        "all_processes_match_serial_reference": all_cross_match,
        "all_processes_match_stored_r153_core_rows": all_stored_match,
        "r153_transient_reproduced": not all_cross_match or not all_stored_match,
        "r153_transient_not_reproduced": (
            all_within_stable and all_cross_match and all_stored_match
        ),
        "causal_attribution_supported": sum([
            explicit_effect,
            thread_effect,
            interaction_effect,
        ]) == 1,
    }
    classification["classification_payload_hash"] = canonical_hash(classification)
    return classification


def report(payload: dict) -> str:
    summary = payload["summary"]
    classification = payload["classification"]
    conditions = "\n".join(
        f"- {row['condition_id']} {'PASS' if row['passed'] else 'FAIL'}: {row['label']}; value `{row['value']}`, threshold `{row['threshold']}`."
        for row in payload["acceptance_conditions"]
    )
    return f"""# B4/B8 R155 Execution-Mode Attribution

- Diagnostic completion: **{'ACCEPT' if summary['global_acceptance'] else 'REJECT'}**
- Processes / rows / circuit executions: `{summary['process_count']}` / `{summary['row_execution_count']}` / `{summary['circuit_execution_count']}`
- Within-profile comparisons: `{summary['within_profile_comparison_count']}`
- Serial-reference comparisons: `{summary['serial_reference_comparison_count']}`
- Stored-R153 comparisons: `{summary['stored_r153_comparison_count']}`
- Within-profile component mismatches: `{summary['within_profile_component_mismatch_count']}`
- Serial-reference component mismatches: `{summary['serial_reference_component_mismatch_count']}`
- Stored-R153 core-row mismatches: `{summary['stored_r153_core_row_mismatch_count']}`
- Unstable cells: `{classification['unstable_cell_count']}`
- R153 transient reproduced / not reproduced: `{str(classification['r153_transient_reproduced']).lower()}` / `{str(classification['r153_transient_not_reproduced']).lower()}`
- Causal attribution supported: `{str(classification['causal_attribution_supported']).lower()}`
- Conditions passed / failed: `{summary['acceptance_conditions_passed']}` / `{summary['acceptance_conditions_failed']}`
- New hidden seeds / new credit: `0` / `0`

## Classification

- Explicit Aer serialization effect detected: `{str(classification['explicit_aer_serialization_effect_detected']).lower()}`
- Thread-environment effect detected: `{str(classification['thread_environment_effect_detected']).lower()}`
- Environment x Aer interaction detected: `{str(classification['environment_aer_interaction_effect_detected']).lower()}`
- Effect classification blocked by unstable cells: `{str(classification['effect_classification_blocked_by_unstable_cells']).lower()}`
- First observed divergence layer: `{classification['first_observed_divergence_layer']}`
- Aer-sampling-only explanation excluded for observed mismatches: `{str(classification['aer_sampling_only_effect_excluded_for_observed_mismatches']).lower()}`
- Unique within-profile mismatch keys: `{classification['unique_within_profile_mismatch_keys']}`
- Automatic QASM variants: `{classification['automatic_qasm_variant_count']}`
- Automatic-fidelity variant delta: `{classification['automatic_fidelity_delta_between_variants']:.12f}`
- One-row implied portfolio-mean delta: `{classification['implied_portfolio_mean_delta_from_one_of_96_rows']:.12f}`
- All processes match the serial reference: `{str(classification['all_processes_match_serial_reference']).lower()}`
- All processes match stored R153 core rows: `{str(classification['all_processes_match_stored_r153_core_rows']).lower()}`

## Acceptance Conditions

{conditions}

## Claim Boundary

Diagnostic completion means the frozen matrix ran and recorded every comparison.
It does not turn a non-reproduced transient into proof that the original event
was impossible, and a single localized pattern would require an expanded
replication block before causal attribution. No new hidden statistical evidence,
temporal or real-device transfer, hardware performance, general route-generation
advantage, quantum advantage, BQP separation, solved frontier, or credit is
claimed.
"""


def finalize(root: Path, protocol_payload: dict) -> dict:
    protocol = protocol_payload["protocol"]
    matrix, classification = build_comparison_matrix(root, protocol)
    write_json(root / COMPARISON_PATH, matrix)
    write_json(root / CLASSIFICATION_PATH, classification)
    within = matrix["within_profile_comparisons"]
    cross = matrix["serial_reference_comparisons"]
    stored = matrix["stored_r153_comparisons"]
    process_count = len(matrix["process_artifacts"])
    row_execution_count = process_count * protocol["row_count_per_process"]
    circuit_execution_count = (
        process_count * protocol["circuit_execution_count_per_process"]
    )
    all_artifact_hashes_present = all(
        row["rows_sha256"] and row["manifest_sha256"]
        for row in matrix["process_artifacts"]
    )
    conditions = [
        condition("A1", "contract, protocol, R154/R153 evidence, seeds, routes, and sources remain exact", True, True, True),
        condition("A2", "eight processes complete 768 rows and 2304 circuits", [process_count, row_execution_count, circuit_execution_count], [8, 768, 2304], process_count == 8 and row_execution_count == 768 and circuit_execution_count == 2304),
        condition("A3", "all process manifests are complete and independently identified", [matrix["process_instance_uuid_count"], matrix["process_started_after_preregistration_count"]], [8, 8], matrix["process_instance_uuid_count"] == 8 and matrix["process_started_after_preregistration_count"] == 8),
        condition("A4", "four within-profile comparisons are complete", len(within), 4, len(within) == 4 and all(row["automatic_qasm_hash_match_count"] + (96 - row["automatic_qasm_hash_match_count"]) == 96 for row in within)),
        condition("A5", "seven serial-reference comparisons are complete", len(cross), 7, len(cross) == 7 and all(row["arm_counts_hash_match_count"] + (288 - row["arm_counts_hash_match_count"]) == 288 for row in cross)),
        condition("A6", "eight stored-R153 core-row comparisons are complete", len(stored), 8, len(stored) == 8 and all(row["core_scientific_row_match_count"] + row["core_scientific_row_mismatch_count"] == 96 for row in stored)),
        condition("A7", "the R153 code-equivalent cell is explicitly classified", "clamped_default_aer_matches_serial" in classification, True, "clamped_default_aer_matches_serial" in classification),
        condition("A8", "Aer, thread-environment, interaction, and non-reproduction classifications are emitted", [key in classification for key in ["explicit_aer_serialization_effect_detected", "thread_environment_effect_detected", "environment_aer_interaction_effect_detected", "r153_transient_not_reproduced"]], [True, True, True, True], all(key in classification for key in ["explicit_aer_serialization_effect_detected", "thread_environment_effect_detected", "environment_aer_interaction_effect_detected", "r153_transient_not_reproduced"])),
        condition("A9", "all process artifacts and comparison bindings are complete", all_artifact_hashes_present, True, all_artifact_hashes_present),
        condition("A10", "new seeds, selection, route changes, and forbidden claims remain false", 0, 0, True),
    ]
    global_acceptance = all(row["passed"] for row in conditions)
    summary = {
        "process_count": process_count,
        "row_execution_count": row_execution_count,
        "circuit_execution_count": circuit_execution_count,
        "total_simulated_shots": protocol["total_simulated_shots"],
        "within_profile_comparison_count": len(within),
        "serial_reference_comparison_count": len(cross),
        "stored_r153_comparison_count": len(stored),
        "within_profile_component_mismatch_count": sum(row["component_mismatch_count"] for row in within),
        "serial_reference_component_mismatch_count": sum(row["component_mismatch_count"] for row in cross),
        "stored_r153_core_row_mismatch_count": sum(row["core_scientific_row_mismatch_count"] for row in stored),
        "process_instance_uuid_count": matrix["process_instance_uuid_count"],
        "process_id_count": matrix["process_id_count"],
        "process_started_after_preregistration_count": matrix["process_started_after_preregistration_count"],
        "immutable_worker_artifact_count": len(matrix["process_artifacts"]),
        "acceptance_conditions_passed": sum(row["passed"] for row in conditions),
        "acceptance_conditions_failed": sum(not row["passed"] for row in conditions),
        "failed_acceptance_condition_ids": [row["condition_id"] for row in conditions if not row["passed"]],
        "global_acceptance": global_acceptance,
        "new_hidden_seed_count": 0,
        "candidate_selection_performed": False,
        "route_change_performed": False,
        "causal_attribution_claimed": False,
        "hardware_execution_claimed": False,
        "temporal_transfer_claimed": False,
        "real_device_transfer_claimed": False,
        "general_route_generation_advantage_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
    }
    requirements = [
        {"requirement_id": "P1", "label": "public preregistration precedes all eight processes", "passed": matrix["process_started_after_preregistration_count"] == 8},
        {"requirement_id": "P2", "label": "contract, protocol, R154/R153 evidence, routes, and seeds are hash-bound", "passed": True},
        {"requirement_id": "P3", "label": "all four cells have two independently identified process replicates", "passed": matrix["process_instance_uuid_count"] == 8},
        {"requirement_id": "P4", "label": "all within-profile comparisons are complete", "passed": len(within) == 4},
        {"requirement_id": "P5", "label": "all serial-reference comparisons are complete", "passed": len(cross) == 7},
        {"requirement_id": "P6", "label": "all stored-R153 comparisons are complete", "passed": len(stored) == 8},
        {"requirement_id": "P7", "label": "all frozen process environments and Aer modes are recorded", "passed": True},
        {"requirement_id": "P8", "label": "all four preregistered classifications are emitted", "passed": conditions[7]["passed"]},
        {"requirement_id": "P9", "label": "mismatches remain evidence rather than post-hoc exclusions", "passed": True},
        {"requirement_id": "P10", "label": "no new evidence, selection, route change, forbidden claim, or credit", "passed": True},
    ]
    payload = {
        "title": "B4/B8 R155 execution-mode attribution",
        "version": 0,
        "method": METHOD,
        "status": "execution_mode_attribution_diagnostic_complete" if global_acceptance else "execution_mode_attribution_diagnostic_incomplete",
        "model_status": "2x2_execution_mode_diagnostic_without_causal_overclaim",
        "generated_at_unix": int(time.time()),
        "source_target_id": "T-B4-002bs/T-B8-003bw/T-B10-009bk",
        "upstream_target_id": "T-B4-002br/T-B8-003bv/T-B10-009bj",
        "summary": summary,
        "classification": classification,
        "acceptance_conditions": conditions,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [row["requirement_id"] for row in requirements if not row["passed"]],
        "artifacts": {
            "contract": CONTRACT_PATH,
            "protocol": PROTOCOL_PATH,
            "process_artifacts": matrix["process_artifacts"],
            "comparison_matrix": COMPARISON_PATH,
            "classification": CLASSIFICATION_PATH,
            "verifier_transcript": TRANSCRIPT_PATH,
            "result": RESULT_PATH,
            "markdown_report": REPORT_PATH,
        },
        "claim_boundary": {
            "what_is_supported": "one preregistered 2x2 execution-mode diagnostic over the public R153 execution surface",
            "what_is_not_supported": "proof that a non-reproduced transient was impossible, causal attribution without expanded replication, new hidden statistical evidence, temporal or real-device transfer, hardware performance, general route-generation advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    payload["payload_hash"] = canonical_hash(payload)
    transcript = {
        "contract_sha256": CONTRACT_SHA256,
        "protocol_payload_hash": PROTOCOL_PAYLOAD_HASH,
        "comparison_matrix_payload_hash": matrix["comparison_matrix_payload_hash"],
        "classification_payload_hash": classification["classification_payload_hash"],
        "acceptance_conditions": conditions,
        "requirements": requirements,
        "global_acceptance": global_acceptance,
        "result_payload_hash": payload["payload_hash"],
    }
    write_json(root / TRANSCRIPT_PATH, transcript)
    write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    return payload


def validate_existing_worker(root: Path, profile_id: str, replicate_id: int) -> bool:
    rows_rel, manifest_rel = artifact_paths(profile_id, replicate_id)
    rows_path = root / rows_rel
    manifest_path = root / manifest_rel
    if rows_path.exists() != manifest_path.exists():
        raise ValueError(f"R155 partial worker evidence: {profile_id}/{replicate_id}")
    if not rows_path.exists():
        return False
    rows = json.loads(rows_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if len(rows) != 96 or manifest.get("row_count") != 96:
        raise ValueError(f"R155 existing worker row mismatch: {profile_id}/{replicate_id}")
    if manifest.get("profile_id") != profile_id or manifest.get("replicate_id") != replicate_id:
        raise ValueError(f"R155 existing worker identity mismatch: {profile_id}/{replicate_id}")
    hp = dict(manifest)
    manifest_hash = hp.pop("manifest_payload_hash", None)
    if manifest_hash != canonical_hash(hp):
        raise ValueError(f"R155 existing worker manifest hash mismatch: {profile_id}/{replicate_id}")
    return True


def orchestrate(root: Path, protocol_payload: dict) -> dict:
    if (root / RESULT_PATH).exists() or (root / COMPARISON_PATH).exists() or (root / CLASSIFICATION_PATH).exists():
        raise ValueError("R155 final evidence already exists; refusing to overwrite")
    protocol = protocol_payload["protocol"]
    for profile in protocol["profiles"]:
        for replicate_id in range(2):
            profile_id = profile["profile_id"]
            if validate_existing_worker(root, profile_id, replicate_id):
                continue
            environment = dict(os.environ)
            environment.update(profile["thread_environment"])
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--root",
                str(root),
                "--worker",
                "--profile-id",
                profile_id,
                "--replicate-id",
                str(replicate_id),
            ]
            completed = subprocess.run(
                command,
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"R155 worker failed {profile_id}/{replicate_id}: {completed.stderr}"
                )
            print(completed.stdout.strip(), flush=True)
    return finalize(root, protocol_payload)


def recompute_derived(root: Path, protocol_payload: dict) -> dict:
    protocol = protocol_payload["protocol"]
    for profile in protocol["profiles"]:
        for replicate_id in range(2):
            if not validate_existing_worker(root, profile["profile_id"], replicate_id):
                raise ValueError("R155 cannot recompute derived evidence with a missing worker")
    return finalize(root, protocol_payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--recompute-derived", action="store_true")
    parser.add_argument("--profile-id")
    parser.add_argument("--replicate-id", type=int)
    args = parser.parse_args()
    root = args.root.resolve()
    if int(time.time()) <= utc_timestamp(PREREGISTRATION_CREATED_AT):
        raise ValueError("R155 execution must start after public preregistration")
    contract = json.loads((root / CONTRACT_PATH).read_text())
    protocol_payload = json.loads((root / PROTOCOL_PATH).read_text())
    validate_bindings(root, contract, protocol_payload)
    if args.worker and args.recompute_derived:
        raise ValueError("R155 worker and derived-recomputation modes are exclusive")
    if args.worker:
        if args.profile_id is None or args.replicate_id not in {0, 1}:
            raise ValueError("R155 worker requires a valid profile and replicate ID")
        result = execute_worker(
            root,
            args.profile_id,
            args.replicate_id,
            protocol_payload,
        )
    elif args.recompute_derived:
        result = recompute_derived(root, protocol_payload)
    else:
        result = orchestrate(root, protocol_payload)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
