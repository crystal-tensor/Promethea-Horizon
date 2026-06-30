#!/usr/bin/env python3
"""T-B3-013: convert the failed B3/B10 rescue gate into a negative boundary note."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b3_b10_same_access_negative_boundary_note_v0"
STATUS = "same_access_negative_boundary_note_not_advantage_claim"
SOURCE_METHOD = "b3_b10_same_access_measurement_rescue_gate_v0"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def make_condition(cond_id: str, label: str, satisfied: bool, evidence: str, reopen_requirement: str) -> dict[str, Any]:
    return {
        "condition_id": cond_id,
        "label": label,
        "satisfied": bool(satisfied),
        "evidence": evidence,
        "reopen_requirement": reopen_requirement,
    }


def build_note(source_path: Path) -> dict[str, Any]:
    source = load_json(source_path)
    summary = source.get("summary", {})
    failed_gate_ids = source.get("failed_gate_ids", [])
    source_claims = source.get("claim_boundary", {})

    conditions = [
        make_condition(
            "N1",
            "source rescue gate is the expected failed B3/B10 gate",
            source.get("method") == SOURCE_METHOD
            and source.get("status") == "same_access_measurement_rescue_failed_not_advantage_claim",
            f"method={source.get('method')}; status={source.get('status')}",
            "Re-run the source gate with a new version if the upstream evidence changes.",
        ),
        make_condition(
            "N2",
            "same-access rescue is explicitly not ready",
            source.get("same_access_measurement_rescue_ready") is False,
            f"same_access_measurement_rescue_ready={source.get('same_access_measurement_rescue_ready')}",
            "Set readiness true only after all same-access measurement gates pass.",
        ),
        make_condition(
            "N3",
            "failed gate set identifies the exact blockers",
            failed_gate_ids == ["M5", "M6", "M7", "M8", "M9"],
            f"failed_gate_ids={failed_gate_ids}",
            "Replace M5-M9 with passing evidence or update the negative note with a new blocker set.",
        ),
        make_condition(
            "N4",
            "full compiled-state covariance is missing",
            summary.get("full_compiled_state_covariance_computed") is False,
            f"full_compiled_state_covariance_computed={summary.get('full_compiled_state_covariance_computed')}",
            "Compute full compiled-state covariance, or a stronger bounded substitute, for every molecule row.",
        ),
        make_condition(
            "N5",
            "state preparation remains one-parameter and unconverged",
            int(summary.get("ansatz_parameter_count", 0)) <= 1
            and summary.get("converged_vqe_or_adapt_energy") is False,
            (
                f"ansatz_parameter_count={summary.get('ansatz_parameter_count')}; "
                f"converged_vqe_or_adapt_energy={summary.get('converged_vqe_or_adapt_energy')}"
            ),
            "Provide multi-parameter UCCSD/ADAPT/VQE or alternative chemistry state-preparation convergence evidence.",
        ),
        make_condition(
            "N6",
            "selected-CI/FCI denominator wins are zero",
            int(summary.get("selected_ci_larger_basis_denominator_beaten_count", -1)) == 0,
            f"selected_ci_larger_basis_denominator_beaten_count={summary.get('selected_ci_larger_basis_denominator_beaten_count')}",
            "Produce at least one same-access denominator win after derivative and optimizer-loop costs.",
        ),
        make_condition(
            "N7",
            "optimizer-loop shot floor is still prohibitive",
            int(summary.get("max_optimizer_loop_total_shots_lower_bound", 0)) >= 10**12,
            f"max_optimizer_loop_total_shots_lower_bound={summary.get('max_optimizer_loop_total_shots_lower_bound')}",
            "Reduce optimizer-loop shot demand below the positive-route stress ceiling under the same target error.",
        ),
        make_condition(
            "N8",
            "B10 access bridge still rejects the current evidence",
            summary.get("b10_sampling_access_bridge_refuted_for_current_evidence") is True,
            (
                "b10_sampling_access_bridge_refuted_for_current_evidence="
                f"{summary.get('b10_sampling_access_bridge_refuted_for_current_evidence')}"
            ),
            "Update the B10 same-access contract only after B3 has full covariance, state-prep, denominator, and optimizer evidence.",
        ),
        make_condition(
            "N9",
            "forbidden claims are all false",
            source_claims.get("reaction_dynamics_solution_claimed") is False
            and source_claims.get("quantum_advantage_claimed") is False
            and source_claims.get("bqp_separation_claimed") is False,
            (
                f"reaction_dynamics_solution_claimed={source_claims.get('reaction_dynamics_solution_claimed')}; "
                f"quantum_advantage_claimed={source_claims.get('quantum_advantage_claimed')}; "
                f"bqp_separation_claimed={source_claims.get('bqp_separation_claimed')}"
            ),
            "Keep forbidden claims false until an independently reproduced same-access positive route exists.",
        ),
    ]

    satisfied = [row for row in conditions if row["satisfied"]]
    unsatisfied = [row for row in conditions if not row["satisfied"]]
    validation_errors = [row["condition_id"] for row in unsatisfied]
    return {
        "benchmark_id": "B3_B10",
        "method": METHOD,
        "status": STATUS,
        "source_result": str(source_path),
        "source_method": source.get("method"),
        "source_status": source.get("status"),
        "source_target_id": source.get("source_target_id"),
        "problem_ids": source.get("problem_ids", [49, 11]),
        "dependency_benchmarks": ["B3", "B10"],
        "negative_boundary_conditions": conditions,
        "condition_count": len(conditions),
        "satisfied_condition_count": len(satisfied),
        "unsatisfied_condition_count": len(unsatisfied),
        "validation_errors": validation_errors,
        "demotion_decision": {
            "b3_current_route_demoted": True,
            "b10_t1_same_access_positive_route_available": False,
            "reopen_only_if_conditions_replaced": ["N4", "N5", "N6", "N7", "N8"],
        },
        "metrics": {
            "passed_source_gate_count": source.get("passed_gate_count"),
            "failed_source_gate_count": source.get("failed_gate_count"),
            "failed_source_gate_ids": failed_gate_ids,
            "row_aligned_instance_count": summary.get("row_aligned_instance_count"),
            "compiled_pilot_instance_count": summary.get("compiled_pilot_instance_count"),
            "cross_molecule_pressure_instance_count": summary.get("cross_molecule_pressure_instance_count"),
            "selected_ci_larger_basis_denominator_beaten_count": summary.get(
                "selected_ci_larger_basis_denominator_beaten_count"
            ),
            "max_optimizer_loop_total_shots_lower_bound": summary.get(
                "max_optimizer_loop_total_shots_lower_bound"
            ),
            "max_optimizer_loop_two_qubit_executions_lower_bound": summary.get(
                "max_optimizer_loop_two_qubit_executions_lower_bound"
            ),
            "full_compiled_state_covariance_computed": summary.get("full_compiled_state_covariance_computed"),
            "ansatz_parameter_count": summary.get("ansatz_parameter_count"),
            "converged_vqe_or_adapt_energy": summary.get("converged_vqe_or_adapt_energy"),
            "b10_sampling_access_bridge_refuted_for_current_evidence": summary.get(
                "b10_sampling_access_bridge_refuted_for_current_evidence"
            ),
        },
        "claim_boundary": {
            "reaction_dynamics_solution_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "positive_same_access_route_claimed": False,
            "what_is_supported": (
                "The current B3 same-access measurement route should stay demoted until M5-M9 "
                "are replaced by full covariance, state-prep, denominator-win, optimizer, and B10 access evidence."
            ),
            "what_is_not_supported": (
                "This note is not a proof that B3 is impossible, not a molecular reaction dynamics solution, "
                "not a quantum advantage claim, and not a BQP separation."
            ),
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# B3/B10 Same-Access Negative Boundary Note",
        "",
        f"- Benchmark: `{payload['benchmark_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Source: `{payload['source_result']}`",
        f"- Conditions satisfied/unsatisfied: {payload['satisfied_condition_count']} / {payload['unsatisfied_condition_count']}",
        "",
        "## Decision",
        "",
        (
            "The current B3 measurement-rescue route remains demoted. This note does not "
            "claim that molecular reaction dynamics has no quantum route; it says the "
            "specific same-access route currently in the repository is not allowed to "
            "be promoted until the named blockers are replaced."
        ),
        "",
        "## Metrics",
        "",
    ]
    for key, value in payload["metrics"].items():
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Boundary Conditions",
        "",
        "| ID | Satisfied | Condition | Evidence | Reopen requirement |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in payload["negative_boundary_conditions"]:
        mark = "yes" if row["satisfied"] else "no"
        lines.append(
            f"| {row['condition_id']} | {mark} | {row['label']} | {row['evidence']} | {row['reopen_requirement']} |"
        )
    lines.extend([
        "",
        "## Claim Boundary",
        "",
        "- No molecular reaction dynamics solution is claimed.",
        "- No quantum advantage is claimed.",
        "- No BQP separation is claimed.",
        "- No positive same-access B3 route is claimed.",
        "- Reopen B3 only with full covariance, multi-parameter/converged state preparation, denominator wins, acceptable optimizer-loop costs, and B10 access-contract acceptance.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-result",
        type=Path,
        default=Path("results/B3_B10_same_access_measurement_rescue_gate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B3_B10_same_access_negative_boundary_note_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B3_B10_same_access_negative_boundary_note.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_note(args.source_result)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload, args.markdown_output)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "satisfied_condition_count": payload["satisfied_condition_count"],
                "unsatisfied_condition_count": payload["unsatisfied_condition_count"],
                "validation_errors": payload["validation_errors"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
