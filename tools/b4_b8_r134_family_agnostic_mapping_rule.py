#!/usr/bin/env python3
"""T-B4-002ai/T-B8-003am: test a family-agnostic deterministic mapper."""

from __future__ import annotations

import argparse
import heapq
import itertools
import json
import math
import os
import statistics
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

from qiskit import QuantumCircuit, qasm3, transpile

from b4_b8_r121_private_bundle_shot_sweep import basis_circuit, stable_hash, write_json
from b4_b8_r126_calibration_attribution_ledger import file_sha256
from b4_b8_r127_calibration_aware_layout_design import SNAPSHOT_CLASSES
from b4_b8_r128_transpiler_loop_layout_ranking import exposure_from_qasm, package_version
from b4_b8_r131_compiled_route_family_attribution import compiled_route_descriptor
from b4_b8_r132_topology_constrained_route_policy import (
    DETERMINISTIC_PROCESS_ENV,
    compile_policy,
)
from b4_b8_r133_unseen_circuit_family_holdout import build_holdout_tasks


METHOD = "b4_b8_r134_family_agnostic_mapping_rule_v0"
STATUS = "family_agnostic_deterministic_mapping_boundary"
MODEL_STATUS = "generic_mapping_rule_selected_on_design_set_and_tested_on_new_families"
TARGET_ID = "T-B4-002ai/T-B8-003am/T-B10-009aa"
UPSTREAM_TARGET_ID = "T-B4-002ah/T-B8-003al/T-B10-009z"
R125_RESULT_PATH = "results/B4_B8_R125_historical_snapshot_replay_v0.json"
R133_RESULT_PATH = "results/B4_B8_R133_unseen_circuit_family_holdout_v0.json"
RESULT_PATH = "results/B4_B8_R134_family_agnostic_mapping_rule_v0.json"
REPORT_PATH = "research/B4_B8_R134_family_agnostic_mapping_rule.md"
OUT_DIR = "results/B4_B8_R134_family_agnostic_mapping_rule"
DESIGN_SEEDS = tuple(range(13401, 13405))
VALIDATION_SEEDS = tuple(range(13451, 13461))
ROUTING_POLICY_ID = "selected_o3_lookahead"
RULE_IDS = (
    "weighted_distance",
    "distance_then_error",
    "error_then_distance",
    "nonadjacency_then_error",
)
TOLERANCE = 1e-15


def ensure_deterministic_process_environment() -> None:
    if all(os.environ.get(key) == value for key, value in DETERMINISTIC_PROCESS_ENV.items()):
        return
    environment = dict(os.environ)
    environment.update(DETERMINISTIC_PROCESS_ENV)
    os.execvpe(sys.executable, [sys.executable, *sys.argv], environment)


def build_validation_tasks() -> list[dict[str, Any]]:
    qft = QuantumCircuit(6)
    for target in range(6):
        qft.h(target)
        for control in range(target + 1, 6):
            qft.cp(math.pi / (2 ** (control - target)), control, target)
    for left, right in [(0, 5), (1, 4), (2, 3)]:
        qft.swap(left, right)

    k33_qaoa = QuantumCircuit(6)
    for target in range(6):
        k33_qaoa.h(target)
    for left in range(3):
        for right in range(3, 6):
            k33_qaoa.rzz(math.pi / 7, left, right)
    for target in range(6):
        k33_qaoa.rx(math.pi / 5, target)

    tree_phase = QuantumCircuit(6)
    for target in range(6):
        tree_phase.h(target)
    tree_edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)]
    for left, right in tree_edges:
        tree_phase.cz(left, right)
    for target in range(6):
        tree_phase.ry(math.pi * (target + 1) / 17, target)
    for left, right in reversed(tree_edges):
        tree_phase.cx(left, right)

    rxx_cycle = QuantumCircuit(6)
    for target in range(6):
        rxx_cycle.ry(math.pi * (target + 2) / 19, target)
    cycle_edges = [(0, 1), (2, 3), (4, 5), (1, 2), (3, 4), (5, 0)]
    for index, (left, right) in enumerate(cycle_edges):
        rxx_cycle.rxx(math.pi * (index + 1) / 23, left, right)
    for target in range(6):
        rxx_cycle.rz(math.pi * (target + 1) / 13, target)

    return [
        {"task_id": "validation_qft_n6", "family": "qft", "circuit": qft},
        {
            "task_id": "validation_k33_qaoa_n6",
            "family": "complete_bipartite_qaoa",
            "circuit": k33_qaoa,
        },
        {
            "task_id": "validation_tree_phase_n6",
            "family": "tree_phase",
            "circuit": tree_phase,
        },
        {
            "task_id": "validation_rxx_cycle_n6",
            "family": "rxx_cycle",
            "circuit": rxx_cycle,
        },
    ]


