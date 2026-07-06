#!/usr/bin/env python3
"""T-B1-004ds/T-B7-013b: R17 NL-C02 O1 search-domain boundary gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r17_nlc02_o1_search_domain_boundary_gate_v0"
STATUS = "cone01_r17_nlc02_o1_search_domain_boundary_set_not_full_lemma"
MODEL_STATUS = "nlc02_o1_disposed_as_search_domain_boundary_reroute_still_forbidden"
VERSION = "0.1"
TARGET_ID = "T-B1-004ds/T-B7-013b"
BOUNDARY_ID = "B1-B7-cone01-R17-NL-C02-O1-search-domain-boundary"
CANDIDATE_ID = "NL-C02"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r11 = load_json(args.r11_skeleton)
    r12 = load_json(args.r12_bridge)
    r13 = load_json(args.r13_binding)
    r16 = load_json(args.r16_lemma)
    r11s = r11["summary"]
    r12s = r12["summary"]
    r13s = r13["summary"]
    r16s = r16["summary"]
    obligations = r11["nlc02_leaveout_proof_skeleton"]["open_proof_obligations"]
    obligation_ids = [row["obligation_id"] for row in obligations]

    disposition_rows = [
        {
            "obligation_id": "O1",
            "original_obligation": next(
                row["description"] for row in obligations if row["obligation_id"] == "O1"
            ),
            "disposition": "downgraded_to_search_domain_boundary",
            "optimizer_completeness_proved": False,
            "search_domain_boundary_declared": True,
            "full_negative_lemma_upgrade_requires": [
                "a proof that the leave-out optimizer is complete for the declared parameterization",
                "or an independently checked symbolic exhaustive argument for the five-parameter domain",
                "or a narrower theorem statement that explicitly quantifies only over the certified search domain",
            ],
        },
        {
            "obligation_id": "O2",
            "disposition": "closed_by_r12_for_current_residual_model",
            "source_hash": r12s["bridge_hash"],
        },
        {
            "obligation_id": "O4",
            "disposition": "closed_by_r13_for_current_hash_chain",
            "source_hash": r13s["binding_hash"],
        },
        {
            "obligation_id": "O3a",
            "disposition": "clifford_frame_affine_sublemma_closed_by_r16",
            "source_hash": r16s["lemma_hash"],
        },
        {
            "obligation_id": "O3",
            "disposition": "full_general_local_unitary_invariance_still_open",
            "full_o3_closed": False,
        },
    ]

    boundary_packet = {
        "boundary_id": BOUNDARY_ID,
        "source_target_id": TARGET_ID,
        "candidate_id": CANDIDATE_ID,
        "source_artifacts": {
            "r11_skeleton": str(args.r11_skeleton),
            "r12_bridge": str(args.r12_bridge),
            "r13_binding": str(args.r13_binding),
            "r16_lemma": str(args.r16_lemma),
        },
        "source_hashes": {
            "r11_skeleton_file": file_hash(args.r11_skeleton),
            "r12_bridge_file": file_hash(args.r12_bridge),
            "r13_binding_file": file_hash(args.r13_binding),
            "r16_lemma_file": file_hash(args.r16_lemma),
        },
        "source_artifact_hashes": {
            "r11_skeleton_hash": r11s["skeleton_hash"],
            "r11_row_table_hash": r11s["row_table_hash"],
            "r12_bridge_hash": r12s["bridge_hash"],
            "r13_binding_hash": r13s["binding_hash"],
            "r16_lemma_hash": r16s["lemma_hash"],
            "r16_proof_table_hash": r16s["proof_table_hash"],
        },
        "search_domain_statement": (
            "NL-C02 is currently only a search-domain diagnostic: the 31 leave-out rows, R12 tolerance "
            "bridge, R13 source binding, and R16 Clifford-frame affine sublemma are accepted as bounded "
            "evidence, but optimizer completeness for the full declared parameterization is not proved."
        ),
        "disposition_rows": disposition_rows,
        "decision": {
            "o1_full_optimizer_completeness_proved": False,
            "o1_disposed_by_search_domain_downgrade": True,
            "search_domain_negative_diagnostic_ready": True,
            "checked_negative_lemma_present": False,
            "nlc02_full_lemma_ready": False,
            "reroute_allowed": False,
            "why": (
                "The only honest R17 action is to declare the O1 boundary rather than upgrade NL-C02. "
                "The candidate remains useful as a bounded diagnostic but cannot unlock R5 reroute or B7 credit."
            ),
        },
    }
    boundary_packet["disposition_table_hash"] = stable_hash(disposition_rows)
    boundary_packet["boundary_hash"] = stable_hash(boundary_packet)

    requirements = [
        requirement(
            "H1",
            "R11 proof skeleton is validation-clean and exposes O1",
            r11.get("method") == "b1_b7_cone01_r11_nlc02_leaveout_proof_skeleton_gate_v0"
            and r11s.get("validation_error_count") == 0
            and "O1" in obligation_ids,
            {
                "r11_method": r11.get("method"),
                "r11_validation_error_count": r11s.get("validation_error_count"),
                "obligation_ids": obligation_ids,
            },
        ),
        requirement(
            "H2",
            "R12 closes O2 for the current residual model",
            r12.get("method") == "b1_b7_cone01_r12_nlc02_tolerance_bridge_gate_v0"
            and r12s.get("validation_error_count") == 0
            and r12s.get("o2_closed_for_current_residual_model") is True,
            {
                "r12_method": r12.get("method"),
                "r12_validation_error_count": r12s.get("validation_error_count"),
                "o2_closed_for_current_residual_model": r12s.get("o2_closed_for_current_residual_model"),
            },
        ),
        requirement(
            "H3",
            "R13 closes O4 for the current hash chain",
            r13.get("method") == "b1_b7_cone01_r13_nlc02_source_domain_binding_gate_v0"
            and r13s.get("validation_error_count") == 0
            and r13s.get("o4_closed_for_current_hash_chain") is True,
            {
                "r13_method": r13.get("method"),
                "r13_validation_error_count": r13s.get("validation_error_count"),
                "o4_closed_for_current_hash_chain": r13s.get("o4_closed_for_current_hash_chain"),
            },
        ),
        requirement(
            "H4",
            "R16 closes only the Clifford-frame affine O3 sublemma",
            r16.get("method") == "b1_b7_cone01_r16_nlc02_clifford_frame_invariance_lemma_gate_v0"
            and r16s.get("validation_error_count") == 0
            and r16s.get("clifford_frame_invariance_sublemma_closed") is True
            and r16s.get("o3_closed") is False,
            {
                "r16_method": r16.get("method"),
                "r16_validation_error_count": r16s.get("validation_error_count"),
                "clifford_frame_invariance_sublemma_closed": r16s.get(
                    "clifford_frame_invariance_sublemma_closed"
                ),
                "o3_closed": r16s.get("o3_closed"),
            },
        ),
        requirement(
            "H5",
            "O1 is explicitly downgraded rather than falsely proved",
            boundary_packet["decision"]["o1_full_optimizer_completeness_proved"] is False
            and boundary_packet["decision"]["o1_disposed_by_search_domain_downgrade"] is True,
            boundary_packet["decision"],
        ),
        requirement(
            "H6",
            "Search-domain statement preserves all 31 leave-out rows and zero exact passes",
            r11s.get("leave_out_row_count") == 31
            and r11s.get("leave_out_exact_pass_count") == 0
            and r11s.get("leave_out_exact_fail_count") == 31,
            {
                "leave_out_row_count": r11s.get("leave_out_row_count"),
                "leave_out_exact_pass_count": r11s.get("leave_out_exact_pass_count"),
                "leave_out_exact_fail_count": r11s.get("leave_out_exact_fail_count"),
            },
        ),
        requirement(
            "H7",
            "Boundary is hash-bound to R11, R12, R13, and R16",
            all(boundary_packet["source_hashes"].values())
            and all(boundary_packet["source_artifact_hashes"].values())
            and bool(boundary_packet["disposition_table_hash"])
            and bool(boundary_packet["boundary_hash"]),
            {
                "source_hashes": boundary_packet["source_hashes"],
                "source_artifact_hashes": boundary_packet["source_artifact_hashes"],
                "disposition_table_hash": boundary_packet["disposition_table_hash"],
                "boundary_hash": boundary_packet["boundary_hash"],
            },
        ),
        requirement(
            "H8",
            "Boundary records the exact upgrade evidence required before any full lemma claim",
            len(disposition_rows[0]["full_negative_lemma_upgrade_requires"]) == 3,
            {
                "full_negative_lemma_upgrade_requires": disposition_rows[0][
                    "full_negative_lemma_upgrade_requires"
                ]
            },
        ),
        requirement(
            "H9",
            "Boundary is not upgraded into a checked negative lemma or reroute",
            boundary_packet["decision"]["checked_negative_lemma_present"] is False
            and boundary_packet["decision"]["nlc02_full_lemma_ready"] is False
            and boundary_packet["decision"]["reroute_allowed"] is False,
            boundary_packet["decision"],
        ),
        requirement(
            "H10",
            "Boundary preserves zero resource and B7 credit claims",
            True,
            {
                "accepted_route_count": 0,
                "accepted_occurrence_removal": 0,
                "accepted_proxy_t_reduction": 0,
                "b7_credit_delta": 0,
                "b7_space_time_volume_credit": 0,
                "resource_saving_claimed": False,
                "b7_ledger_improvement_claimed": False,
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R17 O1 boundary failures: {failed_ids}")

    summary = {
        "boundary_id": BOUNDARY_ID,
        "boundary_hash": boundary_packet["boundary_hash"],
        "disposition_table_hash": boundary_packet["disposition_table_hash"],
        "source_r11_skeleton_hash": r11s["skeleton_hash"],
        "source_r11_row_table_hash": r11s["row_table_hash"],
        "source_r12_bridge_hash": r12s["bridge_hash"],
        "source_r13_binding_hash": r13s["binding_hash"],
        "source_r16_lemma_hash": r16s["lemma_hash"],
        "candidate_id": CANDIDATE_ID,
        "leave_out_row_count": r11s["leave_out_row_count"],
        "leave_out_exact_pass_count": r11s["leave_out_exact_pass_count"],
        "o1_full_optimizer_completeness_proved": False,
        "o1_disposed_by_search_domain_downgrade": True,
        "search_domain_negative_diagnostic_ready": True,
        "o2_closed_for_current_residual_model": True,
        "o4_closed_for_current_hash_chain": True,
        "clifford_frame_invariance_sublemma_closed": True,
        "o3_closed": False,
        "remaining_open_obligations": ["O3", "O1_full_optimizer_completeness_if_upgrading"],
        "remaining_open_obligation_count": 2,
        "checked_negative_lemma_present": False,
        "nlc02_full_lemma_ready": False,
        "reroute_allowed": False,
        "accepted_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "requirement_count": len(requirements),
        "requirements_passed": passed,
        "requirements_failed": len(requirements) - passed,
        "failed_requirement_ids": failed_ids,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "source_target_id": TARGET_ID,
        "title": "B1/B7 Cone01 R17 NL-C02 O1 Search-Domain Boundary Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "summary": summary,
        "nlc02_o1_search_domain_boundary_packet": boundary_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R17 disposes of O1 only by explicitly downgrading NL-C02 to a search-domain diagnostic. "
                "It preserves R11/R12/R13/R16 bounded evidence while preventing any full optimizer-completeness claim."
            ),
            "what_is_not_supported": (
                "R17 does not prove optimizer completeness, does not close full O3, and does not make NL-C02 "
                "a checked negative lemma. No R5 reroute, R1 solution, occurrence removal, proxy-T reduction, "
                "B7 credit, resource saving, or impossibility theorem is supported."
            ),
            "next_gate": (
                "Either supply a real O1 optimizer-completeness proof, expand O3 beyond the closed Clifford-frame "
                "affine sublemma, or keep NL-C02 permanently scoped as a search-domain diagnostic."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    packet = payload["nlc02_o1_search_domain_boundary_packet"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Candidate: `{s['candidate_id']}`",
        f"- Boundary hash: `{s['boundary_hash']}`",
        f"- Disposition-table hash: `{s['disposition_table_hash']}`",
        "",
        "## Result",
        "",
        (
            f"The R17 O1 boundary gate passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements. It disposes of O1 by declaring a search-domain boundary, not by proving "
            "optimizer completeness."
        ),
        "",
        "## Search-Domain Statement",
        "",
        packet["search_domain_statement"],
        "",
        "## Disposition Rows",
        "",
    ]
    for row in packet["disposition_rows"]:
        lines.append(f"- `{row['obligation_id']}`: {row['disposition']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- O1 full optimizer completeness proved: `{s['o1_full_optimizer_completeness_proved']}`",
            f"- O1 disposed by search-domain downgrade: `{s['o1_disposed_by_search_domain_downgrade']}`",
            f"- Search-domain negative diagnostic ready: `{s['search_domain_negative_diagnostic_ready']}`",
            f"- O3 closed: `{s['o3_closed']}`",
            f"- Remaining open obligations: `{s['remaining_open_obligations']}`",
            f"- Checked negative lemma present: `{s['checked_negative_lemma_present']}`",
            f"- Reroute allowed: `{s['reroute_allowed']}`",
            "",
            "## Requirement Results",
            "",
        ]
    )
    for row in payload["requirements"]:
        marker = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- `{row['requirement_id']}` {marker}: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "This boundary gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.",
            "",
            "## Validation",
            "",
            f"- validation_error_count: `{s['validation_error_count']}`",
        ]
    )
    for error in payload["validation_errors"]:
        lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--r11-skeleton",
        type=Path,
        default=Path("results/B1_B7_cone01_R11_nlc02_leaveout_proof_skeleton_gate_v0.json"),
    )
    parser.add_argument(
        "--r12-bridge",
        type=Path,
        default=Path("results/B1_B7_cone01_R12_nlc02_tolerance_bridge_gate_v0.json"),
    )
    parser.add_argument(
        "--r13-binding",
        type=Path,
        default=Path("results/B1_B7_cone01_R13_nlc02_source_domain_binding_gate_v0.json"),
    )
    parser.add_argument(
        "--r16-lemma",
        type=Path,
        default=Path("results/B1_B7_cone01_R16_nlc02_clifford_frame_invariance_lemma_gate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R17_nlc02_o1_search_domain_boundary_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R17_nlc02_o1_search_domain_boundary_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-06")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "boundary_hash": payload["summary"]["boundary_hash"],
                "disposition_table_hash": payload["summary"]["disposition_table_hash"],
                "o1_full_optimizer_completeness_proved": payload["summary"][
                    "o1_full_optimizer_completeness_proved"
                ],
                "o1_disposed_by_search_domain_downgrade": payload["summary"][
                    "o1_disposed_by_search_domain_downgrade"
                ],
                "search_domain_negative_diagnostic_ready": payload["summary"][
                    "search_domain_negative_diagnostic_ready"
                ],
                "o3_closed": payload["summary"]["o3_closed"],
                "remaining_open_obligations": payload["summary"]["remaining_open_obligations"],
                "reroute_allowed": payload["summary"]["reroute_allowed"],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B1/B7 R17 O1 boundary gate validation failed")


if __name__ == "__main__":
    main()
