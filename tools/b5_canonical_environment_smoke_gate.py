#!/usr/bin/env python3
"""Audit B5 two-site tensor evidence for canonical-environment smoke readiness."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any


METHOD = "b5_canonical_environment_smoke_gate_v0"
STATUS = "canonical_environment_smoke_gate_failed_not_production_dmrg"
MODEL_STATUS = "posthoc_two_site_environment_diagnostics_not_canonical_solver"
VERSION = "0.1"

FIXED_SECTOR_NORM_THRESHOLD = 0.01
ENERGY_VARIANCE_THRESHOLD = 1e-6
MAX_RELATIVE_DISCARDED_WEIGHT_THRESHOLD = 0.05
SEEDED_RESPONSE_ERROR_MARGIN = 1.0


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def selected_bond_row(row: dict[str, Any]) -> dict[str, Any]:
    selected_bond = int(row["selected_bond_dimension"])
    for bond_row in row.get("bond_dimension_rows", []):
        if int(bond_row["bond_dimension"]) == selected_bond:
            return bond_row
    raise ValueError(f"missing selected bond row for sites={row.get('sites')} u/t={row.get('u_over_t')}")


def flatten_sweeps(bond_row: dict[str, Any]) -> list[dict[str, Any]]:
    sweeps: list[dict[str, Any]] = []
    for restart in bond_row.get("restart_summaries", []):
        for sweep in restart.get("sweep_history", []):
            sweeps.append({**sweep, "restart": restart.get("restart")})
    return sweeps


def energy_monotonicity_violations(restart: dict[str, Any]) -> int:
    energies = [float(restart["initial_energy"])]
    energies.extend(float(sweep["energy"]) for sweep in restart.get("sweep_history", []))
    return sum(1 for before, after in zip(energies, energies[1:]) if after > before + 1e-8)


def row_diagnostic(row: dict[str, Any]) -> dict[str, Any]:
    bond_row = selected_bond_row(row)
    sweeps = flatten_sweeps(bond_row)
    restart_summaries = bond_row.get("restart_summaries", [])
    max_discarded = max((float(sweep.get("max_relative_discarded_weight", 0.0)) for sweep in sweeps), default=0.0)
    min_local_rank = min((int(sweep.get("min_local_rank", 0)) for sweep in sweeps), default=0)
    max_local_parameter_count = max((int(sweep.get("max_local_parameter_count", 0)) for sweep in sweeps), default=0)
    monotonicity_violations = sum(energy_monotonicity_violations(restart) for restart in restart_summaries)
    final_energy_variances = [float(restart["final_energy_variance"]) for restart in restart_summaries]
    final_norms = [
        float(restart["final_fixed_sector_norm_before_normalization"])
        for restart in restart_summaries
    ]
    selected_energy_variance = float(row["selected_energy_variance"])
    selected_norm = float(row["selected_fixed_sector_norm_before_normalization"])
    selected_response_error = float(row["selected_relative_response_error"])
    seeded_response_error = float(row["seeded_mps_pressure_relative_response_error"])
    fixed_sector_norm_passed = selected_norm >= FIXED_SECTOR_NORM_THRESHOLD
    variance_passed = selected_energy_variance <= ENERGY_VARIANCE_THRESHOLD
    discarded_weight_passed = max_discarded <= MAX_RELATIVE_DISCARDED_WEIGHT_THRESHOLD
    monotonicity_passed = monotonicity_violations == 0
    response_close_to_seeded = selected_response_error <= seeded_response_error * (
        1.0 + SEEDED_RESPONSE_ERROR_MARGIN
    )
    return {
        "sites": int(row["sites"]),
        "u_over_t": float(row["u_over_t"]),
        "selected_bond_dimension": int(row["selected_bond_dimension"]),
        "sweep_count": len(sweeps),
        "restart_count": len(restart_summaries),
        "environment_ledger_present": bool(sweeps),
        "min_local_rank": min_local_rank,
        "max_local_parameter_count": max_local_parameter_count,
        "max_relative_discarded_weight": max_discarded,
        "selected_energy_variance": selected_energy_variance,
        "median_restart_final_energy_variance": statistics.median(final_energy_variances)
        if final_energy_variances
        else None,
        "selected_fixed_sector_norm_before_normalization": selected_norm,
        "median_restart_final_fixed_sector_norm_before_normalization": statistics.median(final_norms)
        if final_norms
        else None,
        "selected_relative_response_error": selected_response_error,
        "seeded_mps_pressure_relative_response_error": seeded_response_error,
        "variational_mps_als_relative_response_error": row.get(
            "variational_mps_als_relative_response_error"
        ),
        "energy_monotonicity_violations": monotonicity_violations,
        "fixed_sector_norm_smoke_passed": fixed_sector_norm_passed,
        "energy_variance_smoke_passed": variance_passed,
        "discarded_weight_smoke_passed": discarded_weight_passed,
        "energy_monotonicity_smoke_passed": monotonicity_passed,
        "response_close_to_seeded_pressure": response_close_to_seeded,
        "row_smoke_passed": bool(
            fixed_sector_norm_passed
            and variance_passed
            and discarded_weight_passed
            and monotonicity_passed
            and response_close_to_seeded
        ),
        "beats_seeded_mps_pressure_reference": bool(
            row["two_site_dmrg_beats_seeded_mps_pressure_reference"]
        ),
        "beats_variational_mps_als_reference": bool(
            row["two_site_dmrg_beats_variational_mps_als_reference"]
        ),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    smoke_passed_rows = [row for row in rows if row["row_smoke_passed"]]
    return {
        "instance_count": len(rows),
        "environment_ledger_rows": sum(1 for row in rows if row["environment_ledger_present"]),
        "smoke_passed_row_count": len(smoke_passed_rows),
        "fixed_sector_norm_passed_rows": sum(
            1 for row in rows if row["fixed_sector_norm_smoke_passed"]
        ),
        "energy_variance_passed_rows": sum(
            1 for row in rows if row["energy_variance_smoke_passed"]
        ),
        "discarded_weight_passed_rows": sum(
            1 for row in rows if row["discarded_weight_smoke_passed"]
        ),
        "energy_monotonicity_passed_rows": sum(
            1 for row in rows if row["energy_monotonicity_smoke_passed"]
        ),
        "response_close_to_seeded_rows": sum(
            1 for row in rows if row["response_close_to_seeded_pressure"]
        ),
        "rows_beating_seeded_mps_pressure_reference": sum(
            1 for row in rows if row["beats_seeded_mps_pressure_reference"]
        ),
        "rows_beating_variational_mps_als_reference": sum(
            1 for row in rows if row["beats_variational_mps_als_reference"]
        ),
        "max_relative_discarded_weight": max(
            float(row["max_relative_discarded_weight"]) for row in rows
        ),
        "min_fixed_sector_norm_before_normalization": min(
            float(row["selected_fixed_sector_norm_before_normalization"]) for row in rows
        ),
        "max_energy_variance": max(float(row["selected_energy_variance"]) for row in rows),
        "max_relative_response_error": max(
            float(row["selected_relative_response_error"]) for row in rows
        ),
        "mean_relative_response_error": statistics.mean(
            float(row["selected_relative_response_error"]) for row in rows
        ),
        "canonical_environment_solver_claimed": False,
        "production_dmrg_claimed": False,
        "mature_canonical_dmrg_ready": False,
        "quantum_response_win_claimed": False,
        "accuracy_per_resource_win_claimed": False,
        "same_access_positive_route_claimed": False,
    }


def validate(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = report["summary"]
    claims = report["claim_boundary"]
    if summary["instance_count"] != 9:
        errors.append("expected 9 B5/B10 D5 rows")
    if summary["environment_ledger_rows"] != 9:
        errors.append("all rows should expose two-site environment ledgers")
    if summary["rows_beating_seeded_mps_pressure_reference"] != 0:
        errors.append("smoke gate must not beat the seeded MPS pressure reference")
    if summary["mature_canonical_dmrg_ready"] is not False:
        errors.append("mature canonical DMRG must remain false")
    for key in [
        "canonical_environment_solver_claimed",
        "production_dmrg_claimed",
        "quantum_response_win_claimed",
        "accuracy_per_resource_win_claimed",
        "same_access_positive_route_claimed",
    ]:
        if claims.get(key) is not False:
            errors.append(f"{key} must remain False")
    return errors


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    source = load_json(args.two_site_result)
    rows = [row_diagnostic(row) for row in source["rows"]]
    summary = summarize(rows)
    report = {
        "benchmark_id": "B5",
        "problem_id": 38,
        "title": "B5 canonical-environment smoke gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "source_result": str(args.two_site_result),
        "thresholds": {
            "fixed_sector_norm_threshold": FIXED_SECTOR_NORM_THRESHOLD,
            "energy_variance_threshold": ENERGY_VARIANCE_THRESHOLD,
            "max_relative_discarded_weight_threshold": MAX_RELATIVE_DISCARDED_WEIGHT_THRESHOLD,
            "seeded_response_error_margin": SEEDED_RESPONSE_ERROR_MARGIN,
        },
        "summary": summary,
        "rows": rows,
        "claim_boundary": {
            "canonical_environment_smoke_diagnostics_built": True,
            "environment_ledger_from_two_site_prototype_used": True,
            "canonical_environment_solver_claimed": False,
            "production_dmrg_claimed": False,
            "quantum_response_win_claimed": False,
            "accuracy_per_resource_win_claimed": False,
            "same_access_positive_route_claimed": False,
            "what_is_supported": (
                "The existing two-site prototype now has a row-level smoke audit "
                "for environment ledger coverage, discarded-weight pressure, "
                "fixed-sector norms, energy variance, and response closeness."
            ),
            "what_is_not_supported": (
                "This is a post-hoc diagnostic over a prototype, not a mature "
                "canonical-environment DMRG solver and not a B10 positive route."
            ),
        },
        "runtime_seconds": time.time() - started,
    }
    report["validation_errors"] = validate(report)
    report["summary"]["validation_error_count"] = len(report["validation_errors"])
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B5 Canonical-Environment Smoke Gate v0.1",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Source result: {report['source_result']}",
        f"- Instances: {summary['instance_count']}",
        f"- Environment ledger rows: {summary['environment_ledger_rows']}",
        f"- Smoke-passed rows: {summary['smoke_passed_row_count']}",
        f"- Fixed-sector norm passed rows: {summary['fixed_sector_norm_passed_rows']}",
        f"- Energy-variance passed rows: {summary['energy_variance_passed_rows']}",
        f"- Discarded-weight passed rows: {summary['discarded_weight_passed_rows']}",
        f"- Energy-monotonicity passed rows: {summary['energy_monotonicity_passed_rows']}",
        f"- Response-close-to-seeded rows: {summary['response_close_to_seeded_rows']}",
        f"- Rows beating seeded MPS pressure: {summary['rows_beating_seeded_mps_pressure_reference']}",
        f"- Rows beating variational MPS/ALS: {summary['rows_beating_variational_mps_als_reference']}",
        f"- Mean/max relative response error: {summary['mean_relative_response_error']:.6g} / {summary['max_relative_response_error']:.6g}",
        f"- Min fixed-sector norm: {summary['min_fixed_sector_norm_before_normalization']:.6g}",
        f"- Max relative discarded weight: {summary['max_relative_discarded_weight']:.6g}",
        f"- Mature canonical DMRG ready: {summary['mature_canonical_dmrg_ready']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Row Diagnostics",
        "",
        "| sites | U/t | sweeps | norm | variance | max discarded | rel error | smoke pass | beats seeded | beats ALS |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['sites']} | {row['u_over_t']} | {row['sweep_count']} | "
            f"{row['selected_fixed_sector_norm_before_normalization']:.6g} | "
            f"{row['selected_energy_variance']:.6g} | "
            f"{row['max_relative_discarded_weight']:.6g} | "
            f"{row['selected_relative_response_error']:.6g} | "
            f"{row['row_smoke_passed']} | "
            f"{row['beats_seeded_mps_pressure_reference']} | "
            f"{row['beats_variational_mps_als_reference']} |"
        )
    lines.extend(["", "## Claim Boundary", ""])
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "T-B5-006 must still implement an actual canonical-center finite-system",
            "DMRG/MPS solver with stored left/right environments, orthonormal",
            "residuals, convergence controls, no exact-state seeding, and full",
            "sweep/matvec/memory cost accounting.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--two-site-result",
        type=Path,
        default=Path("results/B5_two_site_dmrg_response_reference_v0.json"),
    )
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B5_canonical_environment_smoke_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B5_canonical_environment_smoke_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = build_report(args)
    write_json(args.json_output, report)
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
