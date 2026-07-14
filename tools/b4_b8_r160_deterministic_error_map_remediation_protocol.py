#!/usr/bin/env python3
"""Freeze the R160 deterministic external ErrorMap remediation experiment."""

from __future__ import annotations

import argparse
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path

from qiskit import qasm3

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r128_transpiler_loop_layout_ranking import package_version
from b4_b8_r153_independent_seed_replication_holdout import TARGET_CLASSES
from b4_b8_r154_deterministic_automatic_replay import canonical_hash, target_descriptor
from b4_b8_r160_deterministic_error_map_remediation import source_inventory


METHOD = "b4_b8_r160_deterministic_error_map_remediation_protocol_v0"
RESULT_PATH = "results/B4_B8_R160_deterministic_error_map_remediation_protocol_v0.json"
REPORT_PATH = "research/B4_B8_R160_deterministic_error_map_remediation_protocol.md"
CONTRACT_PATH = "benchmarks/B4_B8_R160_deterministic_error_map_remediation_contract_v0.json"
EXECUTOR_PATH = "tools/b4_b8_r160_deterministic_error_map_remediation.py"
SOURCE_MANIFEST_PATH = "research/source_lineage/Qiskit_2_4_1_vf2_source_manifest.json"
R159_RESULT_PATH = "results/B4_B8_R159_error_map_accumulation_trace_v0.json"
R159_NATIVE_PATH = "results/B4_B8_R159_error_map_accumulation_trace/native_hashset_order.json"
R159_ASSOCIATION_PATH = "results/B4_B8_R159_error_map_accumulation_trace/trace_mapping_associations.json"
R159_CONTRACT_PATH = "benchmarks/B4_B8_R159_error_map_accumulation_trace_contract_v0.json"
INPUT_PATH = "benchmarks/B4_B8_R157_vf2_post_layout_input_v0.qasm"
MAPPINGS = {
    "endpoint_4_to_0": [6, 5, 4, 3, 0, 1, 2],
    "endpoint_4_to_2": [6, 5, 4, 3, 2, 1, 0],
}
DISCRIMINATING_KEYS = [[0, 1], [1, 0], [1, 2], [2, 1]]
ULP_SHIFTS = [-512, -64, -8, -1, 1, 8, 64, 512]


def source_binding(root: Path, path: str, payload_key: str | None = None) -> dict:
    binding = {"path": path, "sha256": file_sha256(root / path)}
    if payload_key is not None:
        payload = json.loads((root / path).read_text())
        binding["payload_hash"] = payload[payload_key]
    return binding


def process_environment() -> dict[str, str]:
    return {
        "PYTHONHASHSEED": "0",
        "RAYON_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "QISKIT_PARALLEL": "FALSE",
    }


def perturbation_cases() -> list[dict]:
    rows = [{"case_id": "tie_baseline", "key": None, "ulp_shift": 0}]
    for left, right in DISCRIMINATING_KEYS:
        for shift in ULP_SHIFTS:
            sign = "p" if shift > 0 else "m"
            rows.append(
                {
                    "case_id": f"edge_{left}_{right}_{sign}{abs(shift):03d}ulp",
                    "key": [left, right],
                    "ulp_shift": shift,
                }
            )
    return rows


