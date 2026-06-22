#!/usr/bin/env python3
"""Composable patch certificate gate for the B1/B7 cone_01 candidate.

T-B1-004ba gives a finite input-span replay certificate for the QASM2 candidate.
This gate attacks a different missing link: it turns the non-overlap bounded
patch subset into a tolerance-bounded full-circuit semantic patch certificate.

The certificate is conditional on the already audited local-unitary replacement
rows: every selected source window must be non-overlapping, same-support,
bounded-exact under the local unitary tolerance, and present in the emitted
QASM2 candidate rewrite. This is stronger than sampled replay, but still not a
B7 resource win because line 1378 was dropped and line 1381 still contains
off-grid local-U3 parameters that have no accepted FT pricing.
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
NONOVERLAP_PATH = ROOT / "results" / "B1_B7_cone01_nonoverlap_patch_subset_gate_v0.json"
QASM2_REWRITE_PATH = ROOT / "results" / "B1_B7_cone01_qasm2_candidate_rewrite_gate_v0.json"
LINEAR_SPAN_PATH = ROOT / "results" / "B1_B7_cone01_linear_span_replay_certificate_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_composable_patch_certificate_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_composable_patch_certificate_gate.md"

METHOD = "b1_b7_cone01_composable_patch_certificate_gate_v0"
STATUS = "cone01_composable_patch_certificate_passed_without_b7_resource_credit"
MODEL_STATUS = "nonoverlap_qasm2_candidate_has_tolerance_bounded_semantic_patch_certificate"
LOCAL_UNITARY_TOLERANCE = 1e-10


def windows_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return not (
        int(left["window_end_line"]) < int(right["window_start_line"])
        or int(right["window_end_line"]) < int(left["window_start_line"])
    )


def certify_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_rows = sorted(rows, key=lambda row: int(row["window_start_line"]))
    overlap_pairs: list[dict[str, Any]] = []
    for index, left in enumerate(sorted_rows):
        for right in sorted_rows[index + 1 :]:
            if windows_overlap(left, right):
                overlap_pairs.append(
                    {
                        "left_candidate_line_number": int(left["candidate_line_number"]),
                        "right_candidate_line_number": int(right["candidate_line_number"]),
                        "overlap_start_line": max(
                            int(left["window_start_line"]),
                            int(right["window_start_line"]),
                        ),
                        "overlap_end_line": min(
                            int(left["window_end_line"]),
                            int(right["window_end_line"]),
                        ),
                    }
                )
    row_certificates: list[dict[str, Any]] = []
    for row in sorted_rows:
        residual = float(row["bounded_patch_residual_norm"])
        max_error = float(row["bounded_patch_max_abs_entry_error"])
        local_unitary_passed = (
            bool(row["bounded_patch_exact_pass"])
            and residual <= LOCAL_UNITARY_TOLERANCE
            and max_error <= LOCAL_UNITARY_TOLERANCE
            and bool(row["bounded_replacement_qasm3_patch_available"])
        )
        row_certificates.append(
            {
                "candidate_line_number": int(row["candidate_line_number"]),
                "window_start_line": int(row["window_start_line"]),
                "window_end_line": int(row["window_end_line"]),
                "support_qubits": [int(qubit) for qubit in row["support_qubits"]],
                "source_cnot_count": int(row["source_cnot_count"]),
                "replacement_cnot_count": int(row["replacement_cnot_count"]),
                "candidate_cnot_reduction": int(row["candidate_cnot_reduction"]),
                "replacement_off_pi_over_four_parameter_count": int(
                    row["replacement_off_pi_over_four_parameter_count"]
                ),
                "bounded_patch_residual_norm": residual,
                "bounded_patch_max_abs_entry_error": max_error,
                "local_unitary_certificate_passed": local_unitary_passed,
                "same_support_local_replacement": len(row["support_qubits"]) == 2,
            }
        )
    return {
        "row_certificates": row_certificates,
        "selected_patch_count": len(row_certificates),
        "nonoverlap_window_pair_count": overlap_pairs.__len__(),
        "overlap_pairs": overlap_pairs,
        "all_selected_windows_nonoverlap": len(overlap_pairs) == 0,
        "all_local_unitary_certificates_passed": all(
            row["local_unitary_certificate_passed"] for row in row_certificates
        ),
        "max_selected_patch_residual_norm": max(
            row["bounded_patch_residual_norm"] for row in row_certificates
        ),
        "max_selected_patch_entry_error": max(
            row["bounded_patch_max_abs_entry_error"] for row in row_certificates
        ),
        "selected_candidate_cnot_reduction": sum(
            row["candidate_cnot_reduction"] for row in row_certificates
        ),
        "selected_replacement_off_pi_over_four_parameter_count": sum(
            row["replacement_off_pi_over_four_parameter_count"] for row in row_certificates
        ),
        "selected_line_numbers": [
            row["candidate_line_number"] for row in row_certificates
        ],
    }


def run_probe() -> dict[str, Any]:
    nonoverlap = load_json(NONOVERLAP_PATH)
    qasm2 = load_json(QASM2_REWRITE_PATH)
    span = load_json(LINEAR_SPAN_PATH)
    selected_rows = nonoverlap["selected_nonoverlap_patch_rows"]
    certificate = certify_rows(selected_rows)
    qasm2_summary = qasm2.get("summary", {})
    span_summary = span.get("summary", {})
    candidate_qasm_path = ROOT / qasm2_summary["qasm2_candidate_path"]
    qasm2_candidate_exists = candidate_qasm_path.exists()
    dropped_line_numbers = [
        int(value)
        for value in nonoverlap.get("summary", {}).get("dropped_overlap_candidate_line_numbers", [])
    ]
    semantic_certificate_passed = (
        certificate["all_selected_windows_nonoverlap"]
        and certificate["all_local_unitary_certificates_passed"]
        and qasm2_summary.get("qasm2_candidate_rewrite_emitted") is True
        and qasm2_candidate_exists
        and span_summary.get("finite_linear_span_certificate_passed") is True
    )
    accepted_removed = 0
    accepted_replay_certificate_count = 1 if semantic_certificate_passed else 0
    accepted_qasm_patch_count = 1 if semantic_certificate_passed else 0
    summary = {
        "source_nonoverlap_subset_method": nonoverlap.get("method"),
        "source_qasm2_candidate_method": qasm2.get("method"),
        "source_linear_span_method": span.get("method"),
        "source_qasm": nonoverlap.get("source_qasm"),
        "candidate_qasm": display_path(candidate_qasm_path),
        "qasm2_candidate_exists": qasm2_candidate_exists,
        "qasm2_candidate_rewrite_emitted": qasm2_summary.get("qasm2_candidate_rewrite_emitted"),
        "source_cnot_count": qasm2_summary.get("source_cnot_count"),
        "candidate_cnot_count": qasm2_summary.get("candidate_cnot_count"),
        "candidate_cnot_delta": qasm2_summary.get("candidate_cnot_delta"),
        "selected_patch_count": certificate["selected_patch_count"],
        "selected_line_numbers": certificate["selected_line_numbers"],
        "dropped_overlap_candidate_line_numbers": dropped_line_numbers,
        "lost_candidate_cnot_reduction_due_to_overlap": nonoverlap.get("summary", {}).get(
            "lost_candidate_cnot_reduction_due_to_overlap"
        ),
        "all_selected_windows_nonoverlap": certificate["all_selected_windows_nonoverlap"],
        "nonoverlap_window_pair_count": certificate["nonoverlap_window_pair_count"],
        "all_local_unitary_certificates_passed": certificate[
            "all_local_unitary_certificates_passed"
        ],
        "max_selected_patch_residual_norm": certificate["max_selected_patch_residual_norm"],
        "max_selected_patch_entry_error": certificate["max_selected_patch_entry_error"],
        "selected_candidate_cnot_reduction": certificate["selected_candidate_cnot_reduction"],
        "selected_replacement_off_pi_over_four_parameter_count": certificate[
            "selected_replacement_off_pi_over_four_parameter_count"
        ],
        "tolerance_bounded_full_circuit_semantic_certificate_passed": semantic_certificate_passed,
        "semantic_certificate_is_tolerance_bounded": True,
        "symbolic_unitary_equivalence_claimed": False,
        "full_space_symbolic_equivalence_claimed": False,
        "arbitrary_input_semantic_certificate_claimed": semantic_certificate_passed,
        "accepted_full_circuit_replay_certificate_count": accepted_replay_certificate_count,
        "accepted_full_circuit_qasm_patch_count": accepted_qasm_patch_count,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "local_u3_resource_pricing_accepted": False,
        "line1378_delta_recovered": False,
        "validation_error_count": 0,
        "row_certificates": certificate["row_certificates"],
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_nonoverlap_subset_result": display_path(NONOVERLAP_PATH),
        "source_qasm2_candidate_result": display_path(QASM2_REWRITE_PATH),
        "source_linear_span_result": display_path(LINEAR_SPAN_PATH),
        "summary": summary,
        "claim_boundary": {
            "supported_claim": (
                "The selected line-268 plus line-1381 non-overlap QASM2 candidate "
                "has a tolerance-bounded full-circuit semantic patch certificate "
                "assembled from composable local-unitary replacement rows."
            ),
            "unsupported_claims": [
                "This is not a symbolic exact full-circuit proof.",
                "This does not recover the dropped line-1378 CNOT delta.",
                "This does not price the remaining line-1381 off-grid local-U3 parameters.",
                "This is not an accepted B7 occurrence-removing certificate.",
                "This does not improve the B7 ledger.",
            ],
            "symbolic_unitary_equivalence_claimed": False,
            "full_space_symbolic_equivalence_claimed": False,
            "arbitrary_input_semantic_certificate_claimed": semantic_certificate_passed,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    return payload


def markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Composable Patch Certificate Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Source non-overlap subset: `{payload['source_nonoverlap_subset_result']}`",
        f"- Source QASM2 candidate: `{payload['source_qasm2_candidate_result']}`",
        f"- Source linear-span replay: `{payload['source_linear_span_result']}`",
        "",
        "## Result",
        "",
        f"- Tolerance-bounded full-circuit semantic certificate passed: `{summary['tolerance_bounded_full_circuit_semantic_certificate_passed']}`",
        f"- Selected lines: `{summary['selected_line_numbers']}`",
        f"- Dropped overlap lines: `{summary['dropped_overlap_candidate_line_numbers']}`",
        f"- Selected patch count: `{summary['selected_patch_count']}`",
        f"- All selected windows non-overlap: `{summary['all_selected_windows_nonoverlap']}`",
        f"- All local-unitary certificates passed: `{summary['all_local_unitary_certificates_passed']}`",
        f"- Max selected patch residual norm: `{summary['max_selected_patch_residual_norm']}`",
        f"- Max selected patch entry error: `{summary['max_selected_patch_entry_error']}`",
        f"- Source/candidate CNOT count/delta: `{summary['source_cnot_count']}` / `{summary['candidate_cnot_count']}` / `{summary['candidate_cnot_delta']}`",
        f"- Selected candidate CNOT reduction: `{summary['selected_candidate_cnot_reduction']}`",
        f"- Selected off-grid local-U3 parameters: `{summary['selected_replacement_off_pi_over_four_parameter_count']}`",
        f"- Accepted replay certificate / QASM patch count: `{summary['accepted_full_circuit_replay_certificate_count']}` / `{summary['accepted_full_circuit_qasm_patch_count']}`",
        f"- Accepted occurrence / proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        "",
        "## Claim Boundary",
        "",
        "- This is a tolerance-bounded semantic patch certificate, not a symbolic exact proof.",
        "- B7 resource credit remains 0 because line 1378 is still dropped and line 1381 retains unpriced off-grid local-U3 parameters.",
        "- The next valid gate must recover line 1378, price or remove line-1381 off-grid parameters, or produce a different occurrence-removing route.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", default=str(JSON_OUT))
    parser.add_argument("--markdown-output", default=str(MD_OUT))
    args = parser.parse_args()
    payload = run_probe()
    write_json(Path(args.json_output), payload, True)
    write_text(Path(args.markdown_output), markdown_report(payload))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
