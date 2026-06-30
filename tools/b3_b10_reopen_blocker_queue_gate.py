#!/usr/bin/env python3
"""Build a PR-sized reopen blocker queue for the demoted B3/B10 route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b3_b10_reopen_blocker_queue_gate_v0"
STATUS = "b3_b10_reopen_blocker_queue_open_no_positive_route"
MODEL_STATUS = "failed_m5_m9_gates_partitioned_into_reopen_pr_packets"
VERSION = "0.1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        payload,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
        sort_keys=True,
    )
    path.write_text(text + "\n", encoding="utf-8")


def packet(
    packet_id: str,
    blocks_gate: str,
    owner_role: str,
    required_artifacts: list[str],
    acceptance_rule: str,
    current_evidence: dict[str, Any],
    downstream_gate: str,
) -> dict[str, Any]:
    return {
        "packet_id": packet_id,
        "blocks_gate": blocks_gate,
        "owner_role": owner_role,
        "required_artifacts": required_artifacts,
        "acceptance_rule": acceptance_rule,
        "current_evidence": current_evidence,
        "downstream_gate": downstream_gate,
    }


def gate_row(gate_id: str, label: str, passed: bool, evidence: dict[str, Any], rule: str) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
        "acceptance_rule": rule,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    rescue = load_json(args.rescue_result)
    negative = load_json(args.negative_note)
    summary = rescue["summary"]
    metrics = negative["metrics"]
    failed_gate_ids = rescue["failed_gate_ids"]

    packets = [
        packet(
            "B3-R1-full-compiled-covariance",
            "M5",
            "chemistry_measurement_agent",
            [
                "compiled-state covariance tables for all four B3 reaction-coordinate rows",
                "state-preparation circuit provenance for every row",
                "grouped observable variance/covariance ledger",
                "derivative-level shot floor after covariance propagation",
                "validation rows comparing sampled covariance against exact or high-confidence references",
            ],
            "M5 passes only if full_compiled_state_covariance_computed becomes true for all row-aligned molecules.",
            {
                "current_full_compiled_state_covariance_computed": summary[
                    "full_compiled_state_covariance_computed"
                ],
                "current_compiled_pilot_instance_count": summary["compiled_pilot_instance_count"],
                "row_aligned_instance_count": summary["row_aligned_instance_count"],
            },
            "rerun b3_b10_same_access_measurement_rescue_gate_v0",
        ),
        packet(
            "B3-R2-multiparameter-converged-state-prep",
            "M6",
            "chemistry_state_prep_agent",
            [
                "multi-parameter UCCSD, ADAPT, VQE, or alternative ansatz specification",
                "energy convergence evidence for each molecule row",
                "two-qubit gate and preparation-repetition cost ledger",
                "optimizer evaluation count and stopping criterion",
                "negative-control comparison against the one-parameter pilot",
            ],
            "M6 passes only if ansatz_parameter_count > 1 and converged_vqe_or_adapt_energy is true.",
            {
                "current_ansatz_parameter_count": summary["ansatz_parameter_count"],
                "current_converged_vqe_or_adapt_energy": summary[
                    "converged_vqe_or_adapt_energy"
                ],
            },
            "rerun b3_b10_same_access_measurement_rescue_gate_v0",
        ),
        packet(
            "B3-R3-same-access-denominator-win",
            "M7",
            "baseline_adversary_agent",
            [
                "selected-CI/FCI or stronger classical denominator at the same active-space access level",
                "quantum measurement and state-preparation costs charged on the same rows",
                "row-level win/loss table after derivative and optimizer costs",
                "independent reproduction script for the denominator comparison",
                "explicit non-win rows retained rather than filtered out",
            ],
            "M7 passes only if selected_ci_larger_basis_denominator_beaten_count is at least 1 under same-access accounting.",
            {
                "current_selected_ci_larger_basis_denominator_beaten_count": summary[
                    "selected_ci_larger_basis_denominator_beaten_count"
                ],
            },
            "rerun B10 denominator boundary comparison and B3/B10 rescue gate",
        ),
        packet(
            "B3-R4-optimizer-loop-cost-collapse",
            "M8",
            "measurement_cost_agent",
            [
                "new measurement estimator or optimizer protocol reducing total shots",
                "same target observable error and derivative propagation",
                "optimizer-loop multiplier and evaluation-count evidence",
                "two-qubit execution ledger after state-preparation costs",
                "stress run proving the reduction is not a row-selection artifact",
            ],
            "M8 passes only if max optimizer-loop shots fall below 1e12 under the same target error.",
            {
                "current_max_optimizer_loop_total_shots_lower_bound": summary[
                    "max_optimizer_loop_total_shots_lower_bound"
                ],
                "current_max_optimizer_loop_two_qubit_executions_lower_bound": summary[
                    "max_optimizer_loop_two_qubit_executions_lower_bound"
                ],
            },
            "rerun b3_b10_same_access_measurement_rescue_gate_v0",
        ),
        packet(
            "B3-R5-b10-access-contract-acceptance",
            "M9",
            "theory_access_contract_agent",
            [
                "B10 same-access contract update consuming B3-R1 through B3-R4",
                "explicit access model for sampling, state preparation, or oracle assumptions",
                "proof-obligation note explaining what is and is not separated",
                "negative-boundary cases where the access bridge still fails",
                "claim-boundary update forbidding BQP or advantage claims without denominator wins",
            ],
            "M9 passes only if B10 no longer refutes the B3 sampling/access bridge for current evidence.",
            {
                "current_b10_sampling_access_bridge_refuted": summary[
                    "b10_sampling_access_bridge_refuted_for_current_evidence"
                ],
                "current_b3_demoted": summary["b10_b3_demoted"],
            },
            "rerun B10 asymptotic access contract and B3/B10 rescue gate",
        ),
    ]

    requirements = [
        gate_row(
            "Q1",
            "Source rescue gate is the current failed B3/B10 same-access gate",
            rescue.get("method") == "b3_b10_same_access_measurement_rescue_gate_v0"
            and failed_gate_ids == ["M5", "M6", "M7", "M8", "M9"],
            {
                "source_method": rescue.get("method"),
                "source_status": rescue.get("status"),
                "failed_gate_ids": failed_gate_ids,
            },
            "Queue must be built from the current M5-M9 failed rescue gate.",
        ),
        gate_row(
            "Q2",
            "Negative boundary note is satisfied and aligned",
            negative.get("method") == "b3_b10_same_access_negative_boundary_note_v0"
            and negative.get("unsatisfied_condition_count") == 0
            and negative["metrics"]["failed_source_gate_ids"] == failed_gate_ids,
            {
                "negative_method": negative.get("method"),
                "unsatisfied_condition_count": negative.get("unsatisfied_condition_count"),
                "failed_source_gate_ids": negative["metrics"]["failed_source_gate_ids"],
            },
            "Negative boundary note must identify the same blocker set.",
        ),
        gate_row(
            "Q3",
            "Every failed M gate has exactly one PR packet",
            [row["blocks_gate"] for row in packets] == failed_gate_ids,
            {
                "packet_count": len(packets),
                "packet_ids": [row["packet_id"] for row in packets],
                "blocks_gate_sequence": [row["blocks_gate"] for row in packets],
            },
            "M5-M9 must map one-to-one to B3-R1 through B3-R5.",
        ),
        gate_row(
            "Q4",
            "Current blocker metrics remain negative",
            summary["selected_ci_larger_basis_denominator_beaten_count"] == 0
            and summary["full_compiled_state_covariance_computed"] is False
            and summary["converged_vqe_or_adapt_energy"] is False
            and summary["b10_sampling_access_bridge_refuted_for_current_evidence"] is True,
            {
                "denominator_wins": summary["selected_ci_larger_basis_denominator_beaten_count"],
                "full_covariance": summary["full_compiled_state_covariance_computed"],
                "converged_state_prep": summary["converged_vqe_or_adapt_energy"],
                "b10_refutes_bridge": summary[
                    "b10_sampling_access_bridge_refuted_for_current_evidence"
                ],
            },
            "Do not reopen B3 while the current evidence still fails M5-M9.",
        ),
        gate_row(
            "Q5",
            "Forbidden claims remain absent",
            all(
                rescue["claim_boundary"].get(key) is False
                for key in [
                    "reaction_dynamics_solution_claimed",
                    "quantum_advantage_claimed",
                    "bqp_separation_claimed",
                ]
            ),
            {
                "reaction_dynamics_solution_claimed": rescue["claim_boundary"][
                    "reaction_dynamics_solution_claimed"
                ],
                "quantum_advantage_claimed": rescue["claim_boundary"][
                    "quantum_advantage_claimed"
                ],
                "bqp_separation_claimed": rescue["claim_boundary"][
                    "bqp_separation_claimed"
                ],
            },
            "Queue artifact must not promote a demoted route into a positive claim.",
        ),
    ]

    passed_count = sum(1 for row in requirements if row["passed"])
    report = {
        "benchmark_id": "B3_B10",
        "problem_ids": [49, 11],
        "title": "B3/B10 Reopen Blocker Queue Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_rescue_result": str(args.rescue_result),
        "source_negative_note": str(args.negative_note),
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B3", "B10"],
        "summary": {
            "failed_source_gate_ids": failed_gate_ids,
            "packet_count": len(packets),
            "packet_ids": [row["packet_id"] for row in packets],
            "requirement_count": len(requirements),
            "passed_requirement_count": passed_count,
            "failed_requirement_count": len(requirements) - passed_count,
            "failed_requirement_ids": [row["gate_id"] for row in requirements if not row["passed"]],
            "row_aligned_instance_count": summary["row_aligned_instance_count"],
            "compiled_pilot_instance_count": summary["compiled_pilot_instance_count"],
            "full_compiled_state_covariance_computed": summary[
                "full_compiled_state_covariance_computed"
            ],
            "ansatz_parameter_count": summary["ansatz_parameter_count"],
            "converged_vqe_or_adapt_energy": summary["converged_vqe_or_adapt_energy"],
            "selected_ci_larger_basis_denominator_beaten_count": summary[
                "selected_ci_larger_basis_denominator_beaten_count"
            ],
            "max_optimizer_loop_total_shots_lower_bound": summary[
                "max_optimizer_loop_total_shots_lower_bound"
            ],
            "b10_sampling_access_bridge_refuted_for_current_evidence": summary[
                "b10_sampling_access_bridge_refuted_for_current_evidence"
            ],
            "b3_reopen_ready": False,
            "positive_same_access_route_available": False,
        },
        "requirements": requirements,
        "reopen_packets": packets,
        "claim_boundary": {
            "reopen_queue_built": True,
            "b3_reopen_ready": False,
            "positive_same_access_route_claimed": False,
            "reaction_dynamics_solution_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "what_is_supported": (
                "The B3/B10 failed M5-M9 gates are now partitioned into five PR-sized reopen packets "
                "with concrete artifacts and acceptance rules."
            ),
            "what_is_not_supported": (
                "This queue does not add new chemistry evidence, does not reopen B3, and does not "
                "claim a reaction-dynamics solution, quantum advantage, or BQP separation."
            ),
        },
    }
    report["validation_errors"] = validate(report)
    return report


def validate(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = report["summary"]
    if summary["failed_source_gate_ids"] != ["M5", "M6", "M7", "M8", "M9"]:
        errors.append("failed source gates must remain M5-M9")
    if summary["packet_count"] != 5:
        errors.append("expected five reopen packets")
    if summary["requirement_count"] != 5:
        errors.append("expected five requirements")
    if summary["passed_requirement_count"] != 5:
        errors.append("all queue-construction requirements should pass")
    if summary["failed_requirement_count"] != 0:
        errors.append("queue-construction requirements should not fail")
    if summary["selected_ci_larger_basis_denominator_beaten_count"] != 0:
        errors.append("B3 should still have zero denominator wins")
    if summary["full_compiled_state_covariance_computed"] is not False:
        errors.append("full covariance should still be missing")
    if summary["converged_vqe_or_adapt_energy"] is not False:
        errors.append("state prep should still be unconverged")
    if summary["b10_sampling_access_bridge_refuted_for_current_evidence"] is not True:
        errors.append("B10 should still refute the current B3 bridge")
    for key in [
        "b3_reopen_ready",
        "positive_same_access_route_available",
    ]:
        if summary[key] is not False:
            errors.append(f"{key} must remain false")
    for key in [
        "b3_reopen_ready",
        "positive_same_access_route_claimed",
        "reaction_dynamics_solution_claimed",
        "quantum_advantage_claimed",
        "bqp_separation_claimed",
    ]:
        if report["claim_boundary"].get(key) is not False:
            errors.append(f"{key} must remain false")
    return errors


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B3/B10 Reopen Blocker Queue Gate",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Source failed gates: {', '.join(summary['failed_source_gate_ids'])}",
        f"- Requirements passed / failed: {summary['passed_requirement_count']} / {summary['failed_requirement_count']}",
        f"- Reopen packet count: {summary['packet_count']}",
        f"- Row-aligned instances: {summary['row_aligned_instance_count']}",
        f"- Compiled pilot instances: {summary['compiled_pilot_instance_count']}",
        f"- Full compiled-state covariance computed: {summary['full_compiled_state_covariance_computed']}",
        f"- Ansatz parameter count / converged state prep: {summary['ansatz_parameter_count']} / {summary['converged_vqe_or_adapt_energy']}",
        f"- Selected-CI larger-basis denominator wins: {summary['selected_ci_larger_basis_denominator_beaten_count']}",
        f"- Max optimizer-loop total shots lower bound: {summary['max_optimizer_loop_total_shots_lower_bound']}",
        f"- B10 still refutes current B3 access bridge: {summary['b10_sampling_access_bridge_refuted_for_current_evidence']}",
        f"- B3 reopen ready: {summary['b3_reopen_ready']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Queue Requirements",
        "",
        "| Gate | Passed | Label | Acceptance rule |",
        "|---|---:|---|---|",
    ]
    for row in report["requirements"]:
        lines.append(
            f"| {row['gate_id']} | {row['passed']} | {row['label']} | {row['acceptance_rule']} |"
        )
    lines.extend(["", "## Reopen Packets", ""])
    for item in report["reopen_packets"]:
        lines.extend(
            [
                f"### {item['packet_id']}",
                "",
                f"- Blocks gate: {item['blocks_gate']}",
                f"- Owner role: {item['owner_role']}",
                f"- Downstream gate: {item['downstream_gate']}",
                f"- Acceptance rule: {item['acceptance_rule']}",
                "- Current evidence:",
            ]
        )
        for key, value in item["current_evidence"].items():
            lines.append(f"  - {key}: {value}")
        lines.append("- Required artifacts:")
        for artifact in item["required_artifacts"]:
            lines.append(f"  - {artifact}")
        lines.append("")
    lines.extend(["## Claim Boundary", ""])
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rescue-result",
        type=Path,
        default=Path("results/B3_B10_same_access_measurement_rescue_gate_v0.json"),
    )
    parser.add_argument(
        "--negative-note",
        type=Path,
        default=Path("results/B3_B10_same_access_negative_boundary_note_v0.json"),
    )
    parser.add_argument("--last-updated", default="2026-07-01")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B3_B10_reopen_blocker_queue_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B3_B10_reopen_blocker_queue_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = build_report(args)
    write_json(args.json_output, report, args.pretty)
    write_markdown(report, args.markdown_output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "method": report["method"],
                **report["summary"],
                "validation_errors": report["validation_errors"],
            },
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
