#!/usr/bin/env python3
"""Gate B3 measurement-rescue evidence against B10 same-access requirements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b3_b10_same_access_measurement_rescue_gate_v0"
STATUS = "same_access_measurement_rescue_failed_not_advantage_claim"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def as_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("summary", {})


def gate_row(gate_id: str, label: str, passed: bool, evidence: str, required_next: str) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
        "required_next": required_next,
    }


def build_report(results_dir: Path) -> dict[str, Any]:
    grouped = read_json(results_dir / "B3_grouped_covariance_shot_floor_v0.json")
    derivative = read_json(results_dir / "B3_chemical_state_prep_derivative_boundary_v0.json")
    compiled = read_json(results_dir / "B3_compiled_ucc_adapt_covariance_pilot_v0.json")
    cross = read_json(results_dir / "B3_cross_molecule_ucc_adapt_pressure_v0.json")
    fci = read_json(results_dir / "B10_t1_d5_b3_fci_reference_table_v0.json")
    comparison = read_json(results_dir / "B10_t1_b3_b5_denominator_boundary_comparison_v0.json")
    access = read_json(results_dir / "B10_t1_asymptotic_access_contract_v0.json")

    grouped_s = as_summary(grouped)
    derivative_s = as_summary(derivative)
    compiled_s = as_summary(compiled)
    cross_s = as_summary(cross)
    fci_s = as_summary(fci)
    comparison_s = as_summary(comparison)
    access_s = as_summary(access)

    max_optimizer_shots = int(cross_s.get("max_optimizer_loop_total_shots_lower_bound", 0))
    max_optimizer_2q = int(cross_s.get("max_optimizer_loop_two_qubit_executions_lower_bound", 0))
    denominator_wins = int(cross_s.get("selected_ci_larger_basis_denominator_beaten_count", -1))
    fci_instances = int(fci_s.get("instance_count", 0))
    grouped_instances = int(grouped_s.get("instance_count", 0))
    derivative_instances = int(derivative_s.get("instance_count", 0))
    pressure_instances = int(cross_s.get("instance_count", 0))

    gates = [
        gate_row(
            "M1",
            "Same molecule rows exist across grouped covariance, derivative, pressure, and FCI tables",
            grouped_instances == derivative_instances == pressure_instances == fci_instances == 4,
            (
                f"grouped={grouped_instances}; derivative={derivative_instances}; "
                f"pressure={pressure_instances}; fci={fci_instances}"
            ),
            "Keep all future rescue attempts row-aligned across B3 and B10 denominator artifacts.",
        ),
        gate_row(
            "M2",
            "Grouped covariance is represented rather than independent-term-only measurement",
            grouped_s.get("grouped_covariance_included") is True
            and float(grouped_s.get("max_grouped_covariance_reduction_vs_previous_independent_floor", 0.0)) > 1.0,
            (
                "grouped_covariance_included="
                f"{grouped_s.get('grouped_covariance_included')}; "
                "max_reduction="
                f"{grouped_s.get('max_grouped_covariance_reduction_vs_previous_independent_floor')}"
            ),
            "Retain grouped covariance and compare against non-QWC or classical-shadow style alternatives.",
        ),
        gate_row(
            "M3",
            "Derivative-level observable error propagation is included",
            derivative_s.get("derivative_error_propagation_included") is True
            and float(derivative_s.get("max_derivative_shot_floor_inflation_vs_center_energy_floor", 0.0))
            >= 10000.0,
            (
                "derivative_error_propagation_included="
                f"{derivative_s.get('derivative_error_propagation_included')}; "
                "max_inflation="
                f"{derivative_s.get('max_derivative_shot_floor_inflation_vs_center_energy_floor')}"
            ),
            "Keep derivative error propagation inside every positive-route cost ledger.",
        ),
        gate_row(
            "M4",
            "Compiled-state covariance pilot exists",
            compiled_s.get("compiled_ucc_adapt_covariance_included") is True
            and int(compiled_s.get("instance_count", 0)) >= 1,
            (
                "compiled_covariance="
                f"{compiled_s.get('compiled_ucc_adapt_covariance_included')}; "
                f"instances={compiled_s.get('instance_count')}"
            ),
            "Extend the compiled-state covariance from one pilot row to all reaction rows.",
        ),
        gate_row(
            "M5",
            "Full cross-molecule compiled-state covariance exists",
            cross_s.get("full_compiled_state_covariance_computed") is True,
            (
                "full_compiled_state_covariance_computed="
                f"{cross_s.get('full_compiled_state_covariance_computed')}; "
                f"sampled_pressure_rows={pressure_instances}"
            ),
            "Compute full compiled-state covariance or a stronger bounded substitute for every molecule.",
        ),
        gate_row(
            "M6",
            "Multi-parameter or converged chemistry ansatz exists",
            int(cross_s.get("ansatz_parameter_count", 0)) > 1
            and cross_s.get("converged_vqe_or_adapt_energy") is True,
            (
                f"ansatz_parameter_count={cross_s.get('ansatz_parameter_count')}; "
                f"converged_vqe_or_adapt_energy={cross_s.get('converged_vqe_or_adapt_energy')}"
            ),
            "Move beyond the one-parameter UCC double seed and record convergence evidence.",
        ),
        gate_row(
            "M7",
            "Selected-CI/FCI larger-basis denominator is beaten",
            denominator_wins > 0,
            f"selected_ci_larger_basis_denominator_beaten_count={denominator_wins}",
            "Produce at least one same-access denominator win after measurement, derivative, and optimizer costs.",
        ),
        gate_row(
            "M8",
            "Optimizer-loop budget is below the positive-route stress ceiling",
            0 < max_optimizer_shots <= 10**12,
            (
                f"max_optimizer_loop_total_shots_lower_bound={max_optimizer_shots}; "
                f"max_optimizer_loop_two_qubit_executions_lower_bound={max_optimizer_2q}"
            ),
            "Reduce optimizer-loop shots by at least three orders of magnitude before reopening a positive claim.",
        ),
        gate_row(
            "M9",
            "B10 access contract allows a current B3 sampling bridge",
            access_s.get("sampling_access_bridge_refuted_for_current_evidence") is False
            and comparison_s.get("b3_demoted") is False,
            (
                "sampling_access_bridge_refuted_for_current_evidence="
                f"{access_s.get('sampling_access_bridge_refuted_for_current_evidence')}; "
                f"b3_demoted={comparison_s.get('b3_demoted')}"
            ),
            "Replace the current B3 sampling bridge with a same-access route that B10 no longer rejects.",
        ),
        gate_row(
            "M10",
            "Forbidden claims remain absent",
            all(
                item is False
                for item in [
                    grouped_s.get("quantum_advantage_claimed"),
                    derivative_s.get("quantum_advantage_claimed"),
                    cross_s.get("quantum_advantage_claimed"),
                    comparison_s.get("quantum_advantage_claimed"),
                    comparison_s.get("bqp_separation_claimed"),
                ]
            ),
            (
                f"B3 grouped/derivative/cross advantage claims="
                f"{grouped_s.get('quantum_advantage_claimed')}/"
                f"{derivative_s.get('quantum_advantage_claimed')}/"
                f"{cross_s.get('quantum_advantage_claimed')}; "
                f"B10 advantage/BQP={comparison_s.get('quantum_advantage_claimed')}/"
                f"{comparison_s.get('bqp_separation_claimed')}"
            ),
            "Keep forbidden claims absent until a same-access denominator win and theorem boundary exist.",
        ),
    ]

    passed = [row for row in gates if row["passed"]]
    failed = [row for row in gates if not row["passed"]]
    validation_errors: list[str] = []
    if denominator_wins != 0:
        validation_errors.append("current B3 pressure unexpectedly reports denominator wins")
    if cross_s.get("demotion_recommended") is not True:
        validation_errors.append("current B3 pressure should remain demoted")
    if comparison_s.get("b3_demoted") is not True:
        validation_errors.append("B10 comparison should keep B3 demoted for this gate")
    if comparison_s.get("quantum_advantage_claimed") is not False:
        validation_errors.append("B10 comparison must not claim quantum advantage")

    return {
        "benchmark_id": "B3_B10",
        "problem_ids": [49, 11],
        "title": "B3/B10 Same-Access Measurement Rescue Gate",
        "version": "0.1",
        "status": STATUS,
        "method": METHOD,
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B3", "B10"],
        "source_methods": {
            "b3_grouped_covariance": grouped.get("method"),
            "b3_derivative_boundary": derivative.get("method"),
            "b3_compiled_ucc_adapt_pilot": compiled.get("method"),
            "b3_cross_molecule_pressure": cross.get("method"),
            "b10_b3_fci_reference": fci.get("method"),
            "b10_b3_b5_comparison": comparison.get("method"),
            "b10_asymptotic_access_contract": access.get("method"),
        },
        "same_access_gate_count": len(gates),
        "passed_gate_count": len(passed),
        "failed_gate_count": len(failed),
        "failed_gate_ids": [row["gate_id"] for row in failed],
        "same_access_measurement_rescue_ready": False,
        "b3_demoted": True,
        "summary": {
            "row_aligned_instance_count": min(grouped_instances, derivative_instances, pressure_instances, fci_instances),
            "grouped_covariance_max_reduction": grouped_s.get(
                "max_grouped_covariance_reduction_vs_previous_independent_floor"
            ),
            "derivative_shot_floor_inflation": derivative_s.get(
                "max_derivative_shot_floor_inflation_vs_center_energy_floor"
            ),
            "compiled_pilot_instance_count": compiled_s.get("instance_count"),
            "cross_molecule_pressure_instance_count": pressure_instances,
            "full_compiled_state_covariance_computed": cross_s.get(
                "full_compiled_state_covariance_computed"
            ),
            "ansatz_parameter_count": cross_s.get("ansatz_parameter_count"),
            "converged_vqe_or_adapt_energy": cross_s.get("converged_vqe_or_adapt_energy"),
            "selected_ci_larger_basis_denominator_beaten_count": denominator_wins,
            "max_optimizer_loop_total_shots_lower_bound": max_optimizer_shots,
            "max_optimizer_loop_two_qubit_executions_lower_bound": max_optimizer_2q,
            "b10_sampling_access_bridge_refuted_for_current_evidence": access_s.get(
                "sampling_access_bridge_refuted_for_current_evidence"
            ),
            "b10_b3_demoted": comparison_s.get("b3_demoted"),
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "reaction_dynamics_solution_claimed": False,
            "validation_error_count": len(validation_errors),
        },
        "gates": gates,
        "claim_boundary": {
            "what_is_supported": (
                "B3 has row-aligned denominator pressure, grouped covariance, derivative propagation, "
                "and a one-row compiled covariance pilot, but the same-access measurement rescue fails."
            ),
            "what_is_not_supported": (
                "This is not a molecular reaction dynamics solution, not a quantum advantage claim, "
                "not a BQP separation, and not a positive same-access B3 route."
            ),
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "reaction_dynamics_solution_claimed": False,
        },
        "next_required_artifacts": [
            "full cross-molecule compiled-state covariance or stronger measurement estimator",
            "multi-parameter converged UCC/ADAPT/VQE or alternative chemistry state-prep evidence",
            "same-access denominator win after derivative and optimizer-loop costs",
            "B10 access-contract update showing the B3 sampling bridge is no longer refuted",
        ],
        "validation_errors": validation_errors,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# B3/B10 Same-Access Measurement Rescue Gate v0.1",
        "",
        f"- Status: {report['status']}",
        f"- Method: {report['method']}",
        f"- Source target: {report['source_target_id']}",
        f"- Same-access gates passed / failed: {report['passed_gate_count']} / {report['failed_gate_count']}",
        f"- Failed gate IDs: {', '.join(report['failed_gate_ids'])}",
        f"- Measurement rescue ready: {report['same_access_measurement_rescue_ready']}",
        f"- B3 remains demoted: {report['b3_demoted']}",
        f"- Denominator wins: {report['summary']['selected_ci_larger_basis_denominator_beaten_count']}",
        f"- Max optimizer-loop shots lower bound: {report['summary']['max_optimizer_loop_total_shots_lower_bound']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Gate Table",
        "",
        "| gate | pass | evidence | required next |",
        "|---|---:|---|---|",
    ]
    for row in report["gates"]:
        lines.append(
            f"| {row['gate_id']} {row['label']} | {row['passed']} | "
            f"{row['evidence']} | {row['required_next']} |"
        )
    lines.extend(["", "## Claim Boundary", ""])
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Next Required Artifacts", ""])
    for item in report["next_required_artifacts"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B3_B10_same_access_measurement_rescue_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B3_B10_same_access_measurement_rescue_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = build_report(args.results_dir)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2 if args.pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(markdown(report), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": report["status"],
                "method": report["method"],
                "passed_gate_count": report["passed_gate_count"],
                "failed_gate_count": report["failed_gate_count"],
                "failed_gate_ids": report["failed_gate_ids"],
                "same_access_measurement_rescue_ready": report[
                    "same_access_measurement_rescue_ready"
                ],
                "validation_errors": report["validation_errors"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if report["validation_errors"]:
        raise SystemExit("B3/B10 same-access measurement rescue gate validation failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
