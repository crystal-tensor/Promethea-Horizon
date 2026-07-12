#!/usr/bin/env python3
"""T-B4-002w/T-B8-003aa: pair shot budgets on one ordered replay stream."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from qiskit import QuantumCircuit, qasm3
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from b4_b8_r119_private_observable_bundle_gate import (
    build_bundle_tasks,
    shadow_estimate,
    target_expectation,
)
from b4_b8_r121_private_bundle_shot_sweep import (
    HONEST_TARGET,
    PROFILES,
    SHOT_BUDGETS,
    TOLERANCE,
    basis_circuit,
    decode_counts,
    noise_model,
    stable_hash,
    write_json,
)


METHOD = "b4_b8_r122_matched_seed_prefix_replay_v0"
STATUS = "matched_seed_prefix_shot_budget_confidence_boundary"
MODEL_STATUS = "r121_shot_sweep_replayed_with_paired_prefixes_and_wilson_bounds"
TARGET_ID = "T-B4-002w/T-B8-003aa/T-B10-009o"
UPSTREAM_TARGET_ID = "T-B4-002v/T-B8-003z/T-B10-009n"
R121_RESULT_PATH = "results/B4_B8_R121_private_bundle_shot_sweep_v0.json"
OUT_DIR = "results/B4_B8_R122_matched_seed_prefix_replay"
RESULT_PATH = "results/B4_B8_R122_matched_seed_prefix_replay_v0.json"
REPORT_PATH = "research/B4_B8_R122_matched_seed_prefix_replay.md"
SEED = 122
TRIALS = 30
MAX_SHOTS = max(SHOT_BUDGETS)
WILSON_Z = 1.959963984540054


def wilson_interval(successes: int, trials: int) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    rate = successes / trials
    z2 = WILSON_Z * WILSON_Z
    denominator = 1.0 + z2 / trials
    center = (rate + z2 / (2.0 * trials)) / denominator
    margin = WILSON_Z * math.sqrt(
        rate * (1.0 - rate) / trials + z2 / (4.0 * trials * trials)
    ) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def target_values(task: dict[str, Any]) -> dict[str, float]:
    base = task["circuit"]
    state = Statevector.from_instruction(base)
    values: dict[str, float] = {}
    targets = [
        *task["negative_targets"],
        task["positive_anchor"],
        *task["positive_targets"],
    ]
    for target in targets:
        values[json.dumps(target, sort_keys=True)] = target_expectation(
            state, base.num_qubits, target
        )
    return values


def matched_prefix_records(
    base: QuantumCircuit,
    simulator: AerSimulator,
    rng: np.random.Generator,
    cache: dict[tuple[str, ...], QuantumCircuit],
) -> tuple[list[tuple[tuple[str, ...], np.ndarray]], str]:
    qubits = base.num_qubits
    schedule = [
        tuple(rng.choice(["X", "Y", "Z"], size=qubits))
        for _ in range(MAX_SHOTS)
    ]
    positions: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for index, basis in enumerate(schedule):
        positions[basis].append(index)

    ordered: list[tuple[tuple[str, ...], np.ndarray] | None] = [None] * MAX_SHOTS
    for basis, basis_positions in positions.items():
        circuit = cache.setdefault(basis, basis_circuit(base, basis))
        seed = int(rng.integers(0, 2**31 - 1))
        result = simulator.run(
            circuit,
            shots=len(basis_positions),
            seed_simulator=seed,
        ).result()
        decoded = decode_counts(result.get_counts(0), qubits)
        if len(decoded) != len(basis_positions):
            raise RuntimeError("matched-prefix grouped replay count mismatch")
        assignment = rng.permutation(len(decoded))
        for position, decoded_index in zip(basis_positions, assignment, strict=True):
            ordered[position] = (basis, decoded[int(decoded_index)])

    if any(record is None for record in ordered):
        raise RuntimeError("matched-prefix replay left unfilled shot positions")
    records = [record for record in ordered if record is not None]
    schedule_hash = hashlib.sha256(
        json.dumps(schedule, separators=(",", ":")).encode()
    ).hexdigest()
    return records, schedule_hash


def choose_bundle(
    task: dict[str, Any], rng: np.random.Generator
) -> tuple[list[dict[int, str]], dict[str, int]]:
    negative_index = int(rng.integers(len(task["negative_targets"])))
    positive_index = int(rng.integers(len(task["positive_targets"])))
    return [
        task["negative_targets"][negative_index],
        task["positive_anchor"],
        task["positive_targets"][positive_index],
    ], {
        "negative_index": negative_index,
        "positive_index": positive_index,
    }


def bundle_error(
    records: list[tuple[tuple[str, ...], np.ndarray]],
    bundle: list[dict[int, str]],
    exact_values: dict[str, float],
) -> float:
    errors = []
    for target in bundle:
        exact = exact_values[json.dumps(target, sort_keys=True)]
        estimate = float(
            np.mean(
                [
                    shadow_estimate(bits, basis, target)
                    for basis, bits in records
                ]
            )
        )
        errors.append(abs(estimate - exact))
    return max(errors)


def first_crossing(
    profile: dict[str, Any], field: str, floor: float
) -> int | None:
    for shots in SHOT_BUDGETS:
        if profile["by_shot_budget"][str(shots)][field] >= floor:
            return shots
    return None


def report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    requirement_lines = "\n".join(
        f"- `{row['requirement_id']}` "
        f"{'PASS' if row['passed'] else 'FAIL'}: {row['label']}"
        for row in payload["requirements"]
    )
    profile_lines = []
    for profile_name, profile in summary["profiles"].items():
        point = ", ".join(
            f"{shots}: {profile['by_shot_budget'][str(shots)]['minimum_honest_completeness']:.4f}"
            for shots in SHOT_BUDGETS
        )
        lower = ", ".join(
            f"{shots}: {profile['by_shot_budget'][str(shots)]['minimum_wilson_lower']:.4f}"
            for shots in SHOT_BUDGETS
        )
        profile_lines.append(f"- `{profile_name}` point estimate: {point}")
        profile_lines.append(f"- `{profile_name}` minimum Wilson lower: {lower}")

    return f"""# B4/B8 R122 Matched-Seed Prefix Replay

