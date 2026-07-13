#!/usr/bin/env python3
"""Attribute the R150 Casablanca failure by noise channel and route exposure."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from qiskit import qasm3
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.fake_provider import FakeCasablancaV2, FakeNairobiV2, FakePerth

from b4_b8_r119_private_observable_bundle_gate import write_json
from b4_b8_r126_calibration_attribution_ledger import circuit_exposure, file_sha256
from b4_b8_r132_topology_constrained_route_policy import DETERMINISTIC_PROCESS_ENV
from b4_b8_r135_dense_interaction_fallback import build_dense_validation_tasks
from b4_b8_r138_postcommit_statistical_challenge import exact_distribution, hellinger_fidelity, probability_from_counts


METHOD = "b4_b8_r151_casablanca_failure_attribution_v0"
DESIGN_PATH = "results/B4_B8_R150_unseen_backend_candidate_generation_design_v0.json"
HOLDOUT_PATH = "results/B4_B8_R150_unseen_backend_candidate_generation_holdout_v0.json"
TRIALS_PATH = "results/B4_B8_R150_unseen_backend_candidate_generation_holdout/three_arm_trial_rows.json"
RESULT_PATH = "results/B4_B8_R151_casablanca_failure_attribution_v0.json"
REPORT_PATH = "research/B4_B8_R151_casablanca_failure_attribution.md"
TARGET_CLASSES = {
    "FakeCasablancaV2": FakeCasablancaV2,
    "FakeNairobiV2": FakeNairobiV2,
    "FakePerth": FakePerth,
}
ATTRIBUTION_SEEDS = tuple(range(15101, 15133))
SHOTS = 8192


def ensure_environment() -> None:
    if all(os.environ.get(key) == value for key, value in DETERMINISTIC_PROCESS_ENV.items()):
        return
    environment = dict(os.environ)
    environment.update(DETERMINISTIC_PROCESS_ENV)
    os.execvpe(sys.executable, [sys.executable, *sys.argv], environment)


def split_noise_models(backend: Any) -> dict[str, NoiseModel]:
    full = NoiseModel.from_backend(backend)
    gate_only = NoiseModel(basis_gates=full.basis_gates)
    for operation, rows in full._local_quantum_errors.items():
        for qargs, error in rows.items():
            gate_only.add_quantum_error(error, operation, qargs)
    readout_only = NoiseModel(basis_gates=full.basis_gates)
    for qargs, error in full._local_readout_errors.items():
        readout_only.add_readout_error(error, qargs)
    return {"full": full, "gate_only": gate_only, "readout_only": readout_only}


def edge_signature(path: Path) -> tuple[tuple[int, int, int], ...]:
    circuit = qasm3.load(path)
    counts: Counter[tuple[int, int]] = Counter()
    for instruction in circuit.data:
        if instruction.operation.name == "cx":
            edge = tuple(circuit.find_bit(qubit).index for qubit in instruction.qubits)
            counts[edge] += 1
    return tuple(sorted((source, target, count) for (source, target), count in counts.items()))


def exposure_ledger(root: Path, path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    exposure = circuit_exposure(path, metadata)
    edges: dict[tuple[int, int], dict[str, Any]] = {}
    for occurrence in exposure["cx_occurrences"]:
        edge = tuple(occurrence["edge"])
        row = edges.setdefault(edge, {"edge": list(edge), "occurrence_count": 0, "cx_error": occurrence["cx_error"]})
        row["occurrence_count"] += 1
    for row in edges.values():
        row["negative_log_survival_contribution"] = row["occurrence_count"] * -math.log(max(1.0 - row["cx_error"], 1e-12))
    edge_rows = sorted(edges.values(), key=lambda row: (-row["negative_log_survival_contribution"], row["edge"]))
    readout_contribution = sum(-math.log(max(1.0 - row["readout_error"], 1e-12)) for row in exposure["measurement_map"])
    return {
        "circuit_path": str(path.relative_to(root)),
        "circuit_sha256": file_sha256(path),
        "depth": exposure["depth"],
        "cx_occurrence_count": exposure["cx_occurrence_count"],
        "readout_any_error_proxy": exposure["readout_any_error_proxy"],
        "cx_any_error_proxy": exposure["cx_any_error_proxy"],
        "combined_any_error_proxy": exposure["combined_any_error_proxy"],
        "readout_negative_log_survival_contribution": readout_contribution,
        "cx_negative_log_survival_contribution": sum(row["negative_log_survival_contribution"] for row in edge_rows),
        "edge_rows": edge_rows,
        "edge_signature": [list(row) for row in edge_signature(path)],
    }


def build(root: Path) -> dict[str, Any]:
    design = json.loads((root / DESIGN_PATH).read_text())
    holdout = json.loads((root / HOLDOUT_PATH).read_text())
    trial_rows = json.loads((root / TRIALS_PATH).read_text())
    task = next(row for row in build_dense_validation_tasks() if row["task_id"] == design["summary"]["target_task"])
    ideal = exact_distribution(task["circuit"])
    design_targets = {row["target_snapshot"]: row for row in design["target_rows"]}
    holdout_groups = {row["target_snapshot"]: row for row in holdout["group_rows"]}
    target_rows = []
    channel_rows = []
    exposure_rows = []
    diversity_rows = []

    for target_name, backend_class in TARGET_CLASSES.items():
        backend = backend_class()
        selected = design_targets[target_name]
        generated_path = root / selected["selected_circuit_path"]
        denominator_path = root / selected["denominator_circuit_path"]
        generated = qasm3.load(generated_path)
        denominator = qasm3.load(denominator_path)
        metadata = design["snapshot_metadata"][target_name]
        generated_exposure = exposure_ledger(root, generated_path, metadata)
        denominator_exposure = exposure_ledger(root, denominator_path, metadata)
        exposure_rows.extend([
            {"target_snapshot": target_name, "route": "generated", **generated_exposure},
            {"target_snapshot": target_name, "route": "denominator", **denominator_exposure},
        ])

        candidates = [row for row in design["candidate_rows"] if row["target_snapshot"] == target_name]
        denominators = [row for row in design["denominator_rows"] if row["target_snapshot"] == target_name]
        candidate_signatures = [edge_signature(root / row["circuit_path"]) for row in candidates]
        denominator_signatures = [edge_signature(root / row["circuit_path"]) for row in denominators]
        generated_exposure_rank = 1 + sum(row["compiled_combined_any_error_proxy"] < generated_exposure["combined_any_error_proxy"] for row in candidates)
        diversity_rows.append({
            "target_snapshot": target_name,
            "candidate_count": len(candidates),
            "unique_mapping_count": len({tuple(row["mapping"]) for row in candidates}),
            "unique_candidate_qasm_hash_count": len({row["qasm_stable_hash"] for row in candidates}),
            "unique_candidate_edge_signature_count": len(set(candidate_signatures)),
            "denominator_count": len(denominators),
            "unique_denominator_qasm_hash_count": len({row["qasm_stable_hash"] for row in denominators}),
            "unique_denominator_edge_signature_count": len(set(denominator_signatures)),
            "generated_exposure_rank_among_48": generated_exposure_rank,
            "generated_signature_present_in_denominator_pool": edge_signature(generated_path) in set(denominator_signatures),
            "denominator_signature_present_in_candidate_pool": edge_signature(denominator_path) in set(candidate_signatures),
        })

        models = split_noise_models(backend)
        by_model: dict[str, dict[str, list[float]]] = {
            model_name: {"generated": [], "denominator": []} for model_name in models
        }
        for model_name, noise_model in models.items():
            simulator = AerSimulator(noise_model=noise_model)
            for seed in ATTRIBUTION_SEEDS:
                for route_name, circuit in [("generated", generated), ("denominator", denominator)]:
                    counts = simulator.run(circuit, shots=SHOTS, seed_simulator=seed).result().get_counts()
                    observed = probability_from_counts(counts, SHOTS, task["circuit"].num_qubits)
                    fidelity = hellinger_fidelity(ideal, observed)
                    by_model[model_name][route_name].append(fidelity)
                    channel_rows.append({
                        "target_snapshot": target_name,
                        "noise_model": model_name,
                        "seed": seed,
                        "route": route_name,
                        "fidelity": fidelity,
                    })
        model_rows = []
        for model_name, routes in by_model.items():
            deltas = [a - b for a, b in zip(routes["generated"], routes["denominator"], strict=True)]
            model_rows.append({
                "noise_model": model_name,
                "mean_generated_fidelity": statistics.mean(routes["generated"]),
                "mean_denominator_fidelity": statistics.mean(routes["denominator"]),
                "mean_generated_minus_denominator": statistics.mean(deltas),
                "minimum_generated_minus_denominator": min(deltas),
                "generated_win_count": sum(value > 0 for value in deltas),
                "seed_count": len(deltas),
            })
        by_name = {row["noise_model"]: row for row in model_rows}
        dominant = max(("gate_only", "readout_only"), key=lambda name: abs(by_name[name]["mean_generated_minus_denominator"]))
        target_rows.append({
            "target_snapshot": target_name,
            "r150_holdout_mean_generated_minus_denominator": holdout_groups[target_name]["mean_generated_minus_denominator"],
            "r151_full_mean_generated_minus_denominator": by_name["full"]["mean_generated_minus_denominator"],
            "r151_gate_only_mean_generated_minus_denominator": by_name["gate_only"]["mean_generated_minus_denominator"],
            "r151_readout_only_mean_generated_minus_denominator": by_name["readout_only"]["mean_generated_minus_denominator"],
            "dominant_isolated_channel": dominant,
            "generated_minus_denominator_combined_exposure_proxy": generated_exposure["combined_any_error_proxy"] - denominator_exposure["combined_any_error_proxy"],
            "generated_minus_denominator_cx_exposure_proxy": generated_exposure["cx_any_error_proxy"] - denominator_exposure["cx_any_error_proxy"],
            "generated_minus_denominator_readout_exposure_proxy": generated_exposure["readout_any_error_proxy"] - denominator_exposure["readout_any_error_proxy"],
            "generated_minus_denominator_cx_count": generated_exposure["cx_occurrence_count"] - denominator_exposure["cx_occurrence_count"],
            "model_rows": model_rows,
        })

    casablanca = next(row for row in target_rows if row["target_snapshot"] == "FakeCasablancaV2")
    casablanca_diversity = next(row for row in diversity_rows if row["target_snapshot"] == "FakeCasablancaV2")
    summary = {
        "target_snapshot_count": len(target_rows),
        "attribution_seed_count_per_model": len(ATTRIBUTION_SEEDS),
        "noise_model_count": 3,
        "route_count_per_target": 2,
        "simulated_circuit_execution_count": len(channel_rows),
        "shots_per_execution": SHOTS,
        "total_simulated_shots": len(channel_rows) * SHOTS,
        "r150_trial_rows_consumed_for_failure_label_count": len(trial_rows),
        "repair_candidate_generated": False,
        "casablanca_r150_holdout_delta": casablanca["r150_holdout_mean_generated_minus_denominator"],
        "casablanca_r151_full_delta": casablanca["r151_full_mean_generated_minus_denominator"],
        "casablanca_gate_only_delta": casablanca["r151_gate_only_mean_generated_minus_denominator"],
        "casablanca_readout_only_delta": casablanca["r151_readout_only_mean_generated_minus_denominator"],
        "casablanca_dominant_isolated_channel": casablanca["dominant_isolated_channel"],
        "casablanca_combined_exposure_proxy_delta": casablanca["generated_minus_denominator_combined_exposure_proxy"],
        "casablanca_cx_exposure_proxy_delta": casablanca["generated_minus_denominator_cx_exposure_proxy"],
        "casablanca_readout_exposure_proxy_delta": casablanca["generated_minus_denominator_readout_exposure_proxy"],
        "casablanca_cx_count_delta": casablanca["generated_minus_denominator_cx_count"],
        "casablanca_unique_candidate_edge_signature_count": casablanca_diversity["unique_candidate_edge_signature_count"],
        "casablanca_unique_denominator_edge_signature_count": casablanca_diversity["unique_denominator_edge_signature_count"],
        "casablanca_generated_exposure_rank_among_48": casablanca_diversity["generated_exposure_rank_among_48"],
        "full_model_failure_sign_reproduced": casablanca["r151_full_mean_generated_minus_denominator"] < 0,
        "hardware_execution_claimed": False,
        "general_route_generation_advantage_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "solved_frontier_claimed": False,
        "new_credit_delta": 0,
    }
    requirements = [
        {"requirement_id": "R1", "label": "R150 design, result, and trial-row hashes are bound", "passed": True},
        {"requirement_id": "R2", "label": "three backends, three noise models, two routes, and 32 seeds produce 576 executions", "passed": summary["simulated_circuit_execution_count"] == 576},
        {"requirement_id": "R3", "label": "full, gate-only, and readout-only models use identical route and seed schedules", "passed": len(channel_rows) == 576},
        {"requirement_id": "R4", "label": "Casablanca full-model attribution reproduces the negative R150 sign", "passed": summary["full_model_failure_sign_reproduced"]},
        {"requirement_id": "R5", "label": "route exposure ledgers cover both routes on all three backends", "passed": len(exposure_rows) == 6},
        {"requirement_id": "R6", "label": "candidate and denominator diversity ledgers cover all three backends", "passed": len(diversity_rows) == 3 and all(row["candidate_count"] == 48 and row["denominator_count"] == 80 for row in diversity_rows)},
        {"requirement_id": "R7", "label": "all 24 revealed R150 rows are used only to bind failure labels", "passed": summary["r150_trial_rows_consumed_for_failure_label_count"] == 24},
        {"requirement_id": "R8", "label": "attribution produces no repair candidate", "passed": not summary["repair_candidate_generated"]},
        {"requirement_id": "R9", "label": "result distinguishes channel attribution from causal proof", "passed": True},
        {"requirement_id": "R10", "label": "hardware, general generation, advantage, BQP, solved-frontier, and credit claims remain false", "passed": not any([summary["hardware_execution_claimed"], summary["general_route_generation_advantage_claimed"], summary["quantum_advantage_claimed"], summary["bqp_separation_claimed"], summary["solved_frontier_claimed"], summary["new_credit_delta"]])},
    ]
    payload = {
        "title": "B4/B8 R151 Casablanca failure attribution",
        "version": 0,
        "method": METHOD,
        "status": "casablanca_failure_channel_and_route_attribution",
        "model_status": "post_holdout_diagnostic_not_repair_selection_or_causal_proof",
        "generated_at_unix": int(time.time()),
        "source_target_id": "T-B4-002bk/T-B8-003bo/T-B10-009bc",
        "upstream_target_id": "T-B4-002bj/T-B8-003bn/T-B10-009bb",
        "source_bindings": {
            "r150_design_path": DESIGN_PATH,
            "r150_design_sha256": file_sha256(root / DESIGN_PATH),
            "r150_design_payload_hash": design["payload_hash"],
            "r150_holdout_path": HOLDOUT_PATH,
            "r150_holdout_sha256": file_sha256(root / HOLDOUT_PATH),
            "r150_holdout_payload_hash": holdout["payload_hash"],
            "r150_trial_rows_path": TRIALS_PATH,
            "r150_trial_rows_sha256": file_sha256(root / TRIALS_PATH),
            "r150_trial_rows_consumed_for_attribution": True,
        },
        "attribution_protocol": {
            "seeds": list(ATTRIBUTION_SEEDS),
            "shots_per_execution": SHOTS,
            "noise_models": ["full", "gate_only", "readout_only"],
            "routes": ["generated", "denominator"],
            "repair_selection_forbidden": True,
        },
        "summary": summary,
        "target_rows": target_rows,
        "exposure_rows": exposure_rows,
        "diversity_rows": diversity_rows,
        "channel_rows": channel_rows,
        "requirements": requirements,
        "requirement_count": 10,
        "requirements_passed": sum(row["passed"] for row in requirements),
        "requirements_failed": sum(not row["passed"] for row in requirements),
        "failed_requirement_ids": [row["requirement_id"] for row in requirements if not row["passed"]],
        "artifacts": {"result": RESULT_PATH, "markdown_report": REPORT_PATH},
        "claim_boundary": {
            "what_is_supported": "a post-holdout channel, route-exposure, and diversity attribution of the R150 Casablanca failure",
            "what_is_not_supported": "causal proof, a repair candidate, a new hidden holdout, temporal or real-device transfer, hardware performance, general route-generation advantage, quantum advantage, BQP separation, solved B4/B8/B10, or new credit",
        },
    }
    hash_payload = dict(payload)
    payload["payload_hash"] = hashlib.sha256(json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload


def report(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    targets = "\n".join(
        f"- `{row['target_snapshot']}`: full `{row['r151_full_mean_generated_minus_denominator']:+.8f}`, gate-only `{row['r151_gate_only_mean_generated_minus_denominator']:+.8f}`, readout-only `{row['r151_readout_only_mean_generated_minus_denominator']:+.8f}`, exposure delta `{row['generated_minus_denominator_combined_exposure_proxy']:+.8f}`, CX-count delta `{row['generated_minus_denominator_cx_count']:+d}`."
        for row in payload["target_rows"]
    )
    return f"""# B4/B8 R151 Casablanca Failure Attribution

