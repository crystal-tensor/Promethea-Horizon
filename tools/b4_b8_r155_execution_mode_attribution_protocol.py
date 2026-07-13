#!/usr/bin/env python3
"""Freeze a 2x2 execution-mode attribution matrix for the R153 transient."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r128_transpiler_loop_layout_ranking import package_version


METHOD = "b4_b8_r155_execution_mode_attribution_protocol_v0"
R154_RESULT_PATH = "results/B4_B8_R154_deterministic_automatic_replay_v0.json"
R154_PROTOCOL_PATH = "results/B4_B8_R154_deterministic_automatic_replay_protocol_v0.json"
R154_CONTRACT_PATH = "benchmarks/B4_B8_R154_deterministic_automatic_replay_contract_v0.json"
R153_RESULT_PATH = "results/B4_B8_R153_independent_seed_replication_holdout_v0.json"
R153_TRIALS_PATH = "results/B4_B8_R153_independent_seed_replication_holdout/three_arm_trial_rows.json"
R153_REVEAL_PATH = "results/B4_B8_R153_independent_seed_replication_holdout/challenge_reveal.json"
R153_PROTOCOL_PATH = "results/B4_B8_R153_independent_seed_replication_protocol_v0.json"
R153_CONTRACT_PATH = "benchmarks/B4_B8_R153_independent_seed_replication_contract_v0.json"
R152_DESIGN_PATH = "results/B4_B8_R152_edge_signature_expansion_design_v0.json"
R150_DESIGN_PATH = "results/B4_B8_R150_unseen_backend_candidate_generation_design_v0.json"
RESULT_PATH = "results/B4_B8_R155_execution_mode_attribution_protocol_v0.json"
REPORT_PATH = "research/B4_B8_R155_execution_mode_attribution_protocol.md"
CONTRACT_PATH = "benchmarks/B4_B8_R155_execution_mode_attribution_contract_v0.json"


def canonical_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def source_binding(root: Path, path: str, payload: dict | None = None) -> dict:
    binding = {"path": path, "sha256": file_sha256(root / path)}
    if payload is not None:
        binding["payload_hash"] = payload["payload_hash"]
    return binding


def environment(thread_count: int) -> dict[str, str]:
    return {
        "PYTHONHASHSEED": "0",
        "RAYON_NUM_THREADS": str(thread_count),
        "OMP_NUM_THREADS": str(thread_count),
        "OPENBLAS_NUM_THREADS": str(thread_count),
        "MKL_NUM_THREADS": str(thread_count),
        "QISKIT_PARALLEL": "FALSE",
    }


def build(root: Path) -> tuple[dict, dict]:
    payloads = {
        "r154_result": json.loads((root / R154_RESULT_PATH).read_text()),
        "r154_protocol": json.loads((root / R154_PROTOCOL_PATH).read_text()),
        "r153_result": json.loads((root / R153_RESULT_PATH).read_text()),
        "r153_protocol": json.loads((root / R153_PROTOCOL_PATH).read_text()),
        "r152_design": json.loads((root / R152_DESIGN_PATH).read_text()),
        "r150_design": json.loads((root / R150_DESIGN_PATH).read_text()),
    }
    r153_trials = json.loads((root / R153_TRIALS_PATH).read_text())
    r153_reveal = json.loads((root / R153_REVEAL_PATH).read_text())
    source_paths = {
        "r154_result": R154_RESULT_PATH,
        "r154_protocol": R154_PROTOCOL_PATH,
        "r154_contract": R154_CONTRACT_PATH,
        "r153_result": R153_RESULT_PATH,
        "r153_trials": R153_TRIALS_PATH,
        "r153_reveal": R153_REVEAL_PATH,
        "r153_protocol": R153_PROTOCOL_PATH,
        "r153_contract": R153_CONTRACT_PATH,
        "r152_design": R152_DESIGN_PATH,
        "r150_design": R150_DESIGN_PATH,
    }
    source_bindings = {
        key: source_binding(root, path, payloads.get(key))
        for key, path in source_paths.items()
    }
    profiles = [
        {
            "profile_id": "clamped_serial",
            "thread_environment": environment(1),
            "aer_option_mode": "explicit_serial",
            "aer_simulator_options": {
                "max_parallel_threads": 1,
                "max_parallel_experiments": 1,
                "max_parallel_shots": 1,
            },
            "interpretation": "R154 replacement-replay control",
        },
        {
            "profile_id": "clamped_default_aer",
            "thread_environment": environment(1),
            "aer_option_mode": "no_explicit_parallel_override",
            "documented_aer_defaults": {
                "max_parallel_threads": 0,
                "max_parallel_experiments": 1,
                "max_parallel_shots": 0,
            },
            "interpretation": "R153 code-equivalent Aer option path",
        },
        {
            "profile_id": "four_thread_serial",
            "thread_environment": environment(4),
            "aer_option_mode": "explicit_serial",
            "aer_simulator_options": {
                "max_parallel_threads": 1,
                "max_parallel_experiments": 1,
                "max_parallel_shots": 1,
            },
            "interpretation": "thread-environment stress with serial Aer execution",
        },
        {
            "profile_id": "four_thread_default_aer",
            "thread_environment": environment(4),
            "aer_option_mode": "no_explicit_parallel_override",
            "documented_aer_defaults": {
                "max_parallel_threads": 0,
                "max_parallel_experiments": 1,
                "max_parallel_shots": 0,
            },
            "interpretation": "thread-environment and default-Aer interaction stress",
        },
    ]
    protocol = {
        "research_question": "Can the R153 transient be attributed to explicit Aer serialization, process thread clamps, their interaction, or neither?",
        "snapshot_names": ["FakeCasablancaV2", "FakeNairobiV2", "FakePerth"],
        "task_id": "dense_validation_xy_network_n6",
        "source_trial_row_count": 96,
        "profile_count": 4,
        "replicate_process_count_per_profile": 2,
        "total_process_count": 8,
        "row_count_per_process": 96,
        "total_row_execution_count": 768,
        "circuit_execution_count_per_process": 288,
        "total_circuit_execution_count": 2304,
        "shots_per_execution": 2048,
        "total_simulated_shots": 4718592,
        "profiles": profiles,
        "seed_rule": "replay only the 96 publicly revealed R153 transpiler and simulator seed pairs",
        "route_rule": "reuse the R153 repaired and denominator routes without selection or modification",
        "process_rule": "each profile replicate executes in a distinct operating-system process after public preregistration",
        "comparison_rule": "hash automatic OpenQASM 3, three canonical arm-count vectors, and one canonical scientific row for every source row",
        "within_profile_comparison_count": 4,
        "serial_reference_comparison_count": 7,
        "r153_stored_row_comparison_count": 8,
        "within_profile_qasm_comparison_count": 384,
        "within_profile_arm_count_comparison_count": 1152,
        "within_profile_scientific_row_comparison_count": 384,
        "serial_reference_qasm_comparison_count": 672,
        "serial_reference_arm_count_comparison_count": 2016,
        "serial_reference_scientific_row_comparison_count": 672,
        "r153_stored_scientific_row_comparison_count": 768,
        "classification_rule": {
            "explicit_aer_serialization_effect": "compare clamped_default_aer against clamped_serial",
            "thread_environment_effect": "compare four_thread_serial against clamped_serial",
            "interaction_effect": "compare four_thread_default_aer against all other profile cells",
            "transient_not_reproduced": "all seven process outputs match the clamped_serial reference and all eight processes match stored R153 core rows",
        },
        "official_aer_options_reference": "https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html",
        "frozen_software": {
            "python": platform.python_version(),
            "qiskit": package_version("qiskit"),
            "qiskit_aer": package_version("qiskit-aer"),
            "qiskit_ibm_runtime": package_version("qiskit-ibm-runtime"),
        },
        "new_hidden_seed_count": 0,
        "candidate_selection_performed": False,
        "route_change_performed": False,
    }
    requirements = [
        {"requirement_id": "R1", "label": "R154 and R153 evidence plus route sources are hash-bound", "passed": payloads["r154_result"]["summary"]["global_acceptance"] is True and payloads["r153_result"]["summary"]["global_acceptance"] is True},
        {"requirement_id": "R2", "label": "the 96 public R153 rows and reveal are exact", "passed": len(r153_trials) == 96 and r153_reveal["commitment_matches"] is True},
        {"requirement_id": "R3", "label": "the 2x2 matrix fixes four profiles and two process replicates per profile", "passed": len(profiles) == 4 and protocol["total_process_count"] == 8},
        {"requirement_id": "R4", "label": "the matrix fixes 768 rows and 2304 circuit executions", "passed": protocol["total_row_execution_count"] == 768 and protocol["total_circuit_execution_count"] == 2304},
        {"requirement_id": "R5", "label": "all within-profile hash comparisons are enumerated", "passed": protocol["within_profile_arm_count_comparison_count"] == 1152},
        {"requirement_id": "R6", "label": "all serial-reference hash comparisons are enumerated", "passed": protocol["serial_reference_arm_count_comparison_count"] == 2016},
        {"requirement_id": "R7", "label": "all process outputs are compared with stored R153 core rows", "passed": protocol["r153_stored_scientific_row_comparison_count"] == 768},
        {"requirement_id": "R8", "label": "software, process environments, Aer modes, and classification rules are frozen", "passed": all(protocol["frozen_software"].values()) and len(protocol["classification_rule"]) == 4},
        {"requirement_id": "R9", "label": "no hidden seed, candidate selection, or route change is introduced", "passed": protocol["new_hidden_seed_count"] == 0 and protocol["candidate_selection_performed"] is False and protocol["route_change_performed"] is False},
        {"requirement_id": "R10", "label": "diagnostic completion is separated from determinism and scientific-credit claims", "passed": True},
    ]
    claim_boundary = {
        "what_is_supported": "an immutable diagnostic of whether execution-mode choices reproduce or localize the public R153 transient",
        "what_is_not_supported": "causal attribution before execution, new hidden statistical evidence, temporal or real-device transfer, hardware performance, general route-generation advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
    }
    payload = {
        "title": "B4/B8 R155 execution-mode attribution protocol",
        "version": 0,
        "method": METHOD,
        "status": "execution_mode_attribution_protocol_frozen_before_execution",
        "model_status": "r153_transient_2x2_execution_mode_diagnostic_unopened",
        "generated_at_unix": int(time.time()),
        "source_target_id": "T-B4-002br/T-B8-003bv/T-B10-009bj",
        "upstream_target_id": "T-B4-002bq/T-B8-003bu/T-B10-009bi",
        "source_bindings": source_bindings,
        "protocol": protocol,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [row["requirement_id"] for row in requirements if not row["passed"]],
        "execution_started": False,
        "claim_boundary": claim_boundary,
    }
    payload["payload_hash"] = canonical_hash(payload)
    contract = {
        "contract_id": "B4-B8-R155-execution-mode-attribution-contract-v0",
        "contract_status": "public_preregistration_execution_unopened",
        "target_id": payload["source_target_id"],
        "upstream_target_id": payload["upstream_target_id"],
        "research_question": protocol["research_question"],
        "source_bindings": {
            "protocol_path": RESULT_PATH,
            "protocol_payload_hash": payload["payload_hash"],
            "protocol_sha256": None,
            **source_bindings,
        },
        "execution_protocol": protocol,
        "acceptance_conditions": [
            {"condition_id": "A1", "condition": "contract, protocol, R154/R153 evidence, seeds, routes, and source hashes remain exact"},
            {"condition_id": "A2", "condition": "eight distinct processes complete 768 rows, 2304 circuits, and 4,718,592 shots"},
            {"condition_id": "A3", "condition": "each process emits 96 complete rows plus environment, target, route, and process identity manifests"},
            {"condition_id": "A4", "condition": "four within-profile replicate comparisons record every QASM, arm-count, and scientific-row match or mismatch"},
            {"condition_id": "A5", "condition": "seven serial-reference comparisons record every QASM, arm-count, and scientific-row match or mismatch"},
            {"condition_id": "A6", "condition": "all eight processes compare 96 core scientific rows against stored R153 evidence"},
            {"condition_id": "A7", "condition": "the clamped-default-Aer cell emits an explicit R153-code-path classification"},
            {"condition_id": "A8", "condition": "the full 2x2 matrix emits explicit Aer, thread-environment, interaction, and non-reproduction classifications"},
            {"condition_id": "A9", "condition": "all process artifacts, comparisons, classifications, and transcript bindings are complete and replayable"},
            {"condition_id": "A10", "condition": "no new seed, selection, route change, hidden evidence, hardware, transfer, advantage, BQP, solved-frontier, or credit claim occurs"},
        ],
        "claim_boundary": claim_boundary,
    }
    return payload, contract


def report(payload: dict, contract_sha256: str) -> str:
    protocol = payload["protocol"]
    profile_lines = "\n".join(
        f"- `{row['profile_id']}`: {row['interpretation']}; environment threads `{row['thread_environment']['OMP_NUM_THREADS']}`; Aer mode `{row['aer_option_mode']}`."
        for row in protocol["profiles"]
    )
    return f"""# B4/B8 R155 Execution-Mode Attribution Protocol