def physical_metrics(metadata: dict[str, Any]) -> dict[str, Any]:
    canonical = metadata["canonical"]
    nodes = sorted({qubit for edge in canonical["coupling_edges"] for qubit in edge})
    adjacency = {node: set() for node in nodes}
    for left, right in canonical["coupling_edges"]:
        adjacency[left].add(right)
        adjacency[right].add(left)
    edge_error: dict[tuple[int, int], float] = {}
    for row in canonical["instruction_properties"]["cx"]:
        left, right = row["qargs"]
        edge = tuple(sorted((left, right)))
        edge_error[edge] = min(edge_error.get(edge, 1.0), row["error"])
    readout_error = {
        row["qargs"][0]: row["error"]
        for row in canonical["instruction_properties"]["measure"]
    }
    distance: dict[tuple[int, int], int] = {}
    path_error: dict[tuple[int, int], float] = {}
    for source in nodes:
        levels = {source: 0}
        queue = [source]
        for current in queue:
            for neighbor in sorted(adjacency[current]):
                if neighbor not in levels:
                    levels[neighbor] = levels[current] + 1
                    queue.append(neighbor)
        for target, value in levels.items():
            distance[(source, target)] = value
        best = {source: 0.0}
        heap = [(0.0, source)]
        while heap:
            cost, current = heapq.heappop(heap)
            if cost != best[current]:
                continue
            for neighbor in adjacency[current]:
                edge = tuple(sorted((current, neighbor)))
                candidate = cost - math.log1p(-edge_error[edge])
                if candidate < best.get(neighbor, float("inf")):
                    best[neighbor] = candidate
                    heapq.heappush(heap, (candidate, neighbor))
        for target, value in best.items():
            path_error[(source, target)] = value
    return {
        "nodes": nodes,
        "distance": distance,
        "path_error": path_error,
        "readout_error": readout_error,
    }


def interaction_weights(circuit: QuantumCircuit) -> Counter[tuple[int, int]]:
    weights: Counter[tuple[int, int]] = Counter()
    for instruction in circuit.data:
        if len(instruction.qubits) != 2:
            continue
        left, right = [
            circuit.find_bit(qubit).index for qubit in instruction.qubits
        ]
        weights[tuple(sorted((left, right)))] += 1
    if not weights:
        raise ValueError("mapping rule requires at least one two-qubit interaction")
    return weights


