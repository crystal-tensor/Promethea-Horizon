#!/usr/bin/env python3
"""Freeze the R159 source-instrumented ErrorMap trace protocol."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r154_deterministic_automatic_replay import canonical_hash


METHOD = "b4_b8_r159_error_map_accumulation_trace_protocol_v0"
PROTOCOL_PATH = "results/B4_B8_R159_error_map_accumulation_trace_protocol_v0.json"
CONTRACT_PATH = "benchmarks/B4_B8_R159_error_map_accumulation_trace_contract_v0.json"
REPORT_PATH = "research/B4_B8_R159_error_map_accumulation_trace_protocol.md"
BUILD_MANIFEST_PATH = "research/source_lineage/Qiskit_2_4_1_R159_instrumented_build_manifest.json"
PATCH_PATH = "research/source_lineage/Qiskit_2_4_1_R159_error_map_trace.patch"
EXECUTOR_PATH = "tools/b4_b8_r159_error_map_accumulation_trace.py"
SOURCE_MANIFEST_PATH = "research/source_lineage/Qiskit_2_4_1_vf2_source_manifest.json"
R158_RESULT_PATH = "results/B4_B8_R158_vf2_accelerator_boundary_v0.json"
INPUT_PATH = "benchmarks/B4_B8_R157_vf2_post_layout_input_v0.qasm"


def command_output(command: list[str]) -> str:
    completed = subprocess.run(command, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def payload_binding(root: Path, path: str) -> dict[str, Any]:
    payload = json.loads((root / path).read_text())
    return {"path": path, "sha256": file_sha256(root / path), "payload_hash": payload["payload_hash"]}


def plain_binding(root: Path, path: str) -> dict[str, Any]:
    return {"path": path, "sha256": file_sha256(root / path)}


def build_manifest(root: Path, patched_source: Path, binary: Path) -> dict[str, Any]:
    source_manifest = json.loads((root / SOURCE_MANIFEST_PATH).read_text())
    rust_row = next(row for row in source_manifest["source_rows"] if row["source_id"] == "rust_vf2_layout_pass")
    manifest = {
        "manifest_id": "Qiskit-2.4.1-R159-instrumented-build-v0",
        "base_qiskit_commit": "0fd015a22b84c9082173597a5d2304dc0aaec08c",
        "base_source": {
            "path": rust_row["path"],
            "sha256": rust_row["sha256"],
        },
        "instrumentation_patch": plain_binding(root, PATCH_PATH),
        "patched_source": {
            "path": rust_row["path"],
            "sha256": file_sha256(patched_source),
        },
        "instrumented_binary": {
            "build_relative_path": "qiskit/_accelerate.cpython-312-darwin.so",
            "sha256": file_sha256(binary),
            "size_bytes": binary.stat().st_size,
        },
        "build_environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "rustc": command_output(["rustc", "--version"]),
            "cargo": command_output(["cargo", "--version"]),
            "setuptools_rust": "1.12.0",
            "build_profile": "release",
            "rustup_toolchain_override": "stable",
            "build_command": "RUSTUP_TOOLCHAIN=stable QISKIT_BUILD_PROFILE=release python -m pip install -e . --no-build-isolation --no-deps",
        },
        "build_checks": {
            "patch_applies_to_base_commit": True,
            "cargo_fmt_check_passed": True,
            "editable_release_build_passed": True,
            "traced_entry_point_imported": True,
            "native_ascending_descending_smoke_calls": 3,
            "invalid_mode_rejected": True,
            "smoke_backend": "GenericBackendV2(num_qubits=3, seed=159)",
            "smoke_circuit_operation_count": 3,
            "frozen_r157_input_used_during_smoke": False,
        },
        "claim_boundary": "The pre-registration build and API smoke establish only that the exact instrumented source compiles and emits traces on an unrelated three-qubit toy. They disclose no R159 frozen-input outcome.",
    }
    manifest["payload_hash"] = canonical_hash(manifest)
    return manifest


def protocol_payload(root: Path, build: dict[str, Any]) -> dict[str, Any]:
    source_bindings = {
        "r158_result": payload_binding(root, R158_RESULT_PATH),
        "r157_input": plain_binding(root, INPUT_PATH),
        "qiskit_source_manifest": payload_binding(root, SOURCE_MANIFEST_PATH),
        "instrumentation_patch": plain_binding(root, PATCH_PATH),
        "instrumented_build_manifest": payload_binding(root, BUILD_MANIFEST_PATH),
        "executor": plain_binding(root, EXECUTOR_PATH),
    }
    protocol = {
        "snapshot_name": "FakeNairobiV2",
        "input_path": INPUT_PATH,
        "input_qasm_sha256": "ce216610e995b4c8b4bd9de6547ac6069961e1eb8881997aa05e0068ea16ab98",
        "target_descriptor_sha256": "702c8fd9dcf67a069e7af63e31a57c74c17aaa5e3c5b6d8c2e28ec0c049c0de7",
        "qiskit_source_commit": build["base_qiskit_commit"],
        "base_source_sha256": build["base_source"]["sha256"],
        "instrumentation_patch_sha256": build["instrumentation_patch"]["sha256"],
        "patched_source_sha256": build["patched_source"]["sha256"],
        "instrumented_binary_sha256": build["instrumented_binary"]["sha256"],
        "instrumented_binary_size_bytes": build["instrumented_binary"]["size_bytes"],
        "build_manifest_path": BUILD_MANIFEST_PATH,
        "build_manifest_payload_hash": build["payload_hash"],
        "shared_tied_score": 0.45894321220828727,
        "expected_mapping_classes": {
            "endpoint_4_to_0": [6, 5, 4, 3, 0, 1, 2],
            "endpoint_4_to_2": [6, 5, 4, 3, 2, 1, 0],
        },
        "vf2_configuration": {
            "call_limit": 30000000,
            "max_trials": 250000,
            "shuffle_seed": -1,
            "strict_direction": False,
            "time_limit": None,
            "score_initial_layout": True,
        },
        "profiles": [
            {"profile_id": "native_hashset_order", "operation_order": "native", "process_count": 1, "replay_count": 128, "dag_reused": True, "target_reused": True, "config_reused": True},
            {"profile_id": "ascending_sorted_order", "operation_order": "ascending", "process_count": 1, "replay_count": 64, "dag_reused": True, "target_reused": True, "config_reused": True},
            {"profile_id": "descending_sorted_order", "operation_order": "descending", "process_count": 1, "replay_count": 64, "dag_reused": True, "target_reused": True, "config_reused": True},
        ],
        "profile_count": 3,
        "total_process_count": 3,
        "total_trace_replay_count": 256,
        "retained_per_call_fields": [
            "operation order by qargs",
            "operation error f64 bits",
            "accumulated error f64 bits",
            "average error f64 bits",
            "operation-order hash",
            "average-error-bits hash",
            "full trace hash",
            "mapping vector and class",
            "stop reason",
            "elapsed time",
        ],
        "classification_order": [
            "native_nonreproduction",
            "variation_survives_sorted_accumulation",
            "operation_order_f64_path_supported",
            "average_error_bits_insufficient_for_mapping",
            "operation_order_changes_without_average_bit_change",
            "trace_inconclusive",
        ],
        "support_rule": "operation_order_f64_path_supported requires native mapping variation, both sorted profiles to collapse, multiple native average-error bit maps, a functional native order-hash to error-bits relation, and a functional error-bits to mapping-class relation",
        "process_environment": {
            "PYTHONHASHSEED": "0",
            "RAYON_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "QISKIT_PARALLEL": "FALSE",
        },
        "frozen_software": {
            "python": "3.12.6",
            "qiskit": "2.4.1",
        },
        "pre_registration_build_smoke": build["build_checks"],
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "new_hidden_seed_count": 0,
        "candidate_selection_performed": False,
        "route_change_performed": False,
        "sampling_performed": False,
        "execution_started": False,
    }
    requirements = [
        {"requirement_id": "P1", "label": "source patch applies to the exact Qiskit release commit", "passed": True},
        {"requirement_id": "P2", "label": "patched source and instrumented release binary are hash-bound before frozen-input execution", "passed": True},
        {"requirement_id": "P3", "label": "the only pre-registration runtime smoke uses an unrelated three-qubit toy", "passed": True},
        {"requirement_id": "P4", "label": "native, ascending, and descending accumulation profiles are frozen", "passed": True},
        {"requirement_id": "P5", "label": "three OS processes and 256 traced calls are fixed", "passed": True},
        {"requirement_id": "P6", "label": "operation order and every f64 accumulation bit pattern are retained", "passed": True},
        {"requirement_id": "P7", "label": "trace-to-error and error-to-mapping association tests are frozen", "passed": True},
        {"requirement_id": "P8", "label": "all classifications remain admissible before execution", "passed": True},
        {"requirement_id": "P9", "label": "zero simulations, shots, sampling, candidate selection, and route changes are fixed", "passed": True},
        {"requirement_id": "P10", "label": "no confirmed bug, hardware, advantage, BQP, solved-frontier, or credit claim is allowed", "passed": True},
    ]
    payload = {
        "title": "B4/B8 R159 ErrorMap accumulation trace protocol",
        "version": 0,
        "method": METHOD,
        "status": "error_map_accumulation_trace_protocol_frozen_before_execution",
        "model_status": "source_instrumentation_frozen_without_frozen_input_execution",
        "source_target_id": "T-B4-002bz/T-B8-003cd/T-B10-009br",
        "upstream_target_id": "T-B4-002by/T-B8-003cc/T-B10-009bq",
        "protocol": protocol,
        "source_bindings": source_bindings,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": 10,
        "requirements_failed": 0,
        "execution_started": False,
        "claim_boundary": {
            "what_is_supported": "a source- and binary-bound native-versus-sorted ErrorMap accumulation experiment is ready for public preregistration",
            "what_is_not_supported": "any frozen-input result, causal mechanism, confirmed Qiskit bug, hardware relevance, advantage, BQP separation, solved frontier, or new credit",
        },
    }
    payload["payload_hash"] = canonical_hash(payload)
    return payload


def contract_payload(root: Path, protocol: dict[str, Any]) -> dict[str, Any]:
    bindings = dict(protocol["source_bindings"])
    bindings["protocol"] = payload_binding(root, PROTOCOL_PATH)
    contract = {
        "contract_id": "B4-B8-R159-error-map-accumulation-trace-contract-v0",
        "contract_status": "public_preregistration_execution_unopened",
        "target_id": "T-B4-002bz/T-B8-003cd/T-B10-009br",
        "upstream_target_id": "T-B4-002by/T-B8-003cc/T-B10-009bq",
        "source_bindings": bindings,
        "acceptance_conditions": [
            {"condition_id": "A1", "label": "all source, patch, build, binary, input, target, and R158 bindings remain exact"},
            {"condition_id": "A2", "label": "three post-registration process artifacts retain 256 traced calls"},
            {"condition_id": "A3", "label": "all calls use the frozen instrumented source, binary, and environment"},
            {"condition_id": "A4", "label": "native 128, ascending 64, and descending 64 calls complete without replacement"},
            {"condition_id": "A5", "label": "every call retains operation order, f64 accumulation, average bits, mapping, and row hash"},
            {"condition_id": "A6", "label": "profile summary and trace-to-mapping associations are emitted"},
            {"condition_id": "A7", "label": "all mapping and no-solution outcomes remain classified"},
            {"condition_id": "A8", "label": "native order-to-bits and bits-to-mapping tests are retained regardless of verdict"},
            {"condition_id": "A9", "label": "the two R157 mappings and exact tied score remain bound"},
            {"condition_id": "A10", "label": "forbidden bug, hardware, advantage, BQP, solved-frontier, and credit claims remain false"},
        ],
        "execution_started": False,
        "claim_boundary": protocol["claim_boundary"],
    }
    contract["payload_hash"] = canonical_hash(contract)
    return contract


def report_text(protocol: dict[str, Any], contract: dict[str, Any], build: dict[str, Any]) -> str:
    p = protocol["protocol"]
    return "\n".join([
        "# B4/B8 R159 ErrorMap Accumulation Trace Protocol",
        "",
        f"- Status: `{protocol['status']}`",
        f"- Source target: `{protocol['source_target_id']}`",
        f"- Profiles / processes / traced calls: `{p['profile_count']}` / `{p['total_process_count']}` / `{p['total_trace_replay_count']}`",
        f"- Base / patched source SHA-256: `{p['base_source_sha256']}` / `{p['patched_source_sha256']}`",
        f"- Instrumented binary SHA-256: `{p['instrumented_binary_sha256']}`",
        f"- Patch / build-manifest hashes: `{p['instrumentation_patch_sha256']}` / `{p['build_manifest_payload_hash']}`",
        f"- Contract payload hash: `{contract['payload_hash']}`",
        f"- Requirements passed/failed: `{protocol['requirements_passed']}` / `{protocol['requirements_failed']}`",
        "",
        "## Frozen Matrix",
        "",
        "| Profile | Operation order | Process count | Calls |",
        "|---|---|---:|---:|",
        *[f"| `{row['profile_id']}` | `{row['operation_order']}` | {row['process_count']} | {row['replay_count']} |" for row in p["profiles"]],
        "",
        "## Pre-registration Build Disclosure",
        "",
        f"The exact patch applies cleanly to Qiskit `{build['base_qiskit_commit']}`, passes cargo fmt checking, and produced the hash-bound release accelerator above. Three API-smoke calls used only `{build['build_checks']['smoke_backend']}` and a three-operation toy circuit; the frozen R157 input was not loaded.",
        "",
        "## Decision Rule",
        "",
        p["support_rule"] + ". All other preregistered classifications remain admissible.",
        "",
        "## Claim Boundary",
        "",
        "This protocol freezes an instrumented experiment only. It contains no frozen-input outcome and does not establish a causal mechanism, confirmed Qiskit bug, general compiler theorem, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze the R159 ErrorMap accumulation trace protocol.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--patched-source", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    outputs = [root / PROTOCOL_PATH, root / CONTRACT_PATH, root / REPORT_PATH, root / BUILD_MANIFEST_PATH]
    if any(path.exists() for path in outputs):
        raise ValueError("R159 protocol evidence already exists; refusing to overwrite")
    build = build_manifest(root, args.patched_source.resolve(), args.binary.resolve())
    write_json(root / BUILD_MANIFEST_PATH, build)
    protocol = protocol_payload(root, build)
    write_json(root / PROTOCOL_PATH, protocol)
    contract = contract_payload(root, protocol)
    write_json(root / CONTRACT_PATH, contract)
    (root / REPORT_PATH).write_text(report_text(protocol, contract, build), encoding="utf-8")
    print(json.dumps({
        "status": protocol["status"],
        "protocol_payload_hash": protocol["payload_hash"],
        "contract_payload_hash": contract["payload_hash"],
        "build_manifest_payload_hash": build["payload_hash"],
        "instrumented_binary_sha256": build["instrumented_binary"]["sha256"],
        "requirements_passed": protocol["requirements_passed"],
        "requirements_failed": protocol["requirements_failed"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