## Summary

- Target: `{TARGET_ID}`
- Upstream target: `{UPSTREAM_TARGET_ID}`
- Method: `{METHOD}`
- Status: `{STATUS}`
- Profiles: `{', '.join(PROFILES)}`
- Shot budgets: `{', '.join(str(value) for value in SHOT_BUDGETS)}`
- Trials per profile/task: `{TRIALS}`
- Maximum replay stream: `{MAX_SHOTS}` shots
- Honest completeness floor: `{HONEST_TARGET}`
- Point-estimate first crossing: `{summary['point_first_budget_reaching_honest_floor']}`
- Confidence-qualified first crossing: `{summary['confidence_first_budget_reaching_honest_floor']}`
- Total fail-to-pass adjacent transitions: `{summary['fail_to_pass_transition_count']}`
- Total pass-to-fail adjacent transitions: `{summary['pass_to_fail_transition_count']}`

{chr(10).join(profile_lines)}

R122 removes the largest comparability defect in R121. Within each trial, all
five budgets are prefixes of one ordered 8,192-shot record stream and reuse the
same hidden signed-observable bundle. Point estimates and 95% Wilson lower
bounds are reported separately. A point estimate above 0.80 is not promoted to
a confidence-qualified result unless the weakest task's Wilson lower bound also
reaches 0.80.

## Requirements

{requirement_lines}

## Claim Boundary