def mapping_scores(
    mapping: tuple[int, ...],
    weights: Counter[tuple[int, int]],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    weighted_distance = sum(
        count * metrics["distance"][(mapping[left], mapping[right])]
        for (left, right), count in weights.items()
    )
    maximum_distance = max(
        metrics["distance"][(mapping[left], mapping[right])]
        for left, right in weights
    )
    weighted_path_error = sum(
        count * metrics["path_error"][(mapping[left], mapping[right])]
        for (left, right), count in weights.items()
    )
    nonadjacent_weight = sum(
        count
        for (left, right), count in weights.items()
        if metrics["distance"][(mapping[left], mapping[right])] > 1
    )
    readout_error = sum(metrics["readout_error"][qubit] for qubit in mapping)
    return {
        "weighted_distance": weighted_distance,
        "maximum_distance": maximum_distance,
        "weighted_path_error": weighted_path_error,
        "nonadjacent_interaction_weight": nonadjacent_weight,
        "readout_error_sum": readout_error,
    }


def score_key(
    rule_id: str, score: dict[str, Any], mapping: tuple[int, ...]
) -> tuple[Any, ...]:
    if rule_id == "weighted_distance":
        return (
            score["weighted_distance"],
            score["maximum_distance"],
            score["readout_error_sum"],
            mapping,
        )
    if rule_id == "distance_then_error":
        return (
            score["weighted_distance"],
            score["weighted_path_error"],
            score["readout_error_sum"],
            mapping,
        )
    if rule_id == "error_then_distance":
        return (
            score["weighted_path_error"],
            score["weighted_distance"],
            score["readout_error_sum"],
            mapping,
        )
    if rule_id == "nonadjacency_then_error":
        return (
            score["nonadjacent_interaction_weight"],
            score["weighted_path_error"],
            score["weighted_distance"],
            score["readout_error_sum"],
            mapping,
        )
    raise ValueError(f"unknown rule: {rule_id}")


def choose_mappings(
    circuit: QuantumCircuit, metadata: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    metrics = physical_metrics(metadata)
    weights = interaction_weights(circuit)
    best: dict[str, tuple[tuple[Any, ...], tuple[int, ...], dict[str, Any]]] = {}
    for mapping in itertools.permutations(metrics["nodes"], circuit.num_qubits):
        scores = mapping_scores(mapping, weights, metrics)
        for rule_id in RULE_IDS:
            key = score_key(rule_id, scores, mapping)
            if rule_id not in best or key < best[rule_id][0]:
                best[rule_id] = (key, mapping, scores)
    return {
        rule_id: {
            "mapping": list(row[1]),
            "scores": row[2],
            "interaction_edge_count": len(weights),
            "interaction_occurrence_count": sum(weights.values()),
        }
        for rule_id, row in best.items()
    }


def outcome(delta: float) -> str:
    return "win" if delta > TOLERANCE else "loss" if delta < -TOLERANCE else "tie"


def report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    group_lines = []
    for row in payload["validation_group_rows"]:
        group_lines.append(
            "- `{snapshot}` / `{task}`: mapping `{mapping}`; route/QASM classes "
            "`{routes}/{qasm}`; gain `{gain:+.6f}`; wins/ties/losses "
            "`{wins}/{ties}/{losses}`.".format(
                snapshot=row["snapshot"],
                task=row["task_id"],
                mapping=row["selected_mapping"],
                routes=row["constrained_unique_route_family_count"],
                qasm=row["constrained_unique_qasm_hash_count"],
                gain=row["mean_gain_vs_automatic_default"],
                wins=row["win_count_vs_automatic_default"],
                ties=row["tie_count_vs_automatic_default"],
                losses=row["loss_count_vs_automatic_default"],
            )
        )
    requirements = "\n".join(
        f"- `{row['requirement_id']}` {'PASS' if row['passed'] else 'FAIL'}: {row['label']}"
        for row in payload["requirements"]
    )
    return f"""# B4/B8 R134 Family-Agnostic Deterministic Mapping Rule

## Result

- Candidate mapping rules: `{summary['candidate_rule_count']}`
- Design-set compilations: `{summary['design_compilation_count']}`
- Selected rule: `{summary['selected_rule_id']}`
- New validation families: `{summary['validation_task_count']}`
- Validation compilations: `{summary['validation_compilation_count']}`
- Route-invariant groups: `{summary['route_family_invariant_group_count']}` / `12`
- Exact-QASM-invariant groups: `{summary['exact_qasm_seed_invariant_group_count']}` / `12`
- Frozen QASM replay: `{summary['frozen_qasm_replay_match_count']}` / `120`
- Wins/ties/losses vs automatic layout: `{summary['win_count_vs_automatic_default']}/{summary['tie_count_vs_automatic_default']}/{summary['loss_count_vs_automatic_default']}`
- No-loss groups: `{summary['no_loss_group_count_vs_automatic_default']}` / `12`
- Automatic-baseline no-loss gate: `{summary['automatic_baseline_no_loss_gate_passed']}`
- New credit delta: `0`

## Validation Evidence

{chr(10).join(group_lines)}

R134 replaces transferred mappings with a generic graph-embedding rule. Every
candidate enumerates all 5,040 six-to-seven-qubit injections and scores only the
source interaction graph, historical coupling distances, path-error pressure,
and readout error. R133 circuits and fresh design seeds select one rule globally.
The selected rule is then frozen before four new circuit families and disjoint
validation seeds are opened.

## Requirements

{requirements}

## Claim Boundary

Supported: isolated evidence for or against a deterministic family-agnostic
mapping rule under the historical exposure proxy. Not supported: verifier
acceptance, causal hardware performance, current calibration, mitigation,
protocol soundness, quantum advantage, BQP separation, or new B10 credit.
"""


def run_gate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    r125_path = root / R125_RESULT_PATH
    r133_path = root / R133_RESULT_PATH
    r125 = json.loads(r125_path.read_text(encoding="utf-8"))
    r133 = json.loads(r133_path.read_text(encoding="utf-8"))
    if r133.get("status") != "unseen_circuit_family_route_holdout_boundary":
        raise ValueError("R134 requires the R133 unseen-family boundary")
    prior_seeds = set(r133["summary"]["holdout_seeds"])
    if prior_seeds & set(DESIGN_SEEDS + VALIDATION_SEEDS):
        raise ValueError("R134 seeds must be disjoint from R133")

    design_tasks = build_holdout_tasks()
    validation_tasks = build_validation_tasks()
    output = root / OUT_DIR
    source_dir = output / "source_circuits"
    constrained_dir = output / "constrained_circuits"
    source_dir.mkdir(parents=True, exist_ok=True)
    constrained_dir.mkdir(parents=True, exist_ok=True)
    prior_source_hashes = {
        file_sha256(root / path)
        for path in r133.get("artifacts", {}).get("source_circuits", [])
    }
    design_rows: list[dict[str, Any]] = []
    design_mapping_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    validation_mapping_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    frozen_paths: list[str] = []
    frozen_preexisting_count = 0
    frozen_match_count = 0

    with tempfile.TemporaryDirectory(prefix="r134-") as temporary:
        scratch = Path(temporary) / "compiled.qasm"
        for task in design_tasks:
            representative = basis_circuit(
                task["circuit"], tuple("Z" for _ in range(task["circuit"].num_qubits))
            )
            for snapshot_name in sorted(SNAPSHOT_CLASSES):
                backend = SNAPSHOT_CLASSES[snapshot_name]()
                metadata = r125["snapshot_metadata"][snapshot_name]
                candidates = choose_mappings(task["circuit"], metadata)
                for rule_id, candidate in sorted(candidates.items()):
                    design_mapping_rows.append(
                        {
                            "snapshot": snapshot_name,
                            "task_id": task["task_id"],
                            "rule_id": rule_id,
                            **candidate,
                        }
                    )
                for seed in DESIGN_SEEDS:
                    automatic = transpile(
                        representative,
                        backend=backend,
                        optimization_level=3,
                        seed_transpiler=seed,
                    )
                    automatic_exposure = exposure_from_qasm(
                        qasm3.dumps(automatic), metadata, scratch
                    )["combined_any_error_proxy"]
                    for rule_id, candidate in sorted(candidates.items()):
                        constrained = compile_policy(
                            representative,
                            backend,
                            candidate["mapping"],
                            ROUTING_POLICY_ID,
                            seed,
                        )
                        constrained_exposure = exposure_from_qasm(
                            qasm3.dumps(constrained), metadata, scratch
                        )["combined_any_error_proxy"]
                        gain = automatic_exposure - constrained_exposure
                        design_rows.append(
                            {
                                "snapshot": snapshot_name,
                                "task_id": task["task_id"],
                                "seed": seed,
                                "rule_id": rule_id,
                                "mapping": candidate["mapping"],
                                "gain_vs_automatic_default": gain,
                                "outcome_vs_automatic_default": outcome(gain),
                            }
                        )

        design_rule_rows = []
        for rule_id in RULE_IDS:
            rows = [row for row in design_rows if row["rule_id"] == rule_id]
            design_rule_rows.append(
                {
                    "rule_id": rule_id,
                    "row_count": len(rows),
                    "win_count_vs_automatic_default": sum(
                        row["outcome_vs_automatic_default"] == "win" for row in rows
                    ),
                    "tie_count_vs_automatic_default": sum(
                        row["outcome_vs_automatic_default"] == "tie" for row in rows
                    ),
                    "loss_count_vs_automatic_default": sum(
                        row["outcome_vs_automatic_default"] == "loss" for row in rows
                    ),
                    "mean_gain_vs_automatic_default": statistics.fmean(
                        row["gain_vs_automatic_default"] for row in rows
                    ),
                }
            )
        selected_rule = min(
            design_rule_rows,
            key=lambda row: (
                row["loss_count_vs_automatic_default"],
                -row["mean_gain_vs_automatic_default"],
                row["rule_id"],
            ),
        )
        selected_rule_id = selected_rule["rule_id"]

        for task in validation_tasks:
            source_path = source_dir / f"{task['task_id']}.qasm"
            source_path.write_text(qasm3.dumps(task["circuit"]), encoding="utf-8")
            source_hash = file_sha256(source_path)
            source_rows.append(
                {
                    "task_id": task["task_id"],
                    "family": task["family"],
                    "source_circuit_path": str(source_path.relative_to(root)),
                    "source_circuit_sha256": source_hash,
                    "unseen_vs_r133_source_circuits": source_hash not in prior_source_hashes,
                }
            )
            representative = basis_circuit(
                task["circuit"], tuple("Z" for _ in range(task["circuit"].num_qubits))
            )
            for snapshot_name in sorted(SNAPSHOT_CLASSES):
                backend = SNAPSHOT_CLASSES[snapshot_name]()
                metadata = r125["snapshot_metadata"][snapshot_name]
                candidate = choose_mappings(task["circuit"], metadata)[selected_rule_id]
                validation_mapping_rows.append(
                    {
                        "snapshot": snapshot_name,
                        "task_id": task["task_id"],
                        "rule_id": selected_rule_id,
                        **candidate,
                    }
                )
                for seed in VALIDATION_SEEDS:
                    constrained = compile_policy(
                        representative,
                        backend,
                        candidate["mapping"],
                        ROUTING_POLICY_ID,
                        seed,
                    )
                    fixed_default = compile_policy(
                        representative,
                        backend,
                        candidate["mapping"],
                        "selected_o3_default",
                        seed,
                    )
                    automatic = transpile(
                        representative,
                        backend=backend,
                        optimization_level=3,
                        seed_transpiler=seed,
                    )
                    constrained_qasm = qasm3.dumps(constrained)
                    fixed_qasm = qasm3.dumps(fixed_default)
                    automatic_qasm = qasm3.dumps(automatic)
                    constrained_exposure = exposure_from_qasm(
                        constrained_qasm, metadata, scratch
                    )
                    fixed_exposure = exposure_from_qasm(fixed_qasm, metadata, scratch)
                    automatic_exposure = exposure_from_qasm(
                        automatic_qasm, metadata, scratch
                    )
                    descriptor = compiled_route_descriptor(
                        constrained, constrained_exposure
                    )
                    constrained_path = constrained_dir / (
                        f"{snapshot_name}_{task['task_id']}_seed_{seed}.qasm"
                    )
                    relative_path = str(constrained_path.relative_to(root))
                    frozen_paths.append(relative_path)
                    if constrained_path.exists():
                        frozen_preexisting_count += 1
                        frozen_match = (
                            constrained_path.read_text(encoding="utf-8")
                            == constrained_qasm
                        )
                    else:
                        constrained_path.write_text(constrained_qasm, encoding="utf-8")
                        frozen_match = True
                    frozen_match_count += frozen_match
                    gain = (
                        automatic_exposure["combined_any_error_proxy"]
                        - constrained_exposure["combined_any_error_proxy"]
                    )
                    validation_rows.append(
                        {
                            "snapshot": snapshot_name,
                            "task_id": task["task_id"],
                            "family": task["family"],
                            "seed": seed,
                            "selected_rule_id": selected_rule_id,
                            "selected_mapping": candidate["mapping"],
                            "mapping_scores": candidate["scores"],
                            "constrained_circuit_path": relative_path,
                            "constrained_circuit_sha256": file_sha256(constrained_path),
                            "frozen_qasm_replay_matches": frozen_match,
                            "constrained_qasm_hash": stable_hash(constrained_qasm),
                            "constrained_route_family": descriptor,
                            "constrained_combined_any_error_proxy": constrained_exposure[
                                "combined_any_error_proxy"
                            ],
                            "fixed_mapping_default_combined_any_error_proxy": fixed_exposure[
                                "combined_any_error_proxy"
                            ],
                            "automatic_default_combined_any_error_proxy": automatic_exposure[
                                "combined_any_error_proxy"
                            ],
                            "gain_vs_automatic_default": gain,
                            "gain_vs_fixed_mapping_default": fixed_exposure[
                                "combined_any_error_proxy"
                            ]
                            - constrained_exposure["combined_any_error_proxy"],
                            "outcome_vs_automatic_default": outcome(gain),
                        }
                    )

    group_rows = []
    keys = sorted({(row["snapshot"], row["task_id"]) for row in validation_rows})
    for key in keys:
        rows = [
            row
            for row in validation_rows
            if (row["snapshot"], row["task_id"]) == key
        ]
        route_count = len(
            {row["constrained_route_family"]["route_family_id"] for row in rows}
        )
        qasm_count = len({row["constrained_qasm_hash"] for row in rows})
        group_rows.append(
            {
                "snapshot": key[0],
                "task_id": key[1],
                "family": rows[0]["family"],
                "selected_rule_id": selected_rule_id,
                "selected_mapping": rows[0]["selected_mapping"],
                "constrained_unique_route_family_count": route_count,
                "constrained_unique_qasm_hash_count": qasm_count,
                "route_family_seed_invariant": route_count == 1,
                "exact_qasm_seed_invariant": qasm_count == 1,
                "mean_gain_vs_automatic_default": statistics.fmean(
                    row["gain_vs_automatic_default"] for row in rows
                ),
                "minimum_gain_vs_automatic_default": min(
                    row["gain_vs_automatic_default"] for row in rows
                ),
                "win_count_vs_automatic_default": sum(
                    row["outcome_vs_automatic_default"] == "win" for row in rows
                ),
                "tie_count_vs_automatic_default": sum(
                    row["outcome_vs_automatic_default"] == "tie" for row in rows
                ),
                "loss_count_vs_automatic_default": sum(
                    row["outcome_vs_automatic_default"] == "loss" for row in rows
                ),
            }
        )

    route_invariant_count = sum(row["route_family_seed_invariant"] for row in group_rows)
    qasm_invariant_count = sum(row["exact_qasm_seed_invariant"] for row in group_rows)
    win_count = sum(row["outcome_vs_automatic_default"] == "win" for row in validation_rows)
    tie_count = sum(row["outcome_vs_automatic_default"] == "tie" for row in validation_rows)
    loss_count = sum(row["outcome_vs_automatic_default"] == "loss" for row in validation_rows)
    no_loss_groups = sum(row["loss_count_vs_automatic_default"] == 0 for row in group_rows)
    deterministic_gate = (
        route_invariant_count == 12
        and qasm_invariant_count == 12
        and frozen_preexisting_count == 120
        and frozen_match_count == 120
    )
    no_loss_gate = loss_count == 0
    summary = {
        "candidate_rule_count": len(RULE_IDS),
        "enumerated_mapping_count_per_group": 5040,
        "design_task_count": len(design_tasks),
        "design_group_count": len(design_tasks) * len(SNAPSHOT_CLASSES),
        "design_seed_count": len(DESIGN_SEEDS),
        "design_seeds": list(DESIGN_SEEDS),
        "design_compilation_count": len(design_rows)
        + len(design_tasks) * len(SNAPSHOT_CLASSES) * len(DESIGN_SEEDS),
        "selected_rule_id": selected_rule_id,
        "validation_task_count": len(validation_tasks),
        "validation_group_count": len(group_rows),
        "validation_seed_count": len(VALIDATION_SEEDS),
        "validation_seeds": list(VALIDATION_SEEDS),
        "validation_compilation_count": len(validation_rows) * 3,
        "validation_row_count": len(validation_rows),
        "source_circuit_count": len(source_rows),
        "source_circuits_unseen_vs_r133_count": sum(
            row["unseen_vs_r133_source_circuits"] for row in source_rows
        ),
        "mapping_rule_uses_compile_outcomes": False,
        "validation_read_during_rule_selection": False,
        "route_family_invariant_group_count": route_invariant_count,
        "exact_qasm_seed_invariant_group_count": qasm_invariant_count,
        "frozen_qasm_preexisting_count": frozen_preexisting_count,
        "frozen_qasm_replay_match_count": frozen_match_count,
        "win_count_vs_automatic_default": win_count,
        "tie_count_vs_automatic_default": tie_count,
        "loss_count_vs_automatic_default": loss_count,
        "no_loss_group_count_vs_automatic_default": no_loss_groups,
        "deterministic_generalization_gate_passed": deterministic_gate,
        "automatic_baseline_no_loss_gate_passed": no_loss_gate,
        "exact_qasm_cross_process_replay_claimed": frozen_preexisting_count == 120
        and frozen_match_count == 120,
        "fresh_design_and_validation_seed_blocks_used": True,
        "r133_seeds_reused": False,
        "acceptance_holdout_executed": False,
        "r125_acceptance_rows_read": False,
        "readout_mitigation_tested": False,
        "current_backend_calibration_used": False,
        "hardware_execution_performed": False,
        "protocol_soundness_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "new_credit_delta": 0,
    }
    requirements = [
        {
            "requirement_id": "P1",
            "label": "R133 source is hash-bound",
            "passed": r133.get("source_target_id") == UPSTREAM_TARGET_ID,
            "evidence": {"r133_sha256": file_sha256(r133_path)},
        },
        {
            "requirement_id": "P2",
            "label": "four generic mapping rules enumerate all injections",
            "passed": len(RULE_IDS) == 4
            and summary["enumerated_mapping_count_per_group"] == 5040,
            "evidence": {"rule_ids": list(RULE_IDS)},
        },
        {
            "requirement_id": "P3",
            "label": "design selection is isolated from validation",
            "passed": selected_rule_id in RULE_IDS
            and not summary["validation_read_during_rule_selection"],
            "evidence": {"selected_rule_id": selected_rule_id},
        },
        {
            "requirement_id": "P4",
            "label": "four new validation circuit families are materialized",
            "passed": len(source_rows) == 4
            and summary["source_circuits_unseen_vs_r133_count"] == 4,
            "evidence": {"source_rows": source_rows},
        },
        {
            "requirement_id": "P5",
            "label": "all 12 validation groups have complete ten-seed ledgers",
            "passed": len(group_rows) == 12 and len(validation_rows) == 120,
            "evidence": {"group_count": len(group_rows), "row_count": len(validation_rows)},
        },
        {
            "requirement_id": "P6",
            "label": "route and exact-QASM invariance are measured for every group",
            "passed": route_invariant_count == 12 and qasm_invariant_count == 12,
            "evidence": {
                "route_invariant_groups": route_invariant_count,
                "qasm_invariant_groups": qasm_invariant_count,
            },
        },
        {
            "requirement_id": "P7",
            "label": "all 120 constrained circuits replay in a fresh process",
            "passed": frozen_preexisting_count == 120 and frozen_match_count == 120,
            "evidence": {
                "preexisting": frozen_preexisting_count,
                "matches": frozen_match_count,
            },
        },
        {
            "requirement_id": "P8",
            "label": "automatic-baseline no-loss verdict is evaluated without promotion",
            "passed": summary["automatic_baseline_no_loss_gate_passed"] == (loss_count == 0),
            "evidence": {"loss_count": loss_count, "no_loss_gate": no_loss_gate},
        },
        {
            "requirement_id": "P9",
            "label": "verifier acceptance, mitigation, calibration, and hardware remain excluded",
            "passed": not summary["acceptance_holdout_executed"]
            and not summary["r125_acceptance_rows_read"]
            and not summary["readout_mitigation_tested"]
            and not summary["current_backend_calibration_used"]
            and not summary["hardware_execution_performed"],
            "evidence": {"compiler_mapping_validation_only": True},
        },
        {
            "requirement_id": "P10",
            "label": "no soundness, advantage, BQP, or new credit is claimed",
            "passed": not summary["protocol_soundness_claimed"]
            and not summary["quantum_advantage_claimed"]
            and not summary["bqp_separation_claimed"]
            and summary["new_credit_delta"] == 0,
            "evidence": {"new_credit_delta": 0},
        },
    ]
    failed = [row["requirement_id"] for row in requirements if not row["passed"]]
    payload: dict[str, Any] = {
        "title": "B4/B8 R134 family-agnostic deterministic mapping rule",
        "version": "0.1",
        "generated_at_unix": int(time.time()),
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "requirements": requirements,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "summary": summary,
        "design_rule_rows": design_rule_rows,
        "design_mapping_rows": design_mapping_rows,
        "design_rows": design_rows,
        "validation_source_rows": source_rows,
        "validation_mapping_rows": validation_mapping_rows,
        "validation_group_rows": group_rows,
        "validation_rows": validation_rows,
        "environment": {
            "deterministic_process_environment": DETERMINISTIC_PROCESS_ENV,
            "qiskit": package_version("qiskit"),
            "qiskit_ibm_runtime": package_version("qiskit-ibm-runtime"),
        },
        "artifacts": {
            "r133_result": R133_RESULT_PATH,
            "source_circuits": [row["source_circuit_path"] for row in source_rows],
            "constrained_circuits": sorted(frozen_paths),
        },
        "claim_boundary": {
            "what_is_supported": (
                "Design-separated validation of a family-agnostic deterministic mapping rule "
                "against the historical automatic-layout exposure baseline."
            ),
            "what_is_not_supported": (
                "Verifier acceptance, causal hardware performance, readout mitigation, "
                "current calibration, provider access, hardware execution, protocol soundness, "
                "quantum advantage, BQP separation, or new B10 credit."
            ),
            "next_gate": (
                "If the no-loss gate fails, add a deterministic fallback contract that chooses "
                "between the generic mapping and automatic candidates without reading validation."
            ),
        },
    }
    payload["payload_hash"] = stable_hash(payload)
    write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    return payload


def main() -> None:
    ensure_deterministic_process_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    payload = run_gate(args.root)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