- Profiles / process replicates / total processes: `{protocol['profile_count']}` / `{protocol['replicate_process_count_per_profile']}` / `{protocol['total_process_count']}`
- Rows / circuit executions / shots: `{protocol['total_row_execution_count']}` / `{protocol['total_circuit_execution_count']}` / `{protocol['total_simulated_shots']}`
- Within-profile comparisons: `{protocol['within_profile_comparison_count']}`
- Serial-reference comparisons: `{protocol['serial_reference_comparison_count']}`
- Stored-R153 row comparisons: `{protocol['r153_stored_scientific_row_comparison_count']}`
- New hidden seeds / selection / route changes: `0` / `false` / `false`
- Contract SHA-256: `{contract_sha256}`
- Execution started: `false`

## Frozen 2x2 Matrix

{profile_lines}

R155 separates process thread clamps from explicit Aer serialization. Every
cell runs twice in separate operating-system processes and hashes every fresh
automatic OpenQASM 3 circuit, all three count vectors, and every scientific
row. Diagnostic completion does not require zero mismatch: a mismatch is valid
evidence if it is complete, bound to the frozen cell, and reproduced honestly.

This unopened protocol makes no causal attribution and introduces no hidden
statistical evidence. It does not support temporal or real-device transfer,
hardware performance, general route-generation advantage, quantum advantage,
BQP separation, a solved frontier, or new credit.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    payload, contract = build(root)
    write_json(root / RESULT_PATH, payload)
    contract["source_bindings"]["protocol_sha256"] = file_sha256(root / RESULT_PATH)
    write_json(root / CONTRACT_PATH, contract)
    contract_sha256 = file_sha256(root / CONTRACT_PATH)
    (root / REPORT_PATH).write_text(report(payload, contract_sha256), encoding="utf-8")
    print(json.dumps({"protocol": payload["protocol"], "contract_sha256": contract_sha256}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