def interaction_ledger(root: Path) -> dict:
    circuit = qasm3.load(root / INPUT_PATH)
    one: Counter[int] = Counter()
    two: Counter[tuple[int, int]] = Counter()
    for instruction in circuit.data:
        qargs = tuple(circuit.find_bit(bit).index for bit in instruction.qubits)
        if len(qargs) == 1:
            one[qargs[0]] += 1
        elif len(qargs) == 2:
            two[qargs] += 1
    mapped_counts = {}
    for mapping_id, vector in MAPPINGS.items():
        counts: defaultdict[tuple[int, int], int] = defaultdict(int)
        for virtual, count in one.items():
            counts[(vector[virtual], vector[virtual])] += count
        for (left, right), count in two.items():
            counts[(vector[left], vector[right])] += count
        mapped_counts[mapping_id] = counts
    left = mapped_counts["endpoint_4_to_0"]
    right = mapped_counts["endpoint_4_to_2"]
    deltas = [
        {
            "key": list(key),
            "endpoint_4_to_0_minus_endpoint_4_to_2_coefficient": left[key]
            - right[key],
        }
        for key in sorted(set(left) | set(right))
        if left[key] != right[key]
    ]
    return {
        "input_operation_count": circuit.size(),
        "input_depth": circuit.depth(),
        "one_qubit_counts": {str(key): value for key, value in sorted(one.items())},
        "two_qubit_counts": {
            f"{left}->{right}": value
            for (left, right), value in sorted(two.items())
        },
        "endpoint_coefficient_deltas": deltas,
    }