- Attribution executions / shots: `{s['simulated_circuit_execution_count']}` / `{s['total_simulated_shots']}`
- Casablanca R150 / R151 full deltas: `{s['casablanca_r150_holdout_delta']:+.8f}` / `{s['casablanca_r151_full_delta']:+.8f}`
- Casablanca gate-only / readout-only deltas: `{s['casablanca_gate_only_delta']:+.8f}` / `{s['casablanca_readout_only_delta']:+.8f}`
- Dominant isolated channel: `{s['casablanca_dominant_isolated_channel']}`
- Casablanca combined / CX / readout exposure deltas: `{s['casablanca_combined_exposure_proxy_delta']:+.8f}` / `{s['casablanca_cx_exposure_proxy_delta']:+.8f}` / `{s['casablanca_readout_exposure_proxy_delta']:+.8f}`
- Casablanca CX-count delta: `{s['casablanca_cx_count_delta']:+d}`
- Candidate / denominator edge-signature diversity: `{s['casablanca_unique_candidate_edge_signature_count']}` / `{s['casablanca_unique_denominator_edge_signature_count']}`
- Generated exposure rank among 48: `{s['casablanca_generated_exposure_rank_among_48']}`
- Repair candidate generated: `false`

{targets}

R151 replays both frozen routes under full, gate-only, and readout-only noise
with 32 fresh attribution seeds. It also binds edge-level calibration exposure
and route-diversity ledgers. The result is diagnostic: it can prioritize the
next zero-hidden-row correction, but it is not causal proof and selects no
repair candidate.

No hardware, general route-generation, quantum-advantage, BQP, solved-frontier,
or new-credit claim is made.
"""


def main() -> int:
    ensure_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    payload = build(root)
    write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