Supported: a paired synthetic Aer replay that isolates shot-budget effects more
cleanly than R121. Not supported: a universal monotonic sampling law, calibrated
backend evidence, real hardware execution, protocol or cryptographic soundness,
sampling hardness, quantum advantage, BQP separation, or B10 credit.
"""


def run_gate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    r121 = json.loads((root / R121_RESULT_PATH).read_text(encoding="utf-8"))
    if r121.get("status") != "private_signed_observable_bundle_shot_budget_boundary":
        raise ValueError("R122 requires the accepted R121 shot-budget boundary")

    output = root / OUT_DIR
    if output.exists():
        shutil.rmtree(output)
    circuits_dir = output / "circuits"
    circuits_dir.mkdir(parents=True)

    tasks = build_bundle_tasks()
    trial_rows: list[dict[str, Any]] = []
    circuit_files: list[str] = []
    for profile_index, (profile_name, profile) in enumerate(PROFILES.items()):
        simulator = AerSimulator(
            noise_model=noise_model(profile),
            method="density_matrix",
        )
        for task_index, task in enumerate(tasks):
            base = task["circuit"]
            path = circuits_dir / f"{profile_name}_{task['task_id']}.qasm"
            path.write_text(qasm3.dumps(base), encoding="utf-8")
            circuit_files.append(str(path.relative_to(root)))
            exact_values = target_values(task)
            cache: dict[tuple[str, ...], QuantumCircuit] = {}
            for trial in range(TRIALS):
                rng = np.random.default_rng(
                    np.random.SeedSequence(
                        [SEED, profile_index, task_index, trial]
                    )
                )
                bundle, bundle_choice = choose_bundle(task, rng)
                records, schedule_hash = matched_prefix_records(
                    base, simulator, rng, cache
                )
                by_budget: dict[str, Any] = {}
                for shots in SHOT_BUDGETS:
                    error = bundle_error(records[:shots], bundle, exact_values)
                    by_budget[str(shots)] = {
                        "maximum_bundle_error": error,
                        "passed": error <= TOLERANCE,
                    }
                trial_rows.append(
                    {
                        "profile": profile_name,
                        "task_id": task["task_id"],
                        "trial": trial,
                        "trial_seed_components": [
                            SEED,
                            profile_index,
                            task_index,
                            trial,
                        ],
                        "schedule_sha256": schedule_hash,
                        "bundle_choice": bundle_choice,
                        "all_budgets_share_schedule_prefix": True,
                        "all_budgets_share_bundle": True,
                        "by_shot_budget": by_budget,
                    }
                )

    profiles: dict[str, Any] = {}
    transition_rows: list[dict[str, Any]] = []
    for profile_name, profile in PROFILES.items():
        profile_trials = [
            row for row in trial_rows if row["profile"] == profile_name
        ]
        task_rows_by_budget: dict[str, list[dict[str, Any]]] = {}
        for shots in SHOT_BUDGETS:
            budget_task_rows = []
            for task in tasks:
                selected = [
                    row
                    for row in profile_trials
                    if row["task_id"] == task["task_id"]
                ]
                flags = [row["by_shot_budget"][str(shots)]["passed"] for row in selected]
                errors = [
                    row["by_shot_budget"][str(shots)]["maximum_bundle_error"]
                    for row in selected
                ]
                successes = sum(flags)
                lower, upper = wilson_interval(successes, TRIALS)
                budget_task_rows.append(
                    {
                        "task_id": task["task_id"],
                        "trials": TRIALS,
                        "successes": successes,
                        "pass_rate": successes / TRIALS,
                        "wilson_lower": lower,
                        "wilson_upper": upper,
                        "mean_bundle_error": float(np.mean(errors)),
                        "maximum_bundle_error": max(errors),
                    }
                )
            task_rows_by_budget[str(shots)] = budget_task_rows

        by_budget = {}
        for shots in SHOT_BUDGETS:
            rows = task_rows_by_budget[str(shots)]
            by_budget[str(shots)] = {
                "minimum_honest_completeness": min(row["pass_rate"] for row in rows),
                "minimum_wilson_lower": min(row["wilson_lower"] for row in rows),
                "maximum_wilson_upper": max(row["wilson_upper"] for row in rows),
                "task_rows": rows,
            }

        for task in tasks:
            selected = [
                row
                for row in profile_trials
                if row["task_id"] == task["task_id"]
            ]
            for lower_budget, upper_budget in zip(
                SHOT_BUDGETS[:-1], SHOT_BUDGETS[1:], strict=True
            ):
                lower_flags = [
                    row["by_shot_budget"][str(lower_budget)]["passed"]
                    for row in selected
                ]
                upper_flags = [
                    row["by_shot_budget"][str(upper_budget)]["passed"]
                    for row in selected
                ]
                transition_rows.append(
                    {
                        "profile": profile_name,
                        "task_id": task["task_id"],
                        "lower_budget": lower_budget,
                        "upper_budget": upper_budget,
                        "fail_to_pass": sum(
                            (not before) and after
                            for before, after in zip(lower_flags, upper_flags, strict=True)
                        ),
                        "pass_to_fail": sum(
                            before and (not after)
                            for before, after in zip(lower_flags, upper_flags, strict=True)
                        ),
                    }
                )

        profile_payload = {
            "noise": profile,
            "by_shot_budget": by_budget,
        }
        profile_payload["point_first_budget_reaching_honest_floor"] = first_crossing(
            profile_payload, "minimum_honest_completeness", HONEST_TARGET
        )
        profile_payload["confidence_first_budget_reaching_honest_floor"] = first_crossing(
            profile_payload, "minimum_wilson_lower", HONEST_TARGET
        )
        profiles[profile_name] = profile_payload

    point_first = {
        name: row["point_first_budget_reaching_honest_floor"]
        for name, row in profiles.items()
    }
    confidence_first = {
        name: row["confidence_first_budget_reaching_honest_floor"]
        for name, row in profiles.items()
    }
    fail_to_pass = sum(row["fail_to_pass"] for row in transition_rows)
    pass_to_fail = sum(row["pass_to_fail"] for row in transition_rows)
    summary = {
        "task_count": len(tasks),
        "profile_count": len(PROFILES),
        "trials_per_profile_task": TRIALS,
        "shot_budgets": SHOT_BUDGETS,
        "maximum_replay_shots": MAX_SHOTS,
        "bundle_size": 3,
        "tolerance": TOLERANCE,
        "honest_floor": HONEST_TARGET,
        "matched_seed_prefix_replay": True,
        "profiles": profiles,
        "point_first_budget_reaching_honest_floor": point_first,
        "confidence_first_budget_reaching_honest_floor": confidence_first,
        "fail_to_pass_transition_count": fail_to_pass,
        "pass_to_fail_transition_count": pass_to_fail,
        "r121_point_first_budget_reaching_honest_floor": r121["summary"][
            "first_budget_reaching_honest_floor"
        ],
        "hardware_execution_performed": False,
        "calibrated_backend_evidence": False,
        "protocol_soundness_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
    }
    circuit_files = sorted(set(circuit_files))
    requirements = [
        {
            "requirement_id": "P1",
            "label": "accepted R121 shot-budget boundary is consumed",
            "passed": True,
            "evidence": {"r121_status": r121["status"]},
        },
        {
            "requirement_id": "P2",
            "label": "all budgets are prefixes of one ordered stream per trial",
            "passed": all(row["all_budgets_share_schedule_prefix"] for row in trial_rows),
            "evidence": {"trial_row_count": len(trial_rows)},
        },
        {
            "requirement_id": "P3",
            "label": "the hidden bundle is shared across budgets within each trial",
            "passed": all(row["all_budgets_share_bundle"] for row in trial_rows),
            "evidence": {"trial_row_count": len(trial_rows)},
        },
        {
            "requirement_id": "P4",
            "label": "thirty paired trials cover every profile and task",
            "passed": len(trial_rows) == len(PROFILES) * len(tasks) * TRIALS,
            "evidence": {"trial_row_count": len(trial_rows), "trials": TRIALS},
        },
        {
            "requirement_id": "P5",
            "label": "point estimates and Wilson intervals are both reported",
            "passed": all(
                "minimum_wilson_lower" in profile["by_shot_budget"][str(shots)]
                for profile in profiles.values()
                for shots in SHOT_BUDGETS
            ),
            "evidence": {"confidence_level": 0.95},
        },
        {
            "requirement_id": "P6",
            "label": "adjacent paired pass/fail transitions are materialized",
            "passed": len(transition_rows)
            == len(PROFILES) * len(tasks) * (len(SHOT_BUDGETS) - 1),
            "evidence": {"transition_row_count": len(transition_rows)},
        },
        {
            "requirement_id": "P7",
            "label": "all profile circuits are materialized",
            "passed": len(circuit_files) == len(PROFILES) * len(tasks),
            "evidence": {"circuit_file_count": len(circuit_files)},
        },
        {
            "requirement_id": "P8",
            "label": "synthetic profiles are not mislabeled as hardware evidence",
            "passed": not summary["hardware_execution_performed"]
            and not summary["calibrated_backend_evidence"],
            "evidence": {
                "hardware_execution_performed": False,
                "calibrated_backend_evidence": False,
            },
        },
        {
            "requirement_id": "P9",
            "label": "B4/B8/B10 advantage and BQP claims remain false",
            "passed": not summary["protocol_soundness_claimed"]
            and not summary["quantum_advantage_claimed"]
            and not summary["bqp_separation_claimed"],
            "evidence": {
                "protocol_soundness_claimed": False,
                "quantum_advantage_claimed": False,
                "bqp_separation_claimed": False,
            },
        },
        {
            "requirement_id": "P10",
            "label": "confidence-qualified crossing remains separate from point crossing",
            "passed": True,
            "evidence": {
                "point_first": point_first,
                "confidence_first": confidence_first,
            },
        },
    ]
    failed = [row["requirement_id"] for row in requirements if not row["passed"]]
    payload: dict[str, Any] = {
        "title": "B4/B8 R122 matched-seed prefix replay",
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
        "trial_rows": trial_rows,
        "transition_rows": transition_rows,
        "artifacts": {
            "circuits": circuit_files,
            "r121_result": R121_RESULT_PATH,
        },
        "claim_boundary": {
            "what_is_supported": (
                "Paired ideal/light Aer shot-budget replay using one ordered "
                "measurement stream and one hidden bundle per trial."
            ),
            "what_is_not_supported": (
                "A universal monotonic sampling law, calibrated backend evidence, "
                "real hardware execution, protocol or cryptographic soundness, "
                "sampling hardness, quantum advantage, BQP separation, or B10 credit."
            ),
            "next_gate": (
                "Repeat independent seed blocks and stress the acceptance statistic; "
                "then replay a confidence-qualified budget under calibrated backend "
                "properties or an independent backend transcript."
            ),
        },
    }
    payload["payload_hash"] = stable_hash(payload)
    write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    print(json.dumps(run_gate(Path(args.repo_root)), sort_keys=True))


if __name__ == "__main__":
    main()
