#!/usr/bin/env python3
"""Repaired-packet resource boundary for B1/B7 cone_01.

T-B1-004al closed the reduced-CNOT packet set at 3/3 bounded exact repairs.
This gate asks the next accounting question: after using the cheapest known
exact repair for each packet, does the repaired set become acceptable as a B7
ledger saving?

The answer is still no. The repaired packet set preserves the 9-CNOT candidate
reduction and greatly lowers off-grid local-U3 pressure compared with the
original arbitrary-U3 packet candidates, but the line-1381 repair still carries
five off-grid local-U3 parameters and no symbolic full-circuit replay
certificate exists.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
PACKET_RESOURCE_PATH = ROOT / "results" / "B1_B7_cone01_packet_replay_resource_gate_v0.json"
SPARSE_REPAIR_PATH = ROOT / "results" / "B1_B7_cone01_sparse_local_u3_repair_gate_v0.json"
THREE_PARAMETER_PATH = ROOT / "results" / "B1_B7_cone01_three_parameter_local_u3_repair_gate_v0.json"
FIVE_PARAMETER_PATH = ROOT / "results" / "B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_repaired_packet_resource_boundary_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_repaired_packet_resource_boundary_gate.md"

METHOD = "b1_b7_cone01_repaired_packet_resource_boundary_gate_v0"
STATUS = "cone01_repaired_packet_resource_boundary_not_ledger_accepted"
MODEL_STATUS = "three_of_three_packets_repaired_but_off_grid_resource_boundary_remains"


def repaired_rows() -> list[dict[str, Any]]:
    baseline = load_json(PACKET_RESOURCE_PATH)
    sparse = load_json(SPARSE_REPAIR_PATH)
    three = load_json(THREE_PARAMETER_PATH)
    five = load_json(FIVE_PARAMETER_PATH)

    source_by_line = {
        int(row["candidate_line_number"]): row
        for row in baseline.get("packet_replay_resource_rows", [])
    }
    sparse_by_line = {
        int(row["candidate_line_number"]): row
        for row in sparse.get("sparse_local_u3_repair_rows", [])
    }
    three_by_line = {
        int(row["candidate_line_number"]): row
        for row in three.get("three_parameter_local_u3_repair_rows", [])
    }
    five_by_line = {
        int(row["candidate_line_number"]): row
        for row in five.get("five_parameter_line1381_exact_repair_rows", [])
    }

    repair_specs = [
        {
            "line": 1378,
            "repair_gate_id": "T-B1-004ai",
            "repair_method": sparse.get("method"),
            "exact_pass": sparse_by_line[1378]["sparse_repair_exact_pass"],
            "free_parameter_count": sparse_by_line[1378]["minimum_exact_free_parameter_count"],
            "exact_residual_norm": sparse_by_line[1378]["exact_repair_residual_norm"],
            "exact_free_indices": sparse_by_line[1378]["best_one_parameter_free_indices"],
            "exact_off_grid_parameter_count": sparse_by_line[1378][
                "exact_repair_off_pi_over_four_parameter_count"
            ],
        },
        {
            "line": 268,
            "repair_gate_id": "T-B1-004aj",
            "repair_method": three.get("method"),
            "exact_pass": three_by_line[268]["three_parameter_exact_pass"],
            "free_parameter_count": 3,
            "exact_residual_norm": three_by_line[268]["exact_three_parameter_residual_norm"],
            "exact_free_indices": three_by_line[268]["exact_three_parameter_free_indices"],
            "exact_off_grid_parameter_count": three_by_line[268][
                "exact_three_parameter_off_pi_over_four_parameter_count"
            ],
        },
        {
            "line": 1381,
            "repair_gate_id": "T-B1-004al",
            "repair_method": five.get("method"),
            "exact_pass": five_by_line[1381]["five_parameter_exact_pass"],
            "free_parameter_count": 5,
            "exact_residual_norm": five_by_line[1381][
                "first_exact_five_parameter_residual_norm"
            ],
            "exact_free_indices": five_by_line[1381][
                "first_exact_five_parameter_free_indices"
            ],
            "exact_off_grid_parameter_count": five_by_line[1381][
                "first_exact_five_parameter_off_pi_over_four_parameter_count"
            ],
        },
    ]

    rows: list[dict[str, Any]] = []
    for spec in repair_specs:
        source = source_by_line[spec["line"]]
        source_off_grid = int(source["source_off_pi_over_four_parameter_count"])
        repaired_off_grid = int(spec["exact_off_grid_parameter_count"])
        rows.append(
            {
                "candidate_line_number": spec["line"],
                "repair_gate_id": spec["repair_gate_id"],
                "repair_method": spec["repair_method"],
                "source_cnot_count": int(source["source_cnot_count"]),
                "replacement_cnot_count": int(source["replacement_cnot_count"]),
                "candidate_cnot_reduction": int(source["candidate_cnot_reduction"]),
                "source_off_pi_over_four_parameter_count": source_off_grid,
                "original_replacement_off_pi_over_four_parameter_count": int(
                    source["replacement_off_pi_over_four_parameter_count"]
                ),
                "repaired_off_pi_over_four_parameter_count": repaired_off_grid,
                "repaired_off_grid_parameter_delta_vs_source": repaired_off_grid
                - source_off_grid,
                "repaired_incremental_proxy_t_pressure": (
                    repaired_off_grid - source_off_grid
                )
                * PROXY_T_PER_OCCURRENCE,
                "exact_repair_free_parameter_count": int(spec["free_parameter_count"]),
                "exact_repair_free_indices": spec["exact_free_indices"],
                "exact_repair_residual_norm": float(spec["exact_residual_norm"]),
                "bounded_packet_exact_repair": bool(spec["exact_pass"]),
                "accepted_full_circuit_replay_certificate": False,
                "accepted_occurrence_removal": 0,
                "accepted_proxy_t_reduction": 0,
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    baseline = load_json(PACKET_RESOURCE_PATH)
    sparse = load_json(SPARSE_REPAIR_PATH)
    three = load_json(THREE_PARAMETER_PATH)
    five = load_json(FIVE_PARAMETER_PATH)
    rows = repaired_rows()
    accepted_removed = sum(row["accepted_occurrence_removal"] for row in rows)
    source_off_grid = sum(row["source_off_pi_over_four_parameter_count"] for row in rows)
    original_replacement_off_grid = sum(
        row["original_replacement_off_pi_over_four_parameter_count"] for row in rows
    )
    repaired_off_grid = sum(row["repaired_off_pi_over_four_parameter_count"] for row in rows)
    summary = {
        "source_packet_resource_method": baseline.get("method"),
        "source_sparse_repair_method": sparse.get("method"),
        "source_three_parameter_method": three.get("method"),
        "source_five_parameter_method": five.get("method"),
        "packet_count": len(rows),
        "bounded_packet_exact_repair_count": sum(
            1 for row in rows if row["bounded_packet_exact_repair"]
        ),
        "candidate_cnot_reduction_if_all_packets_accepted": sum(
            row["candidate_cnot_reduction"] for row in rows
        ),
        "source_off_pi_over_four_parameter_count": source_off_grid,
        "original_replacement_off_pi_over_four_parameter_count": original_replacement_off_grid,
        "repaired_off_pi_over_four_parameter_count": repaired_off_grid,
        "original_incremental_off_pi_over_four_parameter_count": original_replacement_off_grid
        - source_off_grid,
        "repaired_incremental_off_pi_over_four_parameter_count": repaired_off_grid
        - source_off_grid,
        "original_incremental_proxy_t_pressure": (
            original_replacement_off_grid - source_off_grid
        )
        * PROXY_T_PER_OCCURRENCE,
        "repaired_incremental_proxy_t_pressure": (repaired_off_grid - source_off_grid)
        * PROXY_T_PER_OCCURRENCE,
        "off_grid_parameter_reduction_vs_original_candidate": original_replacement_off_grid
        - repaired_off_grid,
        "proxy_t_pressure_reduction_vs_original_candidate": (
            original_replacement_off_grid - repaired_off_grid
        )
        * PROXY_T_PER_OCCURRENCE,
        "packets_with_remaining_off_grid_repair_count": sum(
            1 for row in rows if row["repaired_off_pi_over_four_parameter_count"] > 0
        ),
        "accepted_full_circuit_replay_certificate_count": sum(
            1 for row in rows if row["accepted_full_circuit_replay_certificate"]
        ),
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": sum(row["accepted_proxy_t_reduction"] for row in rows),
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "bounded_packet_repair_claimed_as_full_circuit_rewrite": False,
        "symbolic_exact_decomposition_claimed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": baseline.get("workload", "qasmbench_medium_exact/gcm_h6.qasm"),
        "source_packet_resource_result": display_path(PACKET_RESOURCE_PATH),
        "source_sparse_local_u3_repair_result": display_path(SPARSE_REPAIR_PATH),
        "source_three_parameter_local_u3_repair_result": display_path(THREE_PARAMETER_PATH),
        "source_five_parameter_line1381_exact_repair_result": display_path(FIVE_PARAMETER_PATH),
        "summary": summary,
        "repaired_packet_resource_boundary_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "The known exact packet repairs reduce the off-grid local-U3 burden from "
                "40 replacement parameters to 5, while preserving a 9-CNOT candidate reduction."
            ),
            "unsupported_claims": [
                "The repaired packet set is not accepted as a full-circuit rewrite.",
                "The remaining five off-grid local-U3 parameters are not priced as a B7 saving.",
                "No occurrence removal or proxy-T reduction is accepted.",
            ],
            "bounded_packet_repair_claimed_as_full_circuit_rewrite": False,
            "symbolic_exact_decomposition_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["summary"]["validation_error_count"] = len(validate_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload.get("summary", {})
    rows = payload.get("repaired_packet_resource_boundary_rows", [])
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    expected = {
        "packet_count": 3,
        "bounded_packet_exact_repair_count": 3,
        "candidate_cnot_reduction_if_all_packets_accepted": 9,
        "source_off_pi_over_four_parameter_count": 1,
        "original_replacement_off_pi_over_four_parameter_count": 40,
        "repaired_off_pi_over_four_parameter_count": 5,
        "original_incremental_off_pi_over_four_parameter_count": 39,
        "repaired_incremental_off_pi_over_four_parameter_count": 4,
        "original_incremental_proxy_t_pressure": 780,
        "repaired_incremental_proxy_t_pressure": 80,
        "off_grid_parameter_reduction_vs_original_candidate": 35,
        "proxy_t_pressure_reduction_vs_original_candidate": 700,
        "packets_with_remaining_off_grid_repair_count": 1,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
    }
    for field, expected_value in expected.items():
        if summary.get(field) != expected_value:
            errors.append(f"{field}_expected_{expected_value}_got_{summary.get(field)}")
    if [row.get("candidate_line_number") for row in rows] != [1378, 268, 1381]:
        errors.append("candidate_lines_must_be_[1378,268,1381]")
    expected_off_grid_by_line = {1378: 0, 268: 0, 1381: 5}
    for row in rows:
        line = row.get("candidate_line_number")
        if row.get("bounded_packet_exact_repair") is not True:
            errors.append(f"line_{line}_must_have_exact_packet_repair")
        if row.get("repaired_off_pi_over_four_parameter_count") != expected_off_grid_by_line.get(line):
            errors.append(f"line_{line}_repaired_off_grid_count_mismatch")
        if row.get("accepted_full_circuit_replay_certificate") is not False:
            errors.append(f"line_{line}_must_not_accept_full_circuit_replay")
        if row.get("accepted_occurrence_removal") != 0:
            errors.append(f"line_{line}_accepted_occurrence_must_be_zero")
    for field in [
        "bounded_packet_repair_claimed_as_full_circuit_rewrite",
        "symbolic_exact_decomposition_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field}_must_be_false")
        if payload.get("claim_boundary", {}).get(field) is not False:
            errors.append(f"claim_boundary_{field}_must_be_false")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone_01 Repaired Packet Resource Boundary Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes the 3/3 exact packet repairs from T-B1-004ai/aj/al and asks whether the repaired reduced-CNOT packet set can be accepted by the B7 ledger.",
        "",
        "## Summary",
        "",
        f"- Packets with bounded exact repairs: `{summary['bounded_packet_exact_repair_count']}` / `{summary['packet_count']}`",
        f"- Candidate CNOT reduction if accepted: `{summary['candidate_cnot_reduction_if_all_packets_accepted']}`",
        f"- Source off-grid parameters: `{summary['source_off_pi_over_four_parameter_count']}`",
        f"- Original replacement off-grid parameters: `{summary['original_replacement_off_pi_over_four_parameter_count']}`",
        f"- Repaired off-grid parameters: `{summary['repaired_off_pi_over_four_parameter_count']}`",
        f"- Off-grid parameter reduction vs original candidate: `{summary['off_grid_parameter_reduction_vs_original_candidate']}`",
        f"- Original incremental proxy-T pressure: `{summary['original_incremental_proxy_t_pressure']}`",
        f"- Repaired incremental proxy-T pressure: `{summary['repaired_incremental_proxy_t_pressure']}`",
        f"- Packets with remaining off-grid repair: `{summary['packets_with_remaining_off_grid_repair_count']}`",
        f"- Accepted full-circuit replay certificates: `{summary['accepted_full_circuit_replay_certificate_count']}`",
        f"- Accepted occurrence/proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Packet Rows",
        "",
        "| Candidate line | Repair gate | CNOT delta | Repaired off-grid params | Incremental proxy-T pressure | Exact residual | Accepted replay |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["repaired_packet_resource_boundary_rows"]:
        lines.append(
            f"| {row['candidate_line_number']} | {row['repair_gate_id']} | "
            f"{row['candidate_cnot_reduction']} | "
            f"{row['repaired_off_pi_over_four_parameter_count']} | "
            f"{row['repaired_incremental_proxy_t_pressure']} | "
            f"{row['exact_repair_residual_norm']:.6e} | "
            f"{row['accepted_full_circuit_replay_certificate']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "The repaired packet set is materially stronger than the original arbitrary-U3 candidate set: off-grid replacement pressure falls from 40 parameters to 5. However, the remaining five off-grid parameters on line 1381, plus the absence of symbolic full-circuit replay certificates, still block B7 ledger acceptance.",
            "",
            "## Next Required Gate",
            "",
            "The next route must either exact-decompose or absorb the five line-1381 off-grid local-U3 parameters and emit full-circuit replay certificates, or reject the reduced-CNOT route as a ledger-improving rewrite.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload()
    errors = validate_payload(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    if errors:
        payload["validation_errors"] = errors
    write_json(args.json_output, payload, pretty=args.pretty)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