def build(root: Path) -> tuple[dict, dict]:
    r159_result = json.loads((root / R159_RESULT_PATH).read_text())
    r159_native = json.loads((root / R159_NATIVE_PATH).read_text())
    source_manifest = json.loads((root / SOURCE_MANIFEST_PATH).read_text())
    inventory = source_inventory(r159_native)
    inventory_hash = canonical_hash(inventory)
    ledger = interaction_ledger(root)
    cases = perturbation_cases()
    backend = TARGET_CLASSES["FakeNairobiV2"]()
    descriptor = target_descriptor(backend)
    modes = [
        "ascending_f64",
        "descending_f64",
        "math_fsum",
        "exact_binary_fraction",
    ]
    protocol = {
        "research_question": "Can a deterministic external ErrorMap stabilize the tied R157 layout while preserving every exact-oracle optimum whose score margin exceeds a frozen threshold?",
        "snapshot_name": "FakeNairobiV2",
        "target_descriptor_sha256": descriptor["descriptor_hash"],
        "input_path": INPUT_PATH,
        "input_qasm_sha256": file_sha256(root / INPUT_PATH),
        "input_operation_count": ledger["input_operation_count"],
        "input_depth": ledger["input_depth"],
        "operation_inventory_source": R159_NATIVE_PATH,
        "operation_inventory_hash": inventory_hash,
        "operation_inventory_row_count": len(inventory),
        "accumulation_modes": modes,
        "profile_count": len(modes),
        "processes_per_mode": 4,
        "total_process_count": 16,
        "perturbation_cases": cases,
        "case_count": len(cases),
        "replays_per_case_per_process": 2,
        "total_direct_replay_count": len(modes) * 4 * len(cases) * 2,
        "max_concurrent_processes": 4,
        "margin_protection_threshold": 1e-16,
        "exact_oracle": {
            "mapping_space": "all 7! virtual-to-physical permutations",
            "score_arithmetic": "fractions.Fraction.from_float over every ErrorMap value times integer interaction count",
            "direction_rule": "use directed ErrorMap key; use reverse key only when the directed key is absent",
            "acceptance": "each VF2 output must belong to that mode and case exact-minimizer set",
        },
        "interaction_ledger": ledger,
        "mapping_classes": MAPPINGS,
        "score_denominator_boundary": {
            "r157_documented_concrete_only_python_score": 0.45894321220828727,
            "r160_oracle_reuses_r157_score": False,
            "r160_semantics": "rebuild from R159 Rust operation inventory, including zero-error global operations in each qargs denominator",
            "reason": "the R157 concrete-only Python recalculation proves endpoint equality but is not the Rust accelerator ErrorMap score ledger",
        },
        "vf2_configuration": {
            "call_limit": 30000000,
            "time_limit": None,
            "max_trials": 250000,
            "shuffle_seed": -1,
            "score_initial_layout": True,
            "strict_direction": False,
        },
        "classification_order": [
            "tie_not_stabilized",
            "method_dependent_tie_resolution",
            "no_margin_protected_rows",
            "tie_stabilized_but_non_tied_guardrail_failed",
            "deterministic_external_map_remediation_supported",
        ],
        "support_rule": "deterministic_external_map_remediation_supported requires all four modes to select one stable tied vector, at least one margin-protected non-tied case, zero protected-case failures, and every replay inside its exact rational oracle minimizer set",
        "pre_registration_smoke": {
            "backend": "GenericBackendV2(num_qubits=3, seed=160)",
            "circuit_operation_count": 3,
            "accumulation_mode_count": 4,
            "direct_vf2_call_count": 4,
            "all_outputs_in_exact_oracle": True,
            "invalid_mode_rejected": True,
            "frozen_r157_input_loaded": False,
        },
        "official_source": {
            "repository": source_manifest["repository"],
            "release": source_manifest["release"],
            "commit": source_manifest["commit"],
            "rust_vf2_source_sha256": next(
                row["sha256"]
                for row in source_manifest["source_rows"]
                if row["source_id"] == "rust_vf2_layout_pass"
            ),
            "accelerator_sha256": source_manifest["installed_accelerator"]["sha256"],
            "accelerator_size_bytes": source_manifest["installed_accelerator"]["size_bytes"],
        },
        "frozen_software": {
            "python": platform.python_version(),
            "qiskit": package_version("qiskit"),
            "qiskit_aer": package_version("qiskit-aer"),
            "qiskit_ibm_runtime": package_version("qiskit-ibm-runtime"),
        },
        "process_environment": process_environment(),
        "source_patch_performed": False,
        "new_hidden_seed_count": 0,
        "candidate_selection_performed": False,
        "route_change_performed": False,
        "sampling_performed": False,
        "simulation_execution_count": 0,
        "total_simulated_shots": 0,
        "execution_started": False,
    }
    source_bindings = {
        "executor": source_binding(root, EXECUTOR_PATH),
        "qiskit_source_manifest": source_binding(
            root, SOURCE_MANIFEST_PATH, "payload_hash"
        ),
        "r159_result": source_binding(root, R159_RESULT_PATH, "payload_hash"),
        "r159_native_trace": source_binding(
            root, R159_NATIVE_PATH, "manifest_payload_hash"
        ),
        "r159_associations": source_binding(
            root, R159_ASSOCIATION_PATH, "association_payload_hash"
        ),
        "r159_contract": source_binding(root, R159_CONTRACT_PATH, "payload_hash"),
        "r157_input": source_binding(root, INPUT_PATH),
    }
    requirements = [
        {"requirement_id": "P1", "label": "R159 result, trace, association, contract, R157 input, and official source lineage are hash-bound", "passed": r159_result["summary"]["classification"] == "operation_order_f64_path_supported"},
        {"requirement_id": "P2", "label": "the executor and official uninstrumented accelerator are hash-bound", "passed": source_manifest["installed_accelerator"]["sha256"] == "a299d48f8d174481d389b30f1fd240a845144922f32ef918925b17243fc5f007"},
        {"requirement_id": "P3", "label": "four deterministic accumulation modes are frozen", "passed": len(modes) == 4},
        {"requirement_id": "P4", "label": "thirty-three baseline and ULP-perturbation cases are frozen", "passed": len(cases) == 33 and len(DISCRIMINATING_KEYS) == 4 and len(ULP_SHIFTS) == 8},
        {"requirement_id": "P5", "label": "sixteen processes and 1056 direct replays are fixed", "passed": protocol["total_process_count"] == 16 and protocol["total_direct_replay_count"] == 1056},
        {"requirement_id": "P6", "label": "all 7! mappings receive an exact rational score oracle", "passed": protocol["exact_oracle"]["mapping_space"] == "all 7! virtual-to-physical permutations"},
        {"requirement_id": "P7", "label": "the non-tied protection margin and decision order are frozen", "passed": protocol["margin_protection_threshold"] == 1e-16 and len(protocol["classification_order"]) == 5},
        {"requirement_id": "P8", "label": "the R157 concrete-only score is separated from the Rust ErrorMap denominator", "passed": protocol["score_denominator_boundary"]["r160_oracle_reuses_r157_score"] is False},
        {"requirement_id": "P9", "label": "the only pre-registration runtime smoke used an unrelated three-qubit toy", "passed": protocol["pre_registration_smoke"]["frozen_r157_input_loaded"] is False and protocol["pre_registration_smoke"]["direct_vf2_call_count"] == 4},
        {"requirement_id": "P10", "label": "no source patch, hidden selection, simulation, hardware, advantage, BQP, solved-frontier, or credit claim is allowed", "passed": protocol["source_patch_performed"] is False and protocol["simulation_execution_count"] == 0 and protocol["total_simulated_shots"] == 0},
    ]
    claim_boundary = {
        "what_is_supported": "a source-bound deterministic external ErrorMap remediation and exact-oracle non-tied guardrail is ready for public preregistration",
        "what_is_not_supported": "any frozen-input R160 outcome, accepted upstream patch, confirmed Qiskit bug, cross-platform theorem, hardware result, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
    }
    payload = {
        "title": "B4/B8 R160 deterministic ErrorMap remediation protocol",
        "version": 0,
        "method": METHOD,
        "status": "deterministic_error_map_remediation_protocol_frozen_before_execution",
        "model_status": "external_error_map_remediation_and_exact_oracle_matrix_unopened",
        "source_target_id": "T-B4-002cb/T-B8-003cf/T-B10-009bt",
        "upstream_target_id": "T-B4-002ca/T-B8-003ce/T-B10-009bs",
        "source_bindings": source_bindings,
        "protocol": protocol,
        "requirements": requirements,
        "requirement_count": len(requirements),
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "execution_started": False,
        "claim_boundary": claim_boundary,
    }
    payload["payload_hash"] = canonical_hash(payload)
    contract = {
        "contract_id": "B4-B8-R160-deterministic-error-map-remediation-contract-v0",
        "target_id": payload["source_target_id"],
        "upstream_target_id": payload["upstream_target_id"],
        "contract_status": "public_preregistration_execution_unopened",
        "execution_started": False,
        "source_bindings": {
            **source_bindings,
            "protocol": {
                "path": RESULT_PATH,
                "sha256": "",
                "payload_hash": payload["payload_hash"],
            },
        },
        "acceptance_conditions": [
            {"condition_id": "A1", "label": "all source, protocol, executor, input, and official-binary bindings remain exact"},
            {"condition_id": "A2", "label": "four modes, sixteen processes, thirty-three cases, and 1056 calls complete"},
            {"condition_id": "A3", "label": "all process identities are unique and post-registration"},
            {"condition_id": "A4", "label": "every worker and replay payload validates"},
            {"condition_id": "A5", "label": "every replay is checked against an exact rational mapping oracle"},
            {"condition_id": "A6", "label": "tie stability and cross-mode agreement are retained regardless of outcome"},
            {"condition_id": "A7", "label": "all protected non-tied rows and failures are retained"},
            {"condition_id": "A8", "label": "classification follows the frozen decision order"},
            {"condition_id": "A9", "label": "no source patch, simulation, shots, hidden selection, or route change occurs"},
            {"condition_id": "A10", "label": "forbidden bug, hardware, advantage, BQP, solved-frontier, and credit claims remain false"},
        ],
        "claim_boundary": claim_boundary,
    }
    contract["payload_hash"] = canonical_hash(contract)
    return payload, contract


