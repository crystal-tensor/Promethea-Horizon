#!/usr/bin/env python3
"""T-B5-006h/T-B10-014f: first W1 denominator-engine ledger."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any


METHOD = "b5_production_dmrg_mps_denominator_v0"
STATUS = "w1_denominator_engine_v0_failed_not_production_dmrg"
MODEL_STATUS = "w1_denominator_candidate_executed_but_acceptance_failed"
VERSION = "0.1"
FIXED_SECTOR_NORM_THRESHOLD = 0.01
ENERGY_VARIANCE_THRESHOLD = 1e-6


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        text = json.dumps(payload, indent=2, sort_keys=True)
    else:
        text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def row_key(row: dict[str, Any]) -> str:
    return f"{int(row['sites'])}|{float(row['u_over_t']):.6g}"


def selected_bond_row(row: dict[str, Any]) -> dict[str, Any]:
    selected_bond = int(row["selected_bond_dimension"])
    for candidate in row.get("bond_dimension_rows", []):
        if int(candidate["bond_dimension"]) == selected_bond:
            return candidate
    raise ValueError(f"missing selected bond row for {row_key(row)}")


def monotonicity_violations(restart: dict[str, Any]) -> int:
    energies = [float(restart["initial_energy"])]
    energies.extend(float(sweep["energy"]) for sweep in restart.get("sweep_history", []))
    return sum(1 for before, after in zip(energies, energies[1:]) if after > before + 1e-8)


def row_diagnostic(
    als_row: dict[str, Any],
    two_site_row: dict[str, Any],
    seeded_row: dict[str, Any],
    row_contract_hash: str,
) -> dict[str, Any]:
    bond_row = selected_bond_row(als_row)
    restart_summaries = bond_row.get("restart_summaries", [])
    sweep_rows = [
        sweep
        for restart in restart_summaries
        for sweep in restart.get("sweep_history", [])
    ]
    selected_error = float(als_row["selected_relative_response_error"])
    seeded_error = float(seeded_row["selected_relative_response_error"])
    two_site_error = float(two_site_row["selected_relative_response_error"])
    fixed_sector_norm = float(als_row["selected_fixed_sector_norm_before_normalization"])
    energy_variance = float(als_row["selected_energy_variance"])
    monotonicity_count = sum(monotonicity_violations(restart) for restart in restart_summaries)
    fixed_sector_passed = fixed_sector_norm >= FIXED_SECTOR_NORM_THRESHOLD
    variance_passed = energy_variance <= ENERGY_VARIANCE_THRESHOLD
    monotonicity_passed = monotonicity_count == 0
    discarded_weight_ledger_present = False
    convergence_ledger_passed = bool(
        fixed_sector_passed
        and variance_passed
        and monotonicity_passed
        and discarded_weight_ledger_present
    )
    return {
        "row_id": row_key(als_row),
        "row_contract_hash": row_contract_hash,
        "sites": int(als_row["sites"]),
        "u_over_t": float(als_row["u_over_t"]),
        "selected_candidate_family": "variational_mps_als",
        "selection_policy": "predeclared_lowest_global_mean_response_error_non_exact_seeded_family_from_existing_w1_inputs",
        "selected_bond_dimension": int(als_row["selected_bond_dimension"]),
        "restarts_per_bond_dimension": int(len(restart_summaries)),
        "sweeps_per_restart": int(max((len(restart.get("sweep_history", [])) for restart in restart_summaries), default=0)),
        "sweep_ledger_rows": int(len(sweep_rows)),
        "exact_state_seeded": False,
        "production_dmrg_available": False,
        "canonical_environment_production_dmrg": False,
        "stored_left_right_environments": False,
        "orthonormal_residual_ledger_present": False,
        "discarded_weight_ledger_present": discarded_weight_ledger_present,
        "selected_relative_response_error": selected_error,
        "seeded_mps_pressure_relative_response_error": seeded_error,
        "two_site_relative_response_error": two_site_error,
        "relative_error_vs_seeded_pressure": selected_error / max(seeded_error, 1e-12),
        "beats_seeded_mps_pressure": selected_error < seeded_error,
        "beats_two_site_candidate": selected_error < two_site_error,
        "selected_energy_error_per_site": float(als_row["selected_energy_error_per_site"]),
        "selected_energy_variance": energy_variance,
        "selected_fixed_sector_norm_before_normalization": fixed_sector_norm,
        "selected_overlap_with_exact_ground_state": float(als_row["selected_overlap_with_exact_ground_state"]),
        "fixed_sector_norm_passed": fixed_sector_passed,
        "energy_variance_passed": variance_passed,
        "energy_monotonicity_violations": monotonicity_count,
        "energy_monotonicity_passed": monotonicity_passed,
        "convergence_ledger_passed": convergence_ledger_passed,
    }


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    row_contract = load_json(args.row_contract)
    als = load_json(args.variational_mps)
    two_site = load_json(args.two_site)
    seeded = load_json(args.seeded_mps)
    acceptance = load_json(args.acceptance_gate)

    row_contract_summary = row_contract["summary"]
    row_contract_hash = row_contract_summary["row_contract_hash"]
    als_rows = {row_key(row): row for row in als["rows"]}
    two_site_rows = {row_key(row): row for row in two_site["rows"]}
    seeded_rows = {row_key(row): row for row in seeded["rows"]}
    contract_ids = [row["row_id"] for row in row_contract.get("row_contract", [])]
    if not contract_ids:
        contract_ids = sorted(als_rows)

    rows = [
        row_diagnostic(als_rows[row_id], two_site_rows[row_id], seeded_rows[row_id], row_contract_hash)
        for row_id in contract_ids
    ]

    rows_beating_seeded = sum(1 for row in rows if row["beats_seeded_mps_pressure"])
    convergence_passed_rows = sum(1 for row in rows if row["convergence_ledger_passed"])
    fixed_sector_passed_rows = sum(1 for row in rows if row["fixed_sector_norm_passed"])
    variance_passed_rows = sum(1 for row in rows if row["energy_variance_passed"])
    monotonicity_passed_rows = sum(1 for row in rows if row["energy_monotonicity_passed"])
    selected_errors = [float(row["selected_relative_response_error"]) for row in rows]
    seeded_errors = [float(row["seeded_mps_pressure_relative_response_error"]) for row in rows]

    requirements = [
        requirement(
            "E1",
            "Locked B5/B10 row contract is preserved",
            len(rows) == 9 and row_contract_summary.get("source_checks_failed") == 0,
            {
                "row_count": len(rows),
                "row_contract_hash": row_contract_hash,
                "source_checks_failed": row_contract_summary.get("source_checks_failed"),
            },
        ),
        requirement(
            "E2",
            "A non-exact-state-seeded denominator candidate is executed",
            all(row["exact_state_seeded"] is False for row in rows),
            {"candidate_family": "variational_mps_als", "exact_state_seeded_rows": 0},
        ),
        requirement(
            "E3",
            "All rows have sweep ledgers",
            all(row["sweep_ledger_rows"] > 0 for row in rows),
            {"min_sweep_ledger_rows": min(row["sweep_ledger_rows"] for row in rows)},
        ),
        requirement(
            "E4",
            "Production canonical environments and residuals are present",
            False,
            {
                "stored_left_right_environments": False,
                "orthonormal_residual_ledger_present": False,
                "canonical_environment_production_dmrg": False,
            },
        ),
        requirement(
            "E5",
            "All nine rows pass convergence diagnostics",
            convergence_passed_rows == 9,
            {
                "convergence_passed_rows": convergence_passed_rows,
                "fixed_sector_norm_passed_rows": fixed_sector_passed_rows,
                "energy_variance_passed_rows": variance_passed_rows,
                "energy_monotonicity_passed_rows": monotonicity_passed_rows,
                "discarded_weight_ledger_present": False,
            },
        ),
        requirement(
            "E6",
            "Candidate beats exact-state-seeded pressure on every row",
            rows_beating_seeded == 9,
            {
                "rows_beating_seeded_pressure": rows_beating_seeded,
                "mean_candidate_error": statistics.mean(selected_errors),
                "mean_seeded_pressure_error": statistics.mean(seeded_errors),
            },
        ),
        requirement(
            "E7",
            "Same-access production cost ledger is complete",
            False,
            {
                "wall_clock_costs_present": False,
                "memory_costs_present": False,
                "matvec_or_sweep_costs_complete": False,
                "optimizer_loop_costs_complete": False,
            },
        ),
        requirement(
            "E8",
            "Forbidden claims remain false",
            True,
            {
                "production_dmrg_claimed": False,
                "same_access_positive_route_claimed": False,
                "quantum_advantage_claimed": False,
                "bqp_separation_claimed": False,
            },
        ),
    ]
    passed = sum(1 for item in requirements if item["passed"])
    failed = len(requirements) - passed
    failed_ids = [item["requirement_id"] for item in requirements if not item["passed"]]

    validation_errors: list[str] = []
    if len(rows) != 9:
        validation_errors.append("expected nine locked B5/B10 rows")
    if failed_ids != ["E4", "E5", "E6", "E7"]:
        validation_errors.append(f"unexpected failed denominator-engine requirements: {failed_ids}")
    if rows_beating_seeded != 0:
        validation_errors.append("v0 candidate unexpectedly beats seeded pressure")
    if convergence_passed_rows != 0:
        validation_errors.append("v0 candidate unexpectedly passes convergence on at least one row")
    if acceptance["summary"].get("failed_production_dmrg_requirement_ids") != [
        "D3",
        "D4",
        "D5",
        "D6",
        "D7",
        "D8",
        "D9",
    ]:
        validation_errors.append("source W1 acceptance failed IDs changed unexpectedly")

    summary = {
        "row_contract_count": len(rows),
        "row_contract_hash": row_contract_hash,
        "candidate_family_count": 2,
        "selected_candidate_family": "variational_mps_als",
        "selection_policy": "predeclared_lowest_global_mean_response_error_non_exact_seeded_family_from_existing_w1_inputs",
        "denominator_requirement_count": len(requirements),
        "denominator_requirements_passed": passed,
        "denominator_requirements_failed": failed,
        "failed_denominator_requirement_ids": failed_ids,
        "w1_denominator_engine_executed": True,
        "w1_denominator_engine_accepted": False,
        "w1_denominator_engine_failed_not_production_dmrg": True,
        "production_dmrg_available": False,
        "canonical_environment_production_dmrg": False,
        "stored_left_right_environments": False,
        "orthonormal_residual_ledger_present": False,
        "discarded_weight_ledger_present": False,
        "sweep_ledger_rows": sum(row["sweep_ledger_rows"] for row in rows),
        "fixed_sector_norm_passed_rows": fixed_sector_passed_rows,
        "energy_variance_passed_rows": variance_passed_rows,
        "energy_monotonicity_passed_rows": monotonicity_passed_rows,
        "convergence_passed_rows": convergence_passed_rows,
        "rows_beating_seeded_mps_pressure": rows_beating_seeded,
        "mean_candidate_relative_response_error": statistics.mean(selected_errors),
        "median_candidate_relative_response_error": statistics.median(selected_errors),
        "max_candidate_relative_response_error": max(selected_errors),
        "mean_seeded_pressure_relative_response_error": statistics.mean(seeded_errors),
        "candidate_error_over_seeded_error_mean_ratio": statistics.mean(
            row["relative_error_vs_seeded_pressure"] for row in rows
        ),
        "remaining_positive_route_packets": ["W1"],
        "catalog_change_required": False,
        "same_access_positive_route_ready": False,
        "b10_t1_positive_route_ready": False,
        "production_dmrg_claimed": False,
        "quantum_response_win_claimed": False,
        "accuracy_per_resource_win_claimed": False,
        "same_access_positive_route_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "dequantization_theorem_claimed": False,
        "sampling_access_theorem_claimed": False,
        "condition_count": len(requirements),
        "conditions_satisfied": passed,
        "conditions_failed": failed,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B5",
        "linked_benchmark_id": "B10",
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B5", "B10"],
        "title": "B5 W1 Production DMRG/MPS Denominator Engine v0",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_row_contract_result": str(args.row_contract),
        "source_variational_mps_result": str(args.variational_mps),
        "source_two_site_result": str(args.two_site),
        "source_seeded_mps_result": str(args.seeded_mps),
        "source_acceptance_gate_result": str(args.acceptance_gate),
        "summary": summary,
        "requirements": requirements,
        "rows": rows,
        "claim_boundary": {
            "w1_denominator_engine_executed": True,
            "w1_denominator_engine_accepted": False,
            "production_dmrg_available": False,
            "production_dmrg_claimed": False,
            "quantum_response_win_claimed": False,
            "accuracy_per_resource_win_claimed": False,
            "same_access_positive_route_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "dequantization_theorem_claimed": False,
            "sampling_access_theorem_claimed": False,
            "what_is_supported": (
                "A first W1 denominator-engine ledger now selects and audits the strongest current "
                "non-exact-state-seeded tensor candidate under the locked nine-row B5/B10 contract."
            ),
            "what_is_not_supported": (
                "This is not accepted production DMRG, not a canonical-environment implementation, "
                "not a seeded-pressure replacement, not a same-access positive route, not quantum "
                "advantage, and not a BQP separation."
            ),
            "next_gate": (
                "Replace the v0 candidate with an actual canonical-environment DMRG/MPS solver that "
                "stores environments, passes 9/9 convergence diagnostics, and beats the seeded-pressure ladder."
            ),
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B5 W1 Production DMRG/MPS Denominator Engine v0.1",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Row contract count/hash: {summary['row_contract_count']} / `{summary['row_contract_hash']}`",
        f"- Requirements passed/failed: {summary['denominator_requirements_passed']} / {summary['denominator_requirements_failed']}",
        f"- Failed requirement IDs: {summary['failed_denominator_requirement_ids']}",
        f"- Selected candidate family: {summary['selected_candidate_family']}",
        f"- Convergence-passed rows: {summary['convergence_passed_rows']}",
        f"- Rows beating seeded pressure: {summary['rows_beating_seeded_mps_pressure']}",
        f"- Mean candidate / seeded error: {summary['mean_candidate_relative_response_error']:.6g} / {summary['mean_seeded_pressure_relative_response_error']:.6g}",
        f"- Production DMRG available: {summary['production_dmrg_available']}",
        "",
        "## Requirement Ledger",
        "",
        "| ID | Requirement | Passed | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["requirements"]:
        evidence = "; ".join(f"{key}={value}" for key, value in item["evidence"].items())
        lines.append(f"| {item['requirement_id']} | {item['label']} | {item['passed']} | {evidence} |")
    lines.extend(
        [
            "",
            "## Row Ledger",
            "",
            "| row | candidate | rel error | seeded rel error | norm pass | variance pass | monotonic pass | convergence pass | beats seeded |",
            "| --- | --- | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['row_id']} | {row['selected_candidate_family']} | "
            f"{row['selected_relative_response_error']:.6g} | "
            f"{row['seeded_mps_pressure_relative_response_error']:.6g} | "
            f"{row['fixed_sector_norm_passed']} | {row['energy_variance_passed']} | "
            f"{row['energy_monotonicity_passed']} | {row['convergence_ledger_passed']} | "
            f"{row['beats_seeded_mps_pressure']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- what_is_supported: {payload['claim_boundary']['what_is_supported']}",
            f"- what_is_not_supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- next_gate: {payload['claim_boundary']['next_gate']}",
            f"- production_dmrg_claimed: {payload['claim_boundary']['production_dmrg_claimed']}",
            f"- quantum_advantage_claimed: {payload['claim_boundary']['quantum_advantage_claimed']}",
            f"- bqp_separation_claimed: {payload['claim_boundary']['bqp_separation_claimed']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {len(payload['validation_errors'])}",
        ]
    )
    if payload["validation_errors"]:
        lines.extend(f"- {error}" for error in payload["validation_errors"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the first B5/B10 W1 denominator-engine ledger.")
    parser.add_argument("--row-contract", type=Path, default=Path("results/B5_B10_row_contract_harness_v0.json"))
    parser.add_argument("--variational-mps", type=Path, default=Path("results/B5_variational_mps_als_response_reference_v0.json"))
    parser.add_argument("--two-site", type=Path, default=Path("results/B5_two_site_dmrg_response_reference_v0.json"))
    parser.add_argument("--seeded-mps", type=Path, default=Path("results/B5_mps_truncation_response_reference_v0.json"))
    parser.add_argument("--acceptance-gate", type=Path, default=Path("results/B5_B10_production_dmrg_mps_acceptance_gate_v0.json"))
    parser.add_argument("--json-output", type=Path, default=Path("results/B5_production_dmrg_mps_denominator_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B5_production_dmrg_mps_denominator.md"))
    parser.add_argument("--last-updated", default=time.strftime("%Y-%m-%d"))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)
    if args.pretty:
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if not payload["validation_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
