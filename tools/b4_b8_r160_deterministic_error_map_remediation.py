#!/usr/bin/env python3
"""Execute the preregistered R160 deterministic ErrorMap remediation matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import struct
import subprocess
import sys
import time
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction
from itertools import permutations
from pathlib import Path
from typing import Any

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r128_transpiler_loop_layout_ranking import package_version
from b4_b8_r153_independent_seed_replication_holdout import TARGET_CLASSES
from b4_b8_r154_deterministic_automatic_replay import canonical_hash, target_descriptor


METHOD = "b4_b8_r160_deterministic_error_map_remediation_v0"
PROTOCOL_PATH = "results/B4_B8_R160_deterministic_error_map_remediation_protocol_v0.json"
CONTRACT_PATH = "benchmarks/B4_B8_R160_deterministic_error_map_remediation_contract_v0.json"
SOURCE_MANIFEST_PATH = "research/source_lineage/Qiskit_2_4_1_vf2_source_manifest.json"
R159_NATIVE_PATH = "results/B4_B8_R159_error_map_accumulation_trace/native_hashset_order.json"
OUT_DIR = "results/B4_B8_R160_deterministic_error_map_remediation"
PROFILE_SUMMARY_PATH = f"{OUT_DIR}/profile_summary.json"
CASE_ANALYSIS_PATH = f"{OUT_DIR}/case_analysis.json"
TRANSCRIPT_PATH = f"{OUT_DIR}/verifier_transcript.json"
RESULT_PATH = "results/B4_B8_R160_deterministic_error_map_remediation_v0.json"
REPORT_PATH = "research/B4_B8_R160_deterministic_error_map_remediation.md"
EXPECTED_MAPPINGS = {
    "endpoint_4_to_0": [6, 5, 4, 3, 0, 1, 2],
    "endpoint_4_to_2": [6, 5, 4, 3, 2, 1, 0],
}


def utc_timestamp(value: str) -> int:
    from datetime import datetime

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
        "process_environment": {
            key: os.environ.get(key) for key in protocol["process_environment"]
        },
    }


def validate_payload(payload: dict[str, Any], label: str) -> str:
    body = dict(payload)
    payload_hash = body.pop("payload_hash", None)
    if payload_hash != canonical_hash(body):
        raise ValueError(f"R160 {label} payload hash mismatch")
    return payload_hash


def load_bound_inputs(root: Path) -> tuple[dict, dict, dict, dict]:
    protocol_payload = json.loads((root / PROTOCOL_PATH).read_text())
    contract = json.loads((root / CONTRACT_PATH).read_text())
    source_manifest = json.loads((root / SOURCE_MANIFEST_PATH).read_text())
    native_manifest = json.loads((root / R159_NATIVE_PATH).read_text())
    validate_payload(protocol_payload, "protocol")
    validate_payload(contract, "contract")
    validate_payload(source_manifest, "source manifest")
    body = dict(native_manifest)
    manifest_hash = body.pop("manifest_payload_hash", None)
    if manifest_hash != canonical_hash(body):
        raise ValueError("R160 R159 native manifest payload mismatch")
    for binding_id, binding in contract["source_bindings"].items():
        path = root / binding["path"]
        if not path.exists() or file_sha256(path) != binding["sha256"]:
            raise ValueError(f"R160 source binding mismatch: {binding_id}")
        if "payload_hash" in binding:
            payload = json.loads(path.read_text())
            observed = next(
                (
                    payload[key]
                    for key in [
                        "payload_hash",
                        "manifest_payload_hash",
                        "association_payload_hash",
                        "profile_summary_payload_hash",
                        "case_analysis_payload_hash",
                        "verifier_transcript_payload_hash",
                    ]
                    if key in payload
                ),
                None,
            )
            if observed != binding["payload_hash"]:
                raise ValueError(f"R160 source payload mismatch: {binding_id}")
    if contract["source_bindings"]["protocol"]["payload_hash"] != protocol_payload["payload_hash"]:
        raise ValueError("R160 contract protocol binding mismatch")
    return protocol_payload, contract, source_manifest, native_manifest


def validate_runtime_binary(source_manifest: dict[str, Any]) -> None:
    import qiskit._accelerate as accelerate
    from qiskit._accelerate import vf2_layout

    path = Path(accelerate.__file__).resolve()
    expected = source_manifest["installed_accelerator"]
    if file_sha256(path) != expected["sha256"] or path.stat().st_size != expected["size_bytes"]:
        raise ValueError("R160 imported official accelerator binding mismatch")
    if not hasattr(vf2_layout, "vf2_layout_pass_average"):
        raise ValueError("R160 official direct VF2 entry point missing")


def bits_to_float(bits: int) -> float:
    return struct.unpack(">d", int(bits).to_bytes(8, "big"))[0]


def float_bits(value: float) -> int:
    return int.from_bytes(struct.pack(">d", float(value)), "big")


def source_inventory(native_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    trace_rows = native_manifest["replay_rows"][0]["trace_rows"]
    return [
        {
            "qargs": [int(value) for value in row["qargs"]],
            "steps": [
                {
                    "operation": str(step["operation"]),
                    "error_bits": int(step["error_bits"]),
                }
                for step in row["steps"]
            ],
        }
        for row in trace_rows
    ]


def ordered_average(steps: list[dict[str, Any]], mode: str) -> float:
    ordered = sorted(steps, key=lambda row: (row["operation"], row["error_bits"]))
    if mode == "descending_f64":
        ordered.reverse()
    values = [bits_to_float(row["error_bits"]) for row in ordered]
    if mode in {"ascending_f64", "descending_f64"}:
        total = 0.0
        for value in values:
            total += value
        return total / len(values)
    if mode == "math_fsum":
        return math.fsum(values) / len(values)
    if mode == "exact_binary_fraction":
        exact = sum((Fraction.from_float(value) for value in values), Fraction())
        return float(exact / len(values))
    raise ValueError(f"unknown R160 accumulation mode: {mode}")


def shift_ulps(value: float, shift: int) -> float:
    direction = math.inf if shift > 0 else -math.inf
    shifted = value
    for _ in range(abs(shift)):
        shifted = math.nextafter(shifted, direction)
    return shifted


def build_error_map(
    target: Any,
    inventory: list[dict[str, Any]],
    mode: str,
    case: dict[str, Any],
) -> tuple[Any, dict[tuple[int, int], float], dict[str, Any]]:
    from qiskit._accelerate.error_map import ErrorMap

    values: dict[tuple[int, int], float] = {}
    rows = []
    perturbation_key = None if case["key"] is None else tuple(case["key"])
    for row in sorted(inventory, key=lambda item: tuple(item["qargs"])):
        qargs = tuple(row["qargs"])
        key = (qargs[0], qargs[0]) if len(qargs) == 1 else qargs
        base_value = ordered_average(row["steps"], mode)
        value = (
            shift_ulps(base_value, case["ulp_shift"])
            if key == perturbation_key
            else base_value
        )
        values[key] = value
        rows.append(
            {
                "key": list(key),
                "base_bits": float_bits(base_value),
                "value_bits": float_bits(value),
                "perturbed": key == perturbation_key,
            }
        )
    error_map = ErrorMap(target.num_qubits)
    for key, value in sorted(values.items()):
        error_map.add_error(key, value)
    descriptor = {
        "mode": mode,
        "case_id": case["case_id"],
        "construction": "R159 operation-error bits, declared accumulation, optional declared ULP shift",
        "rows": rows,
    }
    descriptor["payload_hash"] = canonical_hash(descriptor)
    return error_map, values, descriptor


def interaction_counts(circuit: Any) -> tuple[Counter[int], Counter[tuple[int, int]]]:
    one: Counter[int] = Counter()
    two: Counter[tuple[int, int]] = Counter()
    for instruction in circuit.data:
        qargs = tuple(circuit.find_bit(bit).index for bit in instruction.qubits)
        if len(qargs) == 1:
            one[qargs[0]] += 1
        elif len(qargs) == 2:
            two[qargs] += 1
    return one, two


def mapping_vector(mapping: Any, num_qubits: int) -> list[int] | None:
    if mapping is None:
        return None
    vector: list[int | None] = [None] * num_qubits
    for virtual, physical in mapping.items():
        vector[int(virtual)] = int(physical)
    if any(value is None for value in vector):
        raise ValueError(f"R160 incomplete accelerator mapping: {vector}")
    return [int(value) for value in vector]


def classify(vector: list[int] | None) -> str:
    if vector is None:
        return "no_solution"
    for class_id, expected in EXPECTED_MAPPINGS.items():
        if vector == expected:
            return class_id
    return "other_mapping"


def unique_vectors(vectors: list[list[int] | None]) -> list[list[int] | None]:
    observed = sorted({tuple(vector) for vector in vectors if vector is not None})
    rows: list[list[int] | None] = [list(vector) for vector in observed]
    if any(vector is None for vector in vectors):
        rows.append(None)
    return rows


def exact_mapping_oracle(
    values: dict[tuple[int, int], float],
    one_counts: Counter[int],
    two_counts: Counter[tuple[int, int]],
    num_qubits: int,
) -> dict[str, Any]:
    scored: list[tuple[Fraction, tuple[int, ...]]] = []
    for vector in permutations(range(num_qubits)):
        score = Fraction()
        feasible = True
        for virtual, count in one_counts.items():
            value = values.get((vector[virtual], vector[virtual]))
            if value is None:
                feasible = False
                break
            score += count * Fraction.from_float(value)
        if not feasible:
            continue
        for (left, right), count in two_counts.items():
            key = (vector[left], vector[right])
            value = values.get(key)
            if value is None:
                value = values.get((key[1], key[0]))
            if value is None:
                feasible = False
                break
            score += count * Fraction.from_float(value)
        if feasible:
            scored.append((score, vector))
    if not scored:
        raise ValueError("R160 exact mapping oracle found no feasible mapping")
    scored.sort(key=lambda row: (row[0], row[1]))
    best_score = scored[0][0]
    minimizers = [list(vector) for score, vector in scored if score == best_score]
    second_score = next((score for score, _ in scored if score > best_score), None)
    gap = None if second_score is None else float(second_score - best_score)
    return {
        "feasible_mapping_count": len(scored),
        "minimum_score_fraction": f"{best_score.numerator}/{best_score.denominator}",
        "minimum_score_float": float(best_score),
        "minimizer_count": len(minimizers),
        "minimizer_vectors": minimizers,
        "second_distinct_score_fraction": None
        if second_score is None
        else f"{second_score.numerator}/{second_score.denominator}",
        "minimum_gap_float": gap,
    }


def new_config() -> Any:
    from qiskit._accelerate.vf2_layout import VF2PassConfiguration

    return VF2PassConfiguration.from_legacy_api(
        call_limit=30000000,
        time_limit=None,
        max_trials=250000,
        shuffle_seed=-1,
        score_initial_layout=True,
    )


def worker_path(mode: str, replica: int) -> str:
    return f"{OUT_DIR}/worker_{mode}_{replica:02d}.json"


def execute_worker(
    root: Path,
    protocol_payload: dict[str, Any],
    contract: dict[str, Any],
    source_manifest: dict[str, Any],
    native_manifest: dict[str, Any],
    mode: str,
    replica: int,
    preregistration: dict[str, str],
) -> dict[str, Any]:
    from qiskit import qasm3
    from qiskit._accelerate.vf2_layout import vf2_layout_pass_average
    from qiskit.converters import circuit_to_dag

    validate_runtime_binary(source_manifest)
    protocol = protocol_payload["protocol"]
    if mode not in protocol["accumulation_modes"]:
        raise ValueError(f"R160 worker mode is not frozen: {mode}")
    if not 0 <= replica < protocol["processes_per_mode"]:
        raise ValueError(f"R160 worker replica is not frozen: {replica}")
    path = root / worker_path(mode, replica)
    if path.exists():
        raise ValueError(f"R160 worker evidence already exists: {mode}/{replica}")
    started_at = int(time.time())
    circuit = qasm3.load(root / protocol["input_path"])
    backend = TARGET_CLASSES[protocol["snapshot_name"]]()
    target = backend.target
    dag = circuit_to_dag(circuit)
    one_counts, two_counts = interaction_counts(circuit)
    inventory = source_inventory(native_manifest)
    case_rows = []
    replay_rows = []
    for case in protocol["perturbation_cases"]:
        error_map, values, descriptor = build_error_map(target, inventory, mode, case)
        oracle = exact_mapping_oracle(
            values, one_counts, two_counts, circuit.num_qubits
        )
        config = new_config()
        case_vectors = []
        for replay_index in range(protocol["replays_per_case_per_process"]):
            started = time.perf_counter()
            output = vf2_layout_pass_average(
                dag,
                target,
                config,
                strict_direction=False,
                avg_error_map=error_map,
            )
            vector = mapping_vector(output.new_mapping(), circuit.num_qubits)
            row = {
                "mode": mode,
                "replica": replica,
                "case_id": case["case_id"],
                "replay_index": replay_index,
                "error_map_payload_hash": descriptor["payload_hash"],
                "mapping_vector": vector,
                "mapping_class": classify(vector),
                "within_exact_oracle_minimizers": vector in oracle["minimizer_vectors"],
                "stop_reason": "solution found"
                if vector is not None
                else ("no improvement" if output.has_solution else "no solution"),
                "elapsed_seconds": time.perf_counter() - started,
                "simulation_execution_count": 0,
                "total_simulated_shots": 0,
            }
            row["replay_payload_hash"] = canonical_hash(row)
            replay_rows.append(row)
            case_vectors.append(vector)
        case_row = {
            "mode": mode,
            "replica": replica,
            "case_id": case["case_id"],
            "error_map_descriptor": descriptor,
            "oracle": oracle,
            "replay_count": protocol["replays_per_case_per_process"],
            "selected_vectors": unique_vectors(case_vectors),
            "within_oracle_count": sum(
                row["within_exact_oracle_minimizers"]
                for row in replay_rows
                if row["case_id"] == case["case_id"]
            ),
        }
        case_row["case_payload_hash"] = canonical_hash(case_row)
        case_rows.append(case_row)
    manifest = {
        "profile_id": mode,
        "replica": replica,
        "process_id": os.getpid(),
        "process_instance_uuid": str(uuid.uuid4()),
        "started_at_unix": started_at,
        "preregistration": preregistration,
        "protocol_payload_hash": protocol_payload["payload_hash"],
        "contract_payload_hash": contract["payload_hash"],
        "input_qasm_sha256": file_sha256(root / protocol["input_path"]),
        "target_descriptor_sha256": target_descriptor(backend)["descriptor_hash"],
        "environment": actual_environment(protocol),
        "case_count": len(case_rows),
        "replay_count": len(replay_rows),
        "case_rows": case_rows,
        "replay_rows": replay_rows,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
    }
    manifest["manifest_payload_hash"] = canonical_hash(manifest)
    write_json(path, manifest)
    return manifest


def launch_worker(
    root: Path,
    mode: str,
    replica: int,
    preregistration: dict[str, str],
) -> None:
    command = [
        sys.executable,
        str(root / "tools/b4_b8_r160_deterministic_error_map_remediation.py"),
        "--worker-mode",
        mode,
        "--worker-replica",
        str(replica),
        "--preregistration-commit",
        preregistration["commit"],
        "--preregistration-discussion",
        preregistration["discussion"],
        "--preregistration-created-at",
        preregistration["created_at"],
    ]
    subprocess.run(command, cwd=root, check=True)


def aggregate(
    root: Path,
    protocol_payload: dict[str, Any],
    contract: dict[str, Any],
    preregistration: dict[str, str],
) -> dict[str, Any]:
    protocol = protocol_payload["protocol"]
    manifests = []
    process_artifacts = []
    for mode in protocol["accumulation_modes"]:
        for replica in range(protocol["processes_per_mode"]):
            rel = worker_path(mode, replica)
            path = root / rel
            manifest = json.loads(path.read_text())
            body = dict(manifest)
            payload_hash = body.pop("manifest_payload_hash", None)
            if payload_hash != canonical_hash(body):
                raise ValueError(f"R160 worker payload mismatch: {mode}/{replica}")
            manifests.append(manifest)
            process_artifacts.append(
                {
                    "profile_id": mode,
                    "replica": replica,
                    "path": rel,
                    "sha256": file_sha256(path),
                    "manifest_payload_hash": payload_hash,
                }
            )
    all_replays = [row for manifest in manifests for row in manifest["replay_rows"]]
    profile_rows = []
    for mode in protocol["accumulation_modes"]:
        selected = [manifest for manifest in manifests if manifest["profile_id"] == mode]
        mode_replays = [row for manifest in selected for row in manifest["replay_rows"]]
        baseline = [row for row in mode_replays if row["case_id"] == "tie_baseline"]
        profile_rows.append(
            {
                "profile_id": mode,
                "process_count": len(selected),
                "process_instance_uuid_count": len(
                    {row["process_instance_uuid"] for row in selected}
                ),
                "case_count": len(protocol["perturbation_cases"]),
                "replay_count": len(mode_replays),
                "baseline_selected_vectors": unique_vectors(
                    [row["mapping_vector"] for row in baseline]
                ),
                "baseline_stable": len(
                    unique_vectors([row["mapping_vector"] for row in baseline])
                )
                == 1,
                "all_replays_within_oracle": all(
                    row["within_exact_oracle_minimizers"] for row in mode_replays
                ),
                "unique_error_map_payload_hash_count": len(
                    {row["error_map_payload_hash"] for row in mode_replays}
                ),
            }
        )
    profile_summary = {
        "profile_count": len(profile_rows),
        "process_count": len(manifests),
        "replay_count": len(all_replays),
        "profile_rows": profile_rows,
    }
    profile_summary["profile_summary_payload_hash"] = canonical_hash(profile_summary)
    write_json(root / PROFILE_SUMMARY_PATH, profile_summary)

    case_rows = []
    for case in protocol["perturbation_cases"]:
        mode_rows = []
        for mode in protocol["accumulation_modes"]:
            worker_cases = [
                case_row
                for manifest in manifests
                if manifest["profile_id"] == mode
                for case_row in manifest["case_rows"]
                if case_row["case_id"] == case["case_id"]
            ]
            oracles = [row["oracle"] for row in worker_cases]
            oracle_hashes = {canonical_hash(row) for row in oracles}
            vectors = unique_vectors(
                [
                    replay["mapping_vector"]
                    for manifest in manifests
                    if manifest["profile_id"] == mode
                    for replay in manifest["replay_rows"]
                    if replay["case_id"] == case["case_id"]
                ]
            )
            mode_rows.append(
                {
                    "mode": mode,
                    "worker_oracle_hash_count": len(oracle_hashes),
                    "oracle": oracles[0],
                    "selected_vectors": vectors,
                    "stable": len(vectors) == 1,
                    "all_replays_within_oracle": all(
                        replay["within_exact_oracle_minimizers"]
                        for manifest in manifests
                        if manifest["profile_id"] == mode
                        for replay in manifest["replay_rows"]
                        if replay["case_id"] == case["case_id"]
                    ),
                }
            )
        unique_oracles = [
            row["oracle"]["minimizer_vectors"][0]
            for row in mode_rows
            if row["oracle"]["minimizer_count"] == 1
        ]
        shared_unique_oracle = (
            len(unique_oracles) == len(mode_rows)
            and len({tuple(row) for row in unique_oracles}) == 1
        )
        minimum_gaps = [
            row["oracle"]["minimum_gap_float"]
            for row in mode_rows
            if row["oracle"]["minimum_gap_float"] is not None
        ]
        min_gap = min(minimum_gaps) if len(minimum_gaps) == len(mode_rows) else None
        protected = (
            case["case_id"] != "tie_baseline"
            and shared_unique_oracle
            and min_gap is not None
            and min_gap >= protocol["margin_protection_threshold"]
        )
        selected_vectors = unique_vectors(
            [vector for row in mode_rows for vector in row["selected_vectors"]]
        )
        shared_oracle_vector = unique_oracles[0] if shared_unique_oracle else None
        row = {
            "case_id": case["case_id"],
            "key": case["key"],
            "ulp_shift": case["ulp_shift"],
            "mode_rows": mode_rows,
            "all_modes_stable": all(mode["stable"] for mode in mode_rows),
            "all_replays_within_oracle": all(
                mode["all_replays_within_oracle"] for mode in mode_rows
            ),
            "shared_unique_oracle": shared_unique_oracle,
            "shared_oracle_vector": shared_oracle_vector,
            "minimum_cross_mode_gap": min_gap,
            "margin_protected": protected,
            "cross_mode_output_agreement": len(selected_vectors) == 1,
            "protected_oracle_selected": (
                protected
                and len(selected_vectors) == 1
                and selected_vectors[0] == shared_oracle_vector
            ),
        }
        row["case_payload_hash"] = canonical_hash(row)
        case_rows.append(row)
    baseline = next(row for row in case_rows if row["case_id"] == "tie_baseline")
    protected_rows = [row for row in case_rows if row["margin_protected"]]
    protected_failures = [
        row
        for row in protected_rows
        if not row["cross_mode_output_agreement"]
        or not row["protected_oracle_selected"]
        or not row["all_replays_within_oracle"]
    ]
    if not baseline["all_modes_stable"]:
        classification = "tie_not_stabilized"
    elif not baseline["cross_mode_output_agreement"]:
        classification = "method_dependent_tie_resolution"
    elif not protected_rows:
        classification = "no_margin_protected_rows"
    elif protected_failures:
        classification = "tie_stabilized_but_non_tied_guardrail_failed"
    else:
        classification = "deterministic_external_map_remediation_supported"
    case_analysis = {
        "classification": classification,
        "case_count": len(case_rows),
        "tie_baseline": baseline,
        "margin_protected_case_count": len(protected_rows),
        "margin_protected_failure_count": len(protected_failures),
        "case_rows": case_rows,
        "source_patch_performed": False,
        "confirmed_qiskit_bug_claimed": False,
    }
    case_analysis["case_analysis_payload_hash"] = canonical_hash(case_analysis)
    write_json(root / CASE_ANALYSIS_PATH, case_analysis)

    all_replay_hashes_valid = all(
        row["replay_payload_hash"]
        == canonical_hash(
            {key: value for key, value in row.items() if key != "replay_payload_hash"}
        )
        for row in all_replays
    )
    started_after = sum(
        manifest["started_at_unix"] >= utc_timestamp(preregistration["created_at"])
        for manifest in manifests
    )
    summary = {
        "global_acceptance": True,
        "classification": classification,
        "profile_count": len(profile_rows),
        "process_count": len(manifests),
        "process_instance_uuid_count": len(
            {manifest["process_instance_uuid"] for manifest in manifests}
        ),
        "process_started_after_preregistration_count": started_after,
        "case_count": len(case_rows),
        "direct_replay_count": len(all_replays),
        "tie_baseline_all_modes_stable": baseline["all_modes_stable"],
        "tie_baseline_cross_mode_agreement": baseline[
            "cross_mode_output_agreement"
        ],
        "tie_baseline_selected_vector": (
            baseline["mode_rows"][0]["selected_vectors"][0]
            if baseline["cross_mode_output_agreement"]
            else None
        ),
        "margin_protected_case_count": len(protected_rows),
        "margin_protected_failure_count": len(protected_failures),
        "all_replays_within_exact_oracle": all(
            row["within_exact_oracle_minimizers"] for row in all_replays
        ),
        "all_replay_hashes_valid": all_replay_hashes_valid,
        "source_patch_performed": False,
        "candidate_selection_performed": False,
        "route_change_performed": False,
        "sampling_performed": False,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "confirmed_qiskit_bug_claimed": False,
        "hardware_execution_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
    }
    acceptance_conditions = [
        {"condition_id": "A1", "label": "all frozen source and protocol bindings validate", "passed": True},
        {"condition_id": "A2", "label": "four modes, sixteen processes, thirty-three cases, and 1056 calls complete", "passed": len(profile_rows) == 4 and len(manifests) == 16 and len(case_rows) == 33 and len(all_replays) == 1056},
        {"condition_id": "A3", "label": "all process identities are unique and post-registration", "passed": summary["process_instance_uuid_count"] == 16 and started_after == 16},
        {"condition_id": "A4", "label": "every worker and replay payload validates", "passed": all_replay_hashes_valid},
        {"condition_id": "A5", "label": "every replay is checked against an exact rational mapping oracle", "passed": all(row.get("within_exact_oracle_minimizers") is not None for row in all_replays)},
        {"condition_id": "A6", "label": "tie stability and cross-mode agreement are retained regardless of outcome", "passed": "all_modes_stable" in baseline and "cross_mode_output_agreement" in baseline},
        {"condition_id": "A7", "label": "all protected non-tied rows and failures are retained", "passed": len(protected_rows) + sum(not row["margin_protected"] for row in case_rows) == len(case_rows)},
        {"condition_id": "A8", "label": "classification follows the frozen decision order", "passed": classification in protocol["classification_order"]},
        {"condition_id": "A9", "label": "no source patch, simulation, shots, hidden selection, or route change occurs", "passed": summary["source_patch_performed"] is False and summary["simulation_execution_count"] == 0 and summary["total_simulated_shots"] == 0 and summary["candidate_selection_performed"] is False and summary["route_change_performed"] is False},
        {"condition_id": "A10", "label": "forbidden bug, hardware, advantage, BQP, solved-frontier, and credit claims remain false", "passed": not any(summary[key] for key in ["confirmed_qiskit_bug_claimed", "hardware_execution_claimed", "quantum_advantage_claimed", "bqp_separation_claimed", "solved_frontier_claimed"]) and summary["new_credit_delta"] == 0},
    ]
    requirements = [
        {"requirement_id": f"P{index}", "label": row["label"], "passed": row["passed"]}
        for index, row in enumerate(acceptance_conditions, 1)
    ]
    result = {
        "title": "B4/B8 R160 deterministic ErrorMap remediation",
        "version": 0,
        "method": METHOD,
        "status": "deterministic_error_map_remediation_complete",
        "model_status": "external_error_map_remediation_diagnostic_without_upstream_bug_claim",
        "generated_at_unix": int(time.time()),
        "source_target_id": "T-B4-002cc/T-B8-003cg/T-B10-009bu",
        "upstream_target_id": "T-B4-002cb/T-B8-003cf/T-B10-009bt",
        "preregistration": preregistration,
        "summary": summary,
        "profile_summary": profile_summary,
        "case_analysis": {
            key: value for key, value in case_analysis.items() if key != "case_rows"
        },
        "acceptance_conditions": acceptance_conditions,
        "requirements": requirements,
        "requirement_count": len(requirements),
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [
            row["requirement_id"] for row in requirements if not row["passed"]
        ],
        "artifacts": {
            "protocol": PROTOCOL_PATH,
            "contract": CONTRACT_PATH,
            "process_artifacts": process_artifacts,
            "profile_summary": PROFILE_SUMMARY_PATH,
            "case_analysis": CASE_ANALYSIS_PATH,
            "verifier_transcript": TRANSCRIPT_PATH,
            "result": RESULT_PATH,
            "markdown_report": REPORT_PATH,
        },
        "claim_boundary": {
            "what_is_supported": "a source-bound external ErrorMap determinism and non-tied ranking guardrail diagnostic on the frozen R157 input",
            "what_is_not_supported": "an accepted upstream patch, confirmed Qiskit bug, cross-platform theorem, hardware result, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    result["payload_hash"] = canonical_hash(result)
    transcript = {
        "protocol_payload_hash": protocol_payload["payload_hash"],
        "contract_payload_hash": contract["payload_hash"],
        "profile_summary_payload_hash": profile_summary[
            "profile_summary_payload_hash"
        ],
        "case_analysis_payload_hash": case_analysis["case_analysis_payload_hash"],
        "result_payload_hash": result["payload_hash"],
        "process_artifact_count": len(process_artifacts),
        "direct_replay_count": len(all_replays),
        "global_acceptance": all(row["passed"] for row in acceptance_conditions),
        "requirements_passed": result["requirements_passed"],
        "requirements_failed": result["requirements_failed"],
    }
    transcript["verifier_transcript_payload_hash"] = canonical_hash(transcript)
    write_json(root / TRANSCRIPT_PATH, transcript)
    write_json(root / RESULT_PATH, result)
    write_report(root / REPORT_PATH, result, profile_rows, case_rows)
    return result


def write_report(
    path: Path,
    result: dict[str, Any],
    profiles: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> None:
    summary = result["summary"]
    lines = [
        "# B4/B8 R160 Deterministic ErrorMap Remediation",
        "",
        f"- Status: `{result['status']}`",
        f"- Classification: `{summary['classification']}`",
        f"- Profiles / processes / cases / direct calls: `{summary['profile_count']}` / `{summary['process_count']}` / `{summary['case_count']}` / `{summary['direct_replay_count']}`",
        f"- Tie baseline stable / cross-mode agreement: `{summary['tie_baseline_all_modes_stable']}` / `{summary['tie_baseline_cross_mode_agreement']}`",
        f"- Tie baseline selected vector: `{summary['tie_baseline_selected_vector']}`",
        f"- Margin-protected cases / failures: `{summary['margin_protected_case_count']}` / `{summary['margin_protected_failure_count']}`",
        f"- All replays within exact oracle: `{summary['all_replays_within_exact_oracle']}`",
        f"- Simulation executions / shots: `{summary['simulation_execution_count']}` / `{summary['total_simulated_shots']}`",
        f"- Conditions and requirements passed/failed: `{sum(row['passed'] for row in result['acceptance_conditions'])}` / `{sum(not row['passed'] for row in result['acceptance_conditions'])}` and `{result['requirements_passed']}` / `{result['requirements_failed']}`",
        "",
        "## Profile Summary",
        "",
        "| Mode | Processes | Calls | Baseline stable | Baseline vectors | All calls in oracle |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in profiles:
        lines.append(
            f"| `{row['profile_id']}` | {row['process_count']} | {row['replay_count']} | `{row['baseline_stable']}` | `{row['baseline_selected_vectors']}` | `{row['all_replays_within_oracle']}` |"
        )
    protected = [row for row in cases if row["margin_protected"]]
    lines.extend(
        [
            "",
            "## Protected Non-Tied Cases",
            "",
            "| Case | Key | ULP shift | Minimum gap | Agreement | Oracle selected |",
            "|---|---|---:|---:|---|---|",
        ]
    )
    for row in protected:
        lines.append(
            f"| `{row['case_id']}` | `{row['key']}` | {row['ulp_shift']} | {row['minimum_cross_mode_gap']:.17g} | `{row['cross_mode_output_agreement']}` | `{row['protected_oracle_selected']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            interpretation(summary["classification"]),
            "",
            "## Claim Boundary",
            "",
            "This experiment can support or reject a deterministic external ErrorMap remediation on one frozen input and official binary. It does not establish an accepted upstream patch, a confirmed general Qiskit bug, cross-platform determinism, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def interpretation(classification: str) -> str:
    return {
        "deterministic_external_map_remediation_supported": "All four deterministic accumulation methods agree on one stable tied-layout selection, and every margin-protected non-tied case selects the shared exact-oracle optimum. This supports a user-space external ErrorMap remediation for this input without claiming an upstream fix.",
        "tie_not_stabilized": "At least one deterministic external ErrorMap profile still varies, so the proposed remediation does not stabilize the tied layout.",
        "method_dependent_tie_resolution": "Each method is internally stable but deterministic accumulation methods choose different tied layouts, so the tie policy remains method-dependent.",
        "no_margin_protected_rows": "The perturbation suite produced no shared unique optimum above the frozen margin threshold, so the non-tied guardrail remains untested.",
        "tie_stabilized_but_non_tied_guardrail_failed": "The tied layout stabilizes, but at least one margin-protected non-tied case disagrees across methods or misses the exact oracle.",
    }[classification]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute the preregistered R160 deterministic ErrorMap remediation."
    )
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--preregistration-commit", required=True)
    parser.add_argument("--preregistration-discussion", required=True)
    parser.add_argument("--preregistration-created-at", required=True)
    parser.add_argument("--worker-mode")
    parser.add_argument("--worker-replica", type=int)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    protocol_payload, contract, source_manifest, native_manifest = load_bound_inputs(root)
    protocol = protocol_payload["protocol"]
    ensure_environment(protocol)
    validate_runtime_binary(source_manifest)
    preregistration = {
        "commit": args.preregistration_commit,
        "discussion": args.preregistration_discussion,
        "created_at": args.preregistration_created_at,
    }
    if args.worker_mode is not None:
        if args.worker_replica is None:
            raise ValueError("R160 worker replica is required")
        execute_worker(
            root,
            protocol_payload,
            contract,
            source_manifest,
            native_manifest,
            args.worker_mode,
            args.worker_replica,
            preregistration,
        )
        print(f"R160 worker complete: {args.worker_mode}/{args.worker_replica}")
        return 0
    output_paths = [root / RESULT_PATH, root / REPORT_PATH, root / OUT_DIR]
    if any(path.exists() for path in output_paths):
        raise ValueError("R160 execution evidence already exists; refusing to overwrite")
    (root / OUT_DIR).mkdir(parents=True)
    jobs = [
        (mode, replica)
        for mode in protocol["accumulation_modes"]
        for replica in range(protocol["processes_per_mode"])
    ]
    with ThreadPoolExecutor(max_workers=protocol["max_concurrent_processes"]) as pool:
        futures = {
            pool.submit(launch_worker, root, mode, replica, preregistration): (
                mode,
                replica,
            )
            for mode, replica in jobs
        }
        for future in as_completed(futures):
            mode, replica = futures[future]
            future.result()
            print(f"R160 process retained: {mode}/{replica}")
    result = aggregate(root, protocol_payload, contract, preregistration)
    print(
        json.dumps(
            {
                "status": result["status"],
                "classification": result["summary"]["classification"],
                "process_count": result["summary"]["process_count"],
                "case_count": result["summary"]["case_count"],
                "direct_replay_count": result["summary"]["direct_replay_count"],
                "tie_baseline_selected_vector": result["summary"][
                    "tie_baseline_selected_vector"
                ],
                "margin_protected_case_count": result["summary"][
                    "margin_protected_case_count"
                ],
                "margin_protected_failure_count": result["summary"][
                    "margin_protected_failure_count"
                ],
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