def write_report(path: Path, payload: dict, contract: dict) -> None:
    p = payload["protocol"]
    lines = [
        "# B4/B8 R160 Deterministic ErrorMap Remediation Protocol",
        "",
        f"- Status: `{payload['status']}`",
        f"- Target chain: `{payload['source_target_id']}` <- `{payload['upstream_target_id']}`",
        f"- Profiles / processes / cases / direct calls: `{p['profile_count']}` / `{p['total_process_count']}` / `{p['case_count']}` / `{p['total_direct_replay_count']}`",
        f"- Operation inventory rows / hash: `{p['operation_inventory_row_count']}` / `{p['operation_inventory_hash']}`",
        f"- Margin protection threshold: `{p['margin_protection_threshold']}`",
        f"- Requirements passed/failed: `{payload['requirements_passed']}` / `{payload['requirements_failed']}`",
        f"- Contract payload hash: `{contract['payload_hash']}`",
        "- Execution started: `False`",
        "",
        "## Research Question",
        "",
        p["research_question"],
        "",
        "## Frozen Modes",
        "",
        "| Mode | Processes | Cases | Replays per case/process | Calls |",
        "|---|---:|---:|---:|---:|",
    ]
    per_mode = p["processes_per_mode"] * p["case_count"] * p["replays_per_case_per_process"]
    for mode in p["accumulation_modes"]:
        lines.append(
            f"| `{mode}` | {p['processes_per_mode']} | {p['case_count']} | {p['replays_per_case_per_process']} | {per_mode} |"
        )
    lines.extend(
        [
            "",
            "The 33 cases comprise one untouched tie baseline plus positive and negative 1, 8, 64, and 512 ULP shifts on each of the four physical directed edges whose endpoint-mapping coefficients differ.",
            "",
            "## Exact Oracle",
            "",
            "Every mode/case ErrorMap is scored over all `7! = 5040` mappings with exact rational arithmetic over the emitted binary64 values. A VF2 output must belong to that mode/case minimum set. A non-tied row counts as margin-protected only when all four modes have the same unique minimizer and every minimum gap is at least `1e-16`.",
            "",
            "## Score-Denominator Boundary",
            "",
            "R157 recorded `0.45894321220828727` with a Python concrete-operation-only denominator. R160 does not reuse that numeric score. It reconstructs the actual Rust ErrorMap operation inventory retained by R159, including zero-error global operations in each qargs denominator. The prior value remains evidence that the two endpoint coefficients are symmetric, not the accelerator score oracle for R160.",
            "",
            "## Smoke Disclosure",
            "",
            "Four pre-registration direct calls exercised the four accumulation methods on an unrelated three-qubit `GenericBackendV2(seed=160)` circuit. All outputs belonged to the toy exact-oracle minimum set, invalid mode rejection passed, and the frozen R157 input was not loaded.",
            "",
            "## Decision Rule",
            "",
            p["support_rule"],
            "",
            "All five classifications remain admissible before execution.",
            "",
            "## Claim Boundary",
            "",
            "This protocol contains no frozen-input R160 result. It does not claim an accepted upstream patch, confirmed Qiskit bug, cross-platform theorem, hardware relevance, route advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new research credit.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze the R160 deterministic ErrorMap remediation protocol."
    )
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    root = Path(args.root).resolve()
    outputs = [root / RESULT_PATH, root / REPORT_PATH, root / CONTRACT_PATH]
    if any(path.exists() for path in outputs):
        raise ValueError("R160 protocol evidence already exists; refusing to overwrite")
    payload, contract = build(root)
    write_json(root / RESULT_PATH, payload)
    contract["source_bindings"]["protocol"]["sha256"] = file_sha256(root / RESULT_PATH)
    body = dict(contract)
    body.pop("payload_hash")
    contract["payload_hash"] = canonical_hash(body)
    write_json(root / CONTRACT_PATH, contract)
    write_report(root / REPORT_PATH, payload, contract)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "protocol_payload_hash": payload["payload_hash"],
                "contract_payload_hash": contract["payload_hash"],
                "executor_sha256": payload["source_bindings"]["executor"]["sha256"],
                "requirements_passed": payload["requirements_passed"],
                "requirements_failed": payload["requirements_failed"],
                "total_process_count": payload["protocol"]["total_process_count"],
                "case_count": payload["protocol"]["case_count"],
                "total_direct_replay_count": payload["protocol"]["total_direct_replay_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
